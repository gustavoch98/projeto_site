"""Popula o banco com os jogadores do topo do ranking BR (Desafiante, Grão-Mestre e Mestre).

Objetivo: dar uma base inicial para o autocomplete. Para cada jogador são 2 requisições
(nome no Account-V1 e ícone/nível no Summoner-V4); o elo vem da própria liga.

Pode ser interrompido (Ctrl+C) e rodado de novo: jogadores que já estão no banco são pulados.

Uso (na pasta backend, com o .venv ativado):
    python scripts/semear_ranking.py                 # todos (~10 mil jogadores; ~3h30 a 5h com chave de dev)
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

from app.config import get_settings  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.models import Account  # noqa: E402
from app.riot.client import RiotClient  # noqa: E402
from app.riot.routing import REGIOES  # noqa: E402
from app.services.coleta import salvar_jogador_da_liga  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("semente")
logging.getLogger("httpx").setLevel(logging.WARNING)

REGIAO = "br"
LIGAS = ["challenger", "grandmaster", "master"]
# Abaixo do limite da chave (100/2min) para sobrar espaço para o site e o desenvolvimento.
# Ajustável com --por-2min (ex.: 90 quando nada mais estiver usando a chave).
POR_2MIN_PADRAO = 60
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


async def main(limite: int | None, por_2min: int) -> None:
    limites = [(18, 1.0), (por_2min, 120.0)]
    riot = RiotClient(get_settings().riot_api_key.get_secret_value(), limites=limites)
    rot = REGIOES[REGIAO]
    try:
        ranking = await carregar_ranking(riot)
        salvos = await puuids_ja_salvos()
        pendentes = [(t, e) for t, e in ranking if e["puuid"] not in salvos][:limite]
        log.info("Contas já no banco: %d | a buscar agora: %d", len(salvos), len(pendentes))

        fila: asyncio.Queue = asyncio.Queue()
        for item in pendentes:
            fila.put_nowait(item)
        contagem = {"ok": 0, "sumiu": 0, "conflito": 0, "falhou": 0}
        inicio = time.monotonic()

        async def trabalhador():
            while not fila.empty():
                tier, entrada = fila.get_nowait()
                resultado = await salvar_jogador_da_liga(riot, rot, REGIAO, tier, entrada)
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
    parser.add_argument(
        "--por-2min", type=int, default=POR_2MIN_PADRAO, help="requisições por host a cada 2 min"
    )
    args = parser.parse_args()
    asyncio.run(main(args.limite, args.por_2min))
