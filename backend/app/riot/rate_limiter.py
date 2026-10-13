"""Limitador de taxa por janela deslizante.

A Riot define limites como "no máximo N requisições a cada X segundos" e conta
separadamente para cada host (br1, americas...). A chave de desenvolvimento tem
duas janelas ao mesmo tempo: 20 req/1s e 100 req/120s.

Funcionamento: guardamos o horário de cada requisição recente. Antes de uma nova,
descartamos as que já saíram da janela; se a janela estiver cheia, esperamos até
a mais antiga sair.
"""

import asyncio
import time
from collections import deque

# (máximo de requisições, tamanho da janela em segundos)
LIMITES_CHAVE_DESENVOLVIMENTO = [(20, 1.0), (100, 120.0)]


class JanelaDeslizante:
    def __init__(self, maximo: int, segundos: float, relogio=time.monotonic):
        self.maximo = maximo
        self.segundos = segundos
        self.relogio = relogio
        self.horarios: deque[float] = deque()

    def tempo_de_espera(self) -> float:
        """Quantos segundos faltam para caber mais uma requisição (0 = pode agora)."""
        agora = self.relogio()
        while self.horarios and agora - self.horarios[0] >= self.segundos:
            self.horarios.popleft()
        if len(self.horarios) < self.maximo:
            return 0.0
        return self.segundos - (agora - self.horarios[0])

    def registrar(self) -> None:
        self.horarios.append(self.relogio())


class RateLimiter:
    """Combina várias janelas: só libera quando TODAS têm espaço."""

    def __init__(self, limites=LIMITES_CHAVE_DESENVOLVIMENTO, relogio=time.monotonic):
        self.janelas = [JanelaDeslizante(maximo, segundos, relogio) for maximo, segundos in limites]
        # O lock garante que duas requisições simultâneas não "furem" a fila juntas.
        self.lock = asyncio.Lock()

    async def aguardar_vez(self) -> None:
        async with self.lock:
            while True:
                espera = max(janela.tempo_de_espera() for janela in self.janelas)
                if espera <= 0:
                    break
                await asyncio.sleep(espera)
            for janela in self.janelas:
                janela.registrar()


class RateLimiterPorHost:
    """Um RateLimiter independente para cada host da Riot."""

    def __init__(self, limites=LIMITES_CHAVE_DESENVOLVIMENTO):
        self.limites = limites
        self.por_host: dict[str, RateLimiter] = {}

    async def aguardar_vez(self, host: str) -> None:
        if host not in self.por_host:
            self.por_host[host] = RateLimiter(self.limites)
        await self.por_host[host].aguardar_vez()
