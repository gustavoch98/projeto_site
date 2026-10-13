"""Coleta históricos longos de partidas para o ambiente de exploração (notebook).

Dois modos (podem ser usados juntos; o jogador do --riot-id é processado primeiro):
  --riot-id "Nome#TAG" --partidas 300     histórico de um jogador específico
  --amostra 10 --partidas-amostra 100      N jogadores sorteados por elo (Ferro a Desafiante)

A amostra é sorteada com semente fixa e salva em dados/amostra_jogadores.json. Ao rodar de
novo, os mesmos jogadores são usados e as partidas já salvas são puladas (dá para interromper).

Uso (na pasta backend, com o .venv ativado):
    python scripts/coletar_partidas.py --riot-id "Hazze Gu#hazze" --partidas 300 --amostra 10
"""

import argparse
import asyncio
import json
import logging
import random
import sys
import time
from pathlib import Path

RAIZ_BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_BACKEND))  # permite "import app..."

from sqlalchemy import select  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.models import Match  # noqa: E402
from app.riot.client import RiotClient, RiotIndisponivel, RiotNaoEncontrado  # noqa: E402
from app.riot.routing import REGIOES  # noqa: E402
from app.services.coleta import com_paciencia, salvar_jogador_da_liga  # noqa: E402
from app.services.matches import salvar_partida  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("coleta")
logging.getLogger("httpx").setLevel(logging.WARNING)

REGIAO = "br"
ROT = REGIOES[REGIAO]
LIMITES = [(18, 1.0), (95, 120.0)]  # quase o limite da chave: a coleta é a prioridade agora
ARQUIVO_AMOSTRA = RAIZ_BACKEND / "dados" / "amostra_jogadores.json"
SEMENTE_SORTEIO = 42
MINIMO_PARTIDAS_TEMPORADA = 60
TIERS_COM_DIVISAO = ["IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD", "DIAMOND"]
LIGAS_APEX = {"MASTER": "master", "GRANDMASTER": "grandmaster", "CHALLENGER": "challenger"}
DOWNLOADS_SIMULTANEOS = 4


# --- Escolha dos jogadores -------------------------------------------------------


def ativo(entrada: dict) -> bool:
    return not entrada["inactive"] and entrada["wins"] + entrada["losses"] >= MINIMO_PARTIDAS_TEMPORADA


async def sortear_amostra(riot: RiotClient, por_elo: int) -> list[dict]:
    """Sorteia `por_elo` jogadores ativos de cada elo. Lê do arquivo se já foi sorteada."""
    if ARQUIVO_AMOSTRA.exists():
        amostra = json.loads(ARQUIVO_AMOSTRA.read_text(encoding="utf-8"))
        log.info("Amostra carregada de %s (%d jogadores)", ARQUIVO_AMOSTRA.name, len(amostra))
        return amostra

    sorteio = random.Random(SEMENTE_SORTEIO)
    amostra = []
    for tier in TIERS_COM_DIVISAO:
        candidatos = []
        for divisao in ["I", "II", "III", "IV"]:
            entradas = await com_paciencia(lambda: riot.entradas_liga(ROT, tier, divisao))
            candidatos += [{**e, "tier": tier} for e in entradas if ativo(e)]
        amostra += sorteio.sample(candidatos, min(por_elo, len(candidatos)))
        log.info("%s: %d candidatos ativos, %d sorteados", tier, len(candidatos), min(por_elo, len(candidatos)))

    for tier, liga in LIGAS_APEX.items():
        dados = await com_paciencia(lambda: riot.liga_apex(ROT, liga))
        candidatos = [{**e, "tier": tier} for e in dados["entries"] if ativo(e)]
        amostra += sorteio.sample(candidatos, min(por_elo, len(candidatos)))
        log.info("%s: %d candidatos ativos, %d sorteados", tier, len(candidatos), min(por_elo, len(candidatos)))

    ARQUIVO_AMOSTRA.parent.mkdir(exist_ok=True)
    ARQUIVO_AMOSTRA.write_text(json.dumps(amostra, indent=1), encoding="utf-8")
    return amostra


def intercalar_por_elo(amostra: list[dict]) -> list[dict]:
    """Ordena como Ferro, Bronze, ..., Desafiante, Ferro, Bronze...: assim, se a coleta for
    interrompida, os dados já estão equilibrados entre os elos."""
    grupos: dict[str, list[dict]] = {}
    for jogador in amostra:
        grupos.setdefault(jogador["tier"], []).append(jogador)
    intercalada = []
    while any(grupos.values()):
        for lista in grupos.values():
            if lista:
                intercalada.append(lista.pop(0))
    return intercalada


# --- Coleta das partidas ---------------------------------------------------------


async def ids_recentes(riot: RiotClient, puuid: str, quantidade: int) -> list[str]:
    """IDs das `quantidade` partidas ranqueadas mais recentes (paginando de 100 em 100)."""
    ids: list[str] = []
    while len(ids) < quantidade:
        pagina = min(100, quantidade - len(ids))
        lote = await com_paciencia(
            lambda: riot.ids_partidas(ROT, puuid, pagina, inicio=len(ids))
        )
        ids += lote
        if len(lote) < pagina:  # acabou o histórico
            break
    return ids


async def coletar_jogador(riot: RiotClient, puuid: str, quantidade: int) -> tuple[int, int]:
    """Salva as partidas que faltam de um jogador. Devolve (total encontrado, novas salvas)."""
    ids = await ids_recentes(riot, puuid, quantidade)
    async with SessionLocal() as session:
        existentes = set(await session.scalars(select(Match.match_id).where(Match.match_id.in_(ids))))
    faltando = [i for i in ids if i not in existentes]

    limite = asyncio.Semaphore(DOWNLOADS_SIMULTANEOS)
    novas = 0

    async def baixar(match_id: str):
        nonlocal novas
        async with limite:
            try:
                dados = await com_paciencia(lambda: riot.partida(ROT, match_id))
            except (RiotNaoEncontrado, RiotIndisponivel):
                log.warning("Pulando partida %s", match_id)
                return
            async with SessionLocal() as session:
                await salvar_partida(session, dados)
                await session.commit()
            novas += 1

    await asyncio.gather(*(baixar(i) for i in faltando))
    return len(ids), novas


async def main(riot_id: str | None, partidas: int, por_elo: int, partidas_amostra: int) -> None:
    riot = RiotClient(get_settings().riot_api_key.get_secret_value(), limites=LIMITES)
    inicio = time.monotonic()
    try:
        alvos: list[tuple[str, str, int]] = []  # (puuid, rótulo, quantidade)

        if riot_id:
            nome, tag = riot_id.split("#")
            conta = await com_paciencia(lambda: riot.conta_por_riot_id(ROT, nome, tag))
            alvos.append((conta["puuid"], riot_id, partidas))

        if por_elo:
            amostra = intercalar_por_elo(await sortear_amostra(riot, por_elo))
            for jogador in amostra:
                # Registra a conta (nome, ícone, elo) para o notebook saber o elo de cada um
                await salvar_jogador_da_liga(riot, ROT, REGIAO, jogador["tier"], jogador)
                alvos.append((jogador["puuid"], jogador["tier"], partidas_amostra))

        total_novas = 0
        for n, (puuid, rotulo, quantidade) in enumerate(alvos, start=1):
            encontradas, novas = await coletar_jogador(riot, puuid, quantidade)
            total_novas += novas
            minutos = (time.monotonic() - inicio) / 60
            log.info(
                "Jogador %d/%d (%s): %d partidas, %d novas | %d novas no total em %.0f min",
                n, len(alvos), rotulo, encontradas, novas, total_novas, minutos,
            )
        log.info("Concluído: %d partidas novas", total_novas)
    finally:
        await riot.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--riot-id", help='jogador específico, ex.: "Hazze Gu#hazze"')
    parser.add_argument("--partidas", type=int, default=300, help="partidas do --riot-id")
    parser.add_argument("--amostra", type=int, default=0, help="jogadores sorteados por elo")
    parser.add_argument("--partidas-amostra", type=int, default=100, help="partidas por jogador da amostra")
    args = parser.parse_args()
    asyncio.run(main(args.riot_id, args.partidas, args.amostra, args.partidas_amostra))
