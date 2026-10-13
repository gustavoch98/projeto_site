"""Popula o banco com os jogadores do topo do ranking BR (Desafiante, Grão-Mestre e Mestre).

Objetivo: dar uma base inicial para o autocomplete. Para cada jogador são 2 requisições
(nome no Account-V1 e ícone/nível no Summoner-V4); o elo vem da própria liga.

Pode ser interrompido (Ctrl+C) e rodado de novo: jogadores que já estão no banco são pulados.

Uso (na pasta backend, com o .venv ativado):
    python scripts/semear_ranking.py                 # todos (~10 mil jogadores, ~3h30 com chave de dev)
    python scripts/semear_ranking.py --limite 100    # só os 100 primeiros
"""

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # permite "import app..."

from sqlalchemy import select  # noqa: E402
from sqlalchemy.exc import IntegrityError  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.models import Account  # noqa: E402
from app.riot.client import RiotClient, RiotLimiteExcedido, RiotNaoEncontrado  # noqa: E402
from app.riot.routing import REGIOES  # noqa: E402
from app.services.players import FILA_SOLO, salvar_dados_riot  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("semente")
logging.getLogger("httpx").setLevel(logging.WARNING)

REGIAO = "br"
LIGAS = ["challenger", "grandmaster", "master"]
# Um pouco abaixo do limite da chave (100/2min) para sobrar espaço para o site rodando junto
LIMITES = [(18, 1.0), (90, 120.0)]
TRABALHADORES = 4  # jogadores processados em paralelo (o rate limiter segura o ritmo)


async def carregar_ranking(riot: RiotClient) -> list[tuple[str, dict]]:
    """Lista (tier, entrada) do maior para o menor PDL, liga por liga."""
    rot = REGIOES[REGIAO]
    jogadores = []
    for liga in LIGAS:
        dados = await riot.liga_apex(rot, liga)
        entradas = sorted(dados["entries"], key=lambda e: e["leaguePoints"], reverse=True)
        log.info("%s: %d jogadores", dados["tier"], len(entradas))
        jogadores += [(dados["tier"], e) for e in entradas]
    return jogadores


async def puuids_ja_salvos() -> set[str]:
    async with SessionLocal() as session:
        return set(await session.scalars(select(Account.puuid)))


async def semear_jogador(riot: RiotClient, tier: str, entrada: dict) -> str:
    """Busca nome e ícone de um jogador e salva. Devolve 'ok', 'sumiu' ou 'conflito'."""
    rot = REGIOES[REGIAO]
    puuid = entrada["puuid"]
    while True:
        try:
            conta, summoner = await asyncio.gather(
                riot.conta_por_puuid(rot, puuid),
                riot.summoner_por_puuid(rot, puuid),
            )
            break
        except RiotLimiteExcedido as erro:
            log.warning("429: esperando %ss", erro.retry_after)
            await asyncio.sleep(erro.retry_after)
        except RiotNaoEncontrado:
            return "sumiu"

    ranked = [{**entrada, "queueType": FILA_SOLO, "tier": tier}]
    async with SessionLocal() as session:
        try:
            await salvar_dados_riot(session, REGIAO, conta, summoner, ranked)
            await session.commit()
            return "ok"
        except IntegrityError:
            # Outro registro antigo do banco usa o mesmo Riot ID (alguém trocou de nome)
            await session.rollback()
            return "conflito"


async def main(limite: int | None) -> None:
    riot = RiotClient(get_settings().riot_api_key.get_secret_value(), limites=LIMITES)
    try:
        ranking = await carregar_ranking(riot)
        salvos = await puuids_ja_salvos()
        pendentes = [(t, e) for t, e in ranking if e["puuid"] not in salvos][:limite]
        log.info("Contas já no banco: %d | a buscar agora: %d", len(salvos), len(pendentes))

        fila: asyncio.Queue = asyncio.Queue()
        for item in pendentes:
            fila.put_nowait(item)
        contagem = {"ok": 0, "sumiu": 0, "conflito": 0}
        inicio = time.monotonic()

        async def trabalhador():
            while not fila.empty():
                tier, entrada = fila.get_nowait()
                resultado = await semear_jogador(riot, tier, entrada)
                contagem[resultado] += 1
                feitos = sum(contagem.values())
                if feitos % 50 == 0 or feitos == len(pendentes):
                    ritmo = feitos / (time.monotonic() - inicio) * 60
                    restante = (len(pendentes) - feitos) / ritmo if ritmo else 0
                    log.info(
                        "%d/%d (%s) | %.0f jogadores/min | faltam ~%.0f min",
                        feitos, len(pendentes), contagem, ritmo, restante,
                    )

        await asyncio.gather(*(trabalhador() for _ in range(TRABALHADORES)))
        log.info("Concluído: %s", contagem)
    finally:
        await riot.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--limite", type=int, default=None, help="máximo de jogadores a buscar")
    asyncio.run(main(parser.parse_args().limite))
