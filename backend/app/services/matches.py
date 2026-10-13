"""Ingestão e consulta de partidas (Match-V5)."""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db import SessionLocal
from app.models import Account, Match, MatchParticipant
from app.riot.client import RiotClient, RiotError, RiotNaoEncontrado
from app.riot.routing import Roteamento
from app.schemas.match import MatchSummary

logger = logging.getLogger(__name__)

PARTIDAS_POR_SINCRONIZACAO = 20
# Partidas mais curtas que isso foram encerradas no início (remake) e não contam nas análises
DURACAO_MINIMA_SEGUNDOS = 300


def _data(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000, tz=UTC)


def extrair_partida(dados: dict) -> tuple[dict, list[dict]]:
    """Converte o JSON da Riot em uma linha de `matches` e dez linhas de `match_participants`."""
    info = dados["info"]
    inicio = _data(info["gameStartTimestamp"])
    remake = info["gameDuration"] < DURACAO_MINIMA_SEGUNDOS or any(
        p.get("gameEndedInEarlySurrender") for p in info["participants"]
    )
    partida = {
        "match_id": dados["metadata"]["matchId"],
        "platform": info["platformId"],
        "queue_id": info["queueId"],
        "game_version": info["gameVersion"],
        "game_start": inicio,
        "game_duration": info["gameDuration"],
        "remake": remake,
        "raw": dados,
        "ingested_at": datetime.now(UTC),
    }
    participantes = [
        {
            "match_id": partida["match_id"],
            "puuid": p["puuid"],
            "queue_id": info["queueId"],
            "game_start": inicio,
            "game_duration": info["gameDuration"],
            "remake": remake,
            "riot_id_game_name": p.get("riotIdGameName", ""),
            "riot_id_tagline": p.get("riotIdTagline", ""),
            "team_id": p["teamId"],
            "team_position": p.get("teamPosition", ""),
            "champion_id": p["championId"],
            "champion_name": p["championName"],
            "win": p["win"],
            "kills": p["kills"],
            "deaths": p["deaths"],
            "assists": p["assists"],
            "cs": p["totalMinionsKilled"] + p["neutralMinionsKilled"],
            "gold": p["goldEarned"],
            "damage_to_champions": p["totalDamageDealtToChampions"],
            "vision_score": p["visionScore"],
            "kill_participation": p.get("challenges", {}).get("killParticipation"),
            "items": [p[f"item{i}"] for i in range(7)],
            "summoner_spells": [p["summoner1Id"], p["summoner2Id"]],
        }
        for p in info["participants"]
    ]
    return partida, participantes


async def salvar_partida(session: AsyncSession, dados: dict) -> None:
    partida, participantes = extrair_partida(dados)
    # ON CONFLICT DO NOTHING: se duas requisições salvarem a mesma partida ao mesmo tempo,
    # a segunda simplesmente não faz nada (em vez de dar erro de chave duplicada).
    await session.execute(insert(Match).values(partida).on_conflict_do_nothing())
    # A Riot às vezes devolve partidas sem participantes (canceladas ou com dados corrompidos).
    # Guardamos a partida para não buscá-la de novo, mas não há jogadores para inserir.
    if participantes:
        await session.execute(
            insert(MatchParticipant).values(participantes).on_conflict_do_nothing()
        )


def precisa_sincronizar(conta: Account, settings: Settings) -> bool:
    """Busca partidas novas se nunca buscou, se o perfil foi atualizado depois da última busca
    (ex.: botão "Atualizar") ou se a última busca é mais antiga que o TTL do cache."""
    if conta.matches_synced_at is None or conta.matches_synced_at < conta.updated_at:
        return True
    return datetime.now(UTC) - conta.matches_synced_at > timedelta(
        minutes=settings.cache_ttl_minutes
    )


async def sincronizar_partidas(
    session: AsyncSession, riot: RiotClient, rot: Roteamento, conta: Account
) -> int:
    """Busca na Riot as partidas recentes que ainda não estão no banco. Devolve quantas salvou."""
    ids = await riot.ids_partidas(rot, conta.puuid, PARTIDAS_POR_SINCRONIZACAO)
    existentes = set(await session.scalars(select(Match.match_id).where(Match.match_id.in_(ids))))

    novas = 0
    for match_id in ids:
        if match_id in existentes:
            continue
        try:
            await salvar_partida(session, await riot.partida(rot, match_id))
            await session.commit()  # salva cada partida já, para não perder o progresso numa falha
            novas += 1
        except RiotNaoEncontrado:
            logger.warning("Partida %s não encontrada na Riot; ignorando", match_id)

    conta.matches_synced_at = datetime.now(UTC)
    await session.commit()
    return novas


async def listar_partidas(
    session: AsyncSession,
    riot: RiotClient,
    settings: Settings,
    rot: Roteamento,
    conta: Account,
    limite: int = PARTIDAS_POR_SINCRONIZACAO,
) -> list[MatchSummary]:
    """Partidas mais recentes do jogador, sincronizando com a Riot antes quando necessário."""
    if precisa_sincronizar(conta, settings):
        try:
            novas = await sincronizar_partidas(session, riot, rot, conta)
            logger.info("%d partidas novas de %s#%s", novas, conta.game_name, conta.tag_line)
        except RiotError as erro:
            # Mesma filosofia do perfil: se a Riot falhar, mostramos o que já temos
            await session.rollback()
            logger.warning("Falha ao sincronizar partidas (%s); usando o banco", erro)

    linhas = await session.scalars(
        select(MatchParticipant)
        .where(MatchParticipant.puuid == conta.puuid)
        .order_by(MatchParticipant.game_start.desc())
        .limit(limite)
    )
    return [MatchSummary.model_validate(linha, from_attributes=True) for linha in linhas]


# --- Histórico longo em segundo plano (para o painel de insights) -------------------

# PUUIDs com preenchimento em andamento neste processo (evita duas buscas iguais ao mesmo tempo)
_historico_em_andamento: set[str] = set()


def precisa_completar_historico(conta: Account, settings: Settings) -> bool:
    return settings.historico_partidas > 0 and conta.history_backfilled_at is None


def historico_em_andamento(puuid: str) -> bool:
    return puuid in _historico_em_andamento


async def completar_historico(riot: RiotClient, rot: Roteamento, puuid: str, alvo: int) -> None:
    """Busca até `alvo` partidas ranqueadas do jogador, pulando as que já estão no banco.

    Roda DEPOIS de a resposta ser enviada (BackgroundTasks do FastAPI), por isso abre a
    própria sessão do banco. Se a Riot falhar, para e tenta de novo numa próxima visita.
    """
    if puuid in _historico_em_andamento:
        return
    _historico_em_andamento.add(puuid)
    try:
        ids: list[str] = []
        while len(ids) < alvo:
            pagina = min(100, alvo - len(ids))
            lote = await riot.ids_partidas(rot, puuid, pagina, inicio=len(ids))
            ids += lote
            if len(lote) < pagina:  # o jogador não tem mais partidas ranqueadas
                break

        async with SessionLocal() as session:
            existentes = set(
                await session.scalars(select(Match.match_id).where(Match.match_id.in_(ids)))
            )
            for match_id in ids:
                if match_id in existentes:
                    continue
                try:
                    await salvar_partida(session, await riot.partida(rot, match_id))
                    await session.commit()
                except RiotNaoEncontrado:
                    continue

            conta = await session.get(Account, puuid)
            if conta is not None:
                conta.history_backfilled_at = datetime.now(UTC)
                await session.commit()
        logger.info("Histórico completo: %d partidas de %s", len(ids), puuid[:12])
    except RiotError as erro:
        logger.warning("Preenchimento do histórico interrompido (%s); tenta de novo depois", erro)
    finally:
        _historico_em_andamento.discard(puuid)

