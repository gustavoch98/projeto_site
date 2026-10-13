import pytest

from app.riot.rate_limiter import JanelaDeslizante, RateLimiter


class RelogioFalso:
    """Relógio controlado pelo teste, para não precisar esperar de verdade."""

    def __init__(self):
        self.agora = 0.0

    def __call__(self) -> float:
        return self.agora


def test_janela_libera_ate_o_maximo_e_depois_pede_espera():
    relogio = RelogioFalso()
    janela = JanelaDeslizante(maximo=3, segundos=10, relogio=relogio)

    for _ in range(3):
        assert janela.tempo_de_espera() == 0
        janela.registrar()

    relogio.agora = 4
    assert janela.tempo_de_espera() == pytest.approx(6)  # a 1ª sai da janela em t=10

    relogio.agora = 10
    assert janela.tempo_de_espera() == 0


async def test_rate_limiter_espera_quando_a_janela_enche(monkeypatch):
    relogio = RelogioFalso()
    esperas = []

    async def sleep_falso(segundos):
        esperas.append(segundos)
        relogio.agora += segundos

    monkeypatch.setattr("app.riot.rate_limiter.asyncio.sleep", sleep_falso)
    limiter = RateLimiter(limites=[(2, 1.0), (3, 120.0)], relogio=relogio)

    for _ in range(3):
        await limiter.aguardar_vez()

    assert esperas == [pytest.approx(1.0)]  # 3ª requisição esperou a janela de 1s

    await limiter.aguardar_vez()  # 4ª estoura a janela de 120s
    assert sum(esperas) == pytest.approx(120.0)
