"""Cliente assíncrono da API da Riot (Account-V1, Summoner-V4, League-V4)."""

import asyncio
import logging
from urllib.parse import quote

import httpx

from app.riot.rate_limiter import RateLimiterPorHost
from app.riot.routing import Roteamento, host

logger = logging.getLogger(__name__)

# Tentativas extras para erros temporários (429 e 5xx)
MAX_TENTATIVAS = 3
# Se a Riot pedir para esperar mais que isso, desistimos e avisamos o usuário
ESPERA_MAXIMA_SEGUNDOS = 10


class RiotError(Exception):
    """Erro genérico ao falar com a Riot."""


class RiotNaoEncontrado(RiotError):
    """404: o recurso (ex.: jogador) não existe."""


class RiotChaveInvalida(RiotError):
    """401/403: chave ausente, inválida ou expirada."""


class RiotLimiteExcedido(RiotError):
    """429: limite de requisições excedido."""

    def __init__(self, retry_after: int):
        super().__init__(f"Limite excedido; tente em {retry_after}s")
        self.retry_after = retry_after


class RiotIndisponivel(RiotError):
    """5xx ou falha de rede: problema do lado da Riot."""


class RiotClient:
    def __init__(self, api_key: str, http: httpx.AsyncClient | None = None):
        self.http = http or httpx.AsyncClient(timeout=10)
        self.api_key = api_key
        self.rate_limiter = RateLimiterPorHost()

    async def close(self) -> None:
        await self.http.aclose()

    async def _get(self, nome_host: str, caminho: str):
        url = host(nome_host) + caminho
        for tentativa in range(1, MAX_TENTATIVAS + 1):
            await self.rate_limiter.aguardar_vez(nome_host)
            try:
                resposta = await self.http.get(url, headers={"X-Riot-Token": self.api_key})
            except httpx.TransportError as erro:
                raise RiotIndisponivel(f"Falha de rede: {erro}") from erro

            status = resposta.status_code
            if status == 200:
                return resposta.json()
            if status == 404:
                raise RiotNaoEncontrado(caminho)
            if status in (401, 403):
                raise RiotChaveInvalida(f"HTTP {status}")

            if status == 429:
                retry_after = int(resposta.headers.get("Retry-After", "1"))
                if retry_after > ESPERA_MAXIMA_SEGUNDOS or tentativa == MAX_TENTATIVAS:
                    raise RiotLimiteExcedido(retry_after)
                logger.warning("429 da Riot; esperando %ss (tentativa %s)", retry_after, tentativa)
                await asyncio.sleep(retry_after)
                continue

            if status >= 500 and tentativa < MAX_TENTATIVAS:
                logger.warning("HTTP %s da Riot; tentando de novo (tentativa %s)", status, tentativa)
                await asyncio.sleep(tentativa)  # espera 1s, depois 2s
                continue

            raise RiotIndisponivel(f"HTTP {status}")
        raise RiotIndisponivel("Tentativas esgotadas")

    # --- Endpoints ---------------------------------------------------------

    async def conta_por_riot_id(self, rot: Roteamento, game_name: str, tag_line: str) -> dict:
        """Account-V1 (host regional) -> {puuid, gameName, tagLine}"""
        caminho = (
            "/riot/account/v1/accounts/by-riot-id/"
            f"{quote(game_name, safe='')}/{quote(tag_line, safe='')}"
        )
        return await self._get(rot.regional, caminho)

    async def summoner_por_puuid(self, rot: Roteamento, puuid: str) -> dict:
        """Summoner-V4 (host de plataforma) -> {puuid, profileIconId, revisionDate, summonerLevel}"""
        return await self._get(rot.plataforma, f"/lol/summoner/v4/summoners/by-puuid/{puuid}")

    async def ranked_por_puuid(self, rot: Roteamento, puuid: str) -> list[dict]:
        """League-V4 (host de plataforma) -> lista com uma entrada por fila ranqueada"""
        return await self._get(rot.plataforma, f"/lol/league/v4/entries/by-puuid/{puuid}")
