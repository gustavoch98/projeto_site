"""Funções de coleta em lote usadas pelos scripts (semente do ranking e coleta de partidas).

Diferente das rotas da API, aqui o objetivo é volume: os erros temporários da Riot são
tratados com espera e nova tentativa, para que um processo de horas não pare por uma falha.
"""

import asyncio
import logging

from sqlalchemy.exc import IntegrityError

from app.db import SessionLocal
from app.riot.client import RiotClient, RiotIndisponivel, RiotLimiteExcedido, RiotNaoEncontrado
from app.riot.routing import Roteamento
from app.services.players import FILA_SOLO, salvar_dados_riot

log = logging.getLogger("coleta")

TENTATIVAS_FALHA_REDE = 3


async def com_paciencia(chamada):
    """Executa `chamada()` esperando nos 429 e tentando de novo em falhas de rede/5xx.

    Repassa RiotNaoEncontrado (404) e, se as falhas persistirem, RiotIndisponivel.
    """
    falhas = 0
    while True:
        try:
            return await chamada()
        except RiotLimiteExcedido as erro:
            log.warning("429: esperando %ss", erro.retry_after)
            await asyncio.sleep(erro.retry_after)
        except RiotIndisponivel:
            falhas += 1
            if falhas >= TENTATIVAS_FALHA_REDE:
                raise
            await asyncio.sleep(5 * falhas)


async def salvar_jogador_da_liga(
    riot: RiotClient, rot: Roteamento, regiao: str, tier: str, entrada: dict
) -> str:
    """Salva um jogador listado numa liga (League-V4), buscando nome e ícone.

    O elo vem da própria entrada da liga. Devolve 'ok', 'sumiu', 'conflito' ou 'falhou'.
    """
    puuid = entrada["puuid"]
    try:
        conta, summoner = await com_paciencia(
            lambda: asyncio.gather(
                riot.conta_por_puuid(rot, puuid), riot.summoner_por_puuid(rot, puuid)
            )
        )
    except RiotNaoEncontrado:
        return "sumiu"
    except RiotIndisponivel:
        log.warning("Pulando %s: Riot indisponível", puuid[:12])
        return "falhou"

    ranked = [{**entrada, "queueType": FILA_SOLO, "tier": tier}]
    async with SessionLocal() as session:
        try:
            await salvar_dados_riot(session, regiao, conta, summoner, ranked)
            await session.commit()
            return "ok"
        except IntegrityError:
            # Outro registro antigo do banco usa o mesmo Riot ID (alguém trocou de nome)
            await session.rollback()
            return "conflito"
