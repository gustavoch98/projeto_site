"""Regras de negócio do perfil de jogador, incluindo o cache no Postgres."""

import asyncio
import logging
import re
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models import Account, RankedEntry, RankedHistory
from app.riot.client import RiotChaveInvalida, RiotClient, RiotIndisponivel, RiotLimiteExcedido
from app.riot.routing import obter_roteamento
from app.schemas.player import PlayerProfile, PlayerSuggestion, RankedQueue

logger = logging.getLogger(__name__)

FILA_SOLO = "RANKED_SOLO_5x5"
FILA_FLEX = "RANKED_FLEX_SR"

# Autocomplete
TAMANHO_MINIMO_BUSCA = 2
LIMITE_SUGESTOES = 8

# Erros em que vale a pena devolver dados antigos do banco em vez de falhar
ERROS_TEMPORARIOS = (RiotIndisponivel, RiotLimiteExcedido, RiotChaveInvalida)


class RiotIdInvalido(ValueError):
    pass


def normalizar_riot_id(game_name: str, tag_line: str) -> tuple[str, str]:
    """Remove espaços nas pontas, junta espaços repetidos no nome e tira espaços da TAG."""
    nome = re.sub(r"\s+", " ", game_name).strip()
    tag = re.sub(r"\s+", "", tag_line).lstrip("#")
    if not 1 <= len(nome) <= 32 or not 1 <= len(tag) <= 10:
        raise RiotIdInvalido("Riot ID inválido. Use o formato Nome#TAG.")
    return nome, tag


async def buscar_perfil(
    session: AsyncSession,
    riot: RiotClient,
    settings: Settings,
    region: str,
    game_name: str,
    tag_line: str,
    forcar: bool = False,
) -> PlayerProfile:
    region = region.lower()
    rot = obter_roteamento(region)
    nome, tag = normalizar_riot_id(game_name, tag_line)

    conta = await session.scalar(
        select(Account).where(
            func.lower(Account.game_name) == nome.lower(),
            func.lower(Account.tag_line) == tag.lower(),
            Account.region == region,
        )
    )

    if conta is not None:
        idade = datetime.now(UTC) - conta.updated_at
        # Busca normal respeita o TTL do cache; "Atualizar" respeita só o intervalo mínimo
        validade = (
            timedelta(seconds=settings.refresh_cooldown_seconds)
            if forcar
            else timedelta(minutes=settings.cache_ttl_minutes)
        )
        if idade < validade:
            return montar_perfil(conta, settings, cached=True)

    try:
        dados_conta = await riot.conta_por_riot_id(rot, nome, tag)
        puuid = dados_conta["puuid"]
        summoner, ranked = await asyncio.gather(
            riot.summoner_por_puuid(rot, puuid),
            riot.ranked_por_puuid(rot, puuid),
        )
    except ERROS_TEMPORARIOS as erro:
        if conta is None:
            raise
        logger.warning("Riot indisponível (%s); devolvendo dados antigos do banco", erro)
        return montar_perfil(conta, settings, cached=True)

    # Se o Riot ID que estava no banco agora pertence a outro PUUID, o registro antigo
    # ficou desatualizado (o jogador antigo trocou de nome). Removemos para liberar o nome.
    if conta is not None and conta.puuid != puuid:
        await session.delete(conta)
        await session.flush()

    conta = await salvar_dados_riot(session, region, dados_conta, summoner, ranked)
    await session.commit()
    return montar_perfil(conta, settings, cached=False)


async def salvar_dados_riot(
    session: AsyncSession, region: str, dados_conta: dict, summoner: dict, ranked: list[dict]
) -> Account:
    agora = datetime.now(UTC)
    conta = await session.get(Account, dados_conta["puuid"])
    if conta is None:
        conta = Account(puuid=dados_conta["puuid"])
        session.add(conta)

    # O nome vem da Riot com as maiúsculas "oficiais", independente do que o usuário digitou
    conta.game_name = dados_conta["gameName"]
    conta.tag_line = dados_conta["tagLine"]
    conta.region = region
    conta.profile_icon_id = summoner["profileIconId"]
    conta.summoner_level = summoner["summonerLevel"]
    conta.updated_at = agora

    conta.ranked_entries = [
        RankedEntry(
            puuid=conta.puuid,
            queue_type=entrada["queueType"],
            tier=entrada["tier"],
            rank=entrada["rank"],
            league_points=entrada["leaguePoints"],
            wins=entrada["wins"],
            losses=entrada["losses"],
            updated_at=agora,
        )
        for entrada in ranked
    ]
    await registrar_historico(session, conta.puuid, conta.ranked_entries, agora)
    await session.flush()
    return conta


async def registrar_historico(
    session: AsyncSession, puuid: str, entradas: list[RankedEntry], agora: datetime
) -> None:
    """Grava uma "foto" de cada fila cujo elo mudou desde a última foto."""
    for entrada in entradas:
        ultima = await session.scalar(
            select(RankedHistory)
            .where(RankedHistory.puuid == puuid, RankedHistory.queue_type == entrada.queue_type)
            .order_by(RankedHistory.recorded_at.desc())
            .limit(1)
        )
        atual = (entrada.tier, entrada.rank, entrada.league_points, entrada.wins, entrada.losses)
        if ultima is not None and atual == (
            ultima.tier, ultima.rank, ultima.league_points, ultima.wins, ultima.losses
        ):
            continue
        session.add(
            RankedHistory(
                puuid=puuid,
                queue_type=entrada.queue_type,
                tier=entrada.tier,
                rank=entrada.rank,
                league_points=entrada.league_points,
                wins=entrada.wins,
                losses=entrada.losses,
                recorded_at=agora,
            )
        )


def filas_ranked(conta: Account) -> dict[str, RankedQueue]:
    """Entradas de ranked da conta indexadas pelo tipo de fila."""
    return {
        entrada.queue_type: RankedQueue(
            tier=entrada.tier,
            rank=entrada.rank,
            league_points=entrada.league_points,
            wins=entrada.wins,
            losses=entrada.losses,
        )
        for entrada in conta.ranked_entries
    }


def montar_perfil(conta: Account, settings: Settings, cached: bool) -> PlayerProfile:
    filas = filas_ranked(conta)
    return PlayerProfile(
        puuid=conta.puuid,
        game_name=conta.game_name,
        tag_line=conta.tag_line,
        region=conta.region,
        profile_icon_id=conta.profile_icon_id,
        summoner_level=conta.summoner_level,
        solo=filas.get(FILA_SOLO),
        flex=filas.get(FILA_FLEX),
        updated_at=conta.updated_at,
        refresh_available_at=conta.updated_at
        + timedelta(seconds=settings.refresh_cooldown_seconds),
        cached=cached,
    )


async def sugerir_jogadores(
    session: AsyncSession, region: str, texto: str
) -> list[PlayerSuggestion]:
    """Jogadores JÁ SALVOS no banco cujo nome começa com o texto digitado.

    A API da Riot não tem busca por prefixo, então só aparecem jogadores que o site já viu.
    Se o texto tiver '#', o que vem depois filtra a TAG por prefixo (ex.: "hazze gu#ha").
    """
    region = region.lower()
    obter_roteamento(region)  # valida a região
    nome, _, tag = texto.partition("#")
    nome = re.sub(r"\s+", " ", nome).strip().lower()
    tag = re.sub(r"\s+", "", tag).lower()
    if len(nome) < TAMANHO_MINIMO_BUSCA:
        return []

    consulta = select(Account).where(
        Account.region == region,
        # autoescape: um "%" ou "_" digitado pelo usuário é tratado como texto, não como curinga
        func.lower(Account.game_name).startswith(nome, autoescape=True),
    )
    if tag:
        consulta = consulta.where(func.lower(Account.tag_line).startswith(tag, autoescape=True))

    # Nomes mais curtos primeiro: quem digitou "hazz" provavelmente quer "Hazze", não "Hazzelnut123"
    consulta = consulta.order_by(func.length(Account.game_name), Account.game_name).limit(
        LIMITE_SUGESTOES
    )
    contas = (await session.scalars(consulta)).all()

    return [
        PlayerSuggestion(
            game_name=conta.game_name,
            tag_line=conta.tag_line,
            region=conta.region,
            profile_icon_id=conta.profile_icon_id,
            summoner_level=conta.summoner_level,
            solo=filas_ranked(conta).get(FILA_SOLO),
        )
        for conta in contas
    ]
