"""Testes da tier list (GET /api/champions/tierlist)."""

import random
from datetime import UTC, datetime, timedelta

import pytest

from app.services.tierlist import estimar_prior, tier_de, winrate_ajustado
from tests.test_api_matches import partida_falsa
from tests.test_insights import salvar

TIER_LIST = "/api/champions/tierlist"
INICIO = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
YASUO = (157, "Yasuo")
AHRI = (103, "Ahri")


def partida(i: int, vitoria_yasuo: bool, ahri_banida: bool, versao: str = "16.20.824.8524") -> dict:
    """Yasuo (meio, time azul) contra Ahri (meio, time vermelho); os outros 8 campeões mudam a
    cada partida para nunca atingirem o mínimo de jogos."""
    dados = partida_falsa(f"BR1_{i}", vitoria=vitoria_yasuo)
    info = dados["info"]
    info["gameVersion"] = versao
    info["gameStartTimestamp"] = int((INICIO + timedelta(hours=i)).timestamp() * 1000)
    for j, p in enumerate(info["participants"]):
        p["teamPosition"] = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"][j % 5]
        p["championId"], p["championName"] = 1000 + i * 10 + j, f"Outro{i}_{j}"
    info["participants"][2].update(championId=YASUO[0], championName=YASUO[1])  # azul, meio
    info["participants"][7].update(championId=AHRI[0], championName=AHRI[1])  # vermelho, meio
    bans = [{"championId": AHRI[0], "pickTurn": 1}] if ahri_banida else [{"championId": -1, "pickTurn": 1}]
    info["teams"] = [{"teamId": 100, "bans": bans}, {"teamId": 200, "bans": []}]
    return dados


def test_tier_de():
    assert [tier_de(w) for w in (0.56, 0.52, 0.505, 0.49, 0.40)] == ["S", "A", "B", "C", "D"]


def test_winrate_ajustado_puxa_amostras_pequenas_para_50():
    assert winrate_ajustado(12, 15, prior=100) == pytest.approx((12 + 50) / 115)  # 80% vira ~54%
    assert winrate_ajustado(800, 1000, prior=100) == pytest.approx(850 / 1100)  # quase não muda


def test_estimar_prior_sem_sinal_devolve_none():
    # Todos os campeões com o mesmo winrate real (50%): a variação é só ruído
    sorteio = random.Random(1)
    linhas = []
    for _ in range(150):
        n = 40
        linhas.append((sum(sorteio.random() < 0.5 for _ in range(n)), n))
    assert estimar_prior(linhas) is None


def test_estimar_prior_com_sinal_forte():
    # Metade dos campeões com 45% e metade com 55%, muitas partidas: diferença real clara
    linhas = [(450, 1000)] * 50 + [(550, 1000)] * 50
    prior = estimar_prior(linhas)
    assert prior is not None
    assert prior == pytest.approx(0.25 / (0.05**2 - 0.2475 / 1000), rel=0.01)


async def test_pick_ban_e_filtro_de_patch(api, riot_mock):
    # 20 partidas no patch atual: Yasuo vence 15; Ahri banida em 10. Mais 1 partida do patch anterior.
    await salvar(*(partida(i, vitoria_yasuo=i < 15, ahri_banida=i % 2 == 0) for i in range(20)))
    antiga = partida(-5, True, True, versao="16.19.800.1")  # 5 horas ANTES das outras
    antiga["metadata"]["matchId"] = "BR1_antiga"
    await salvar(antiga)

    dados = (await api.get(TIER_LIST)).json()

    assert dados["patch"] == "16.20"
    assert dados["partidas"] == 20  # a partida do 16.19 fica de fora
    por_nome = {c["champion_name"]: c for c in dados["campeoes"]}
    assert set(por_nome) == {"Yasuo", "Ahri"}  # os outros têm 1 partida cada (< mínimo)
    yasuo, ahri = por_nome["Yasuo"], por_nome["Ahri"]
    assert (yasuo["jogos"], yasuo["vitorias"], yasuo["rota"]) == (20, 15, "MIDDLE")
    assert yasuo["pickrate"] == pytest.approx(1.0)
    assert ahri["winrate"] == pytest.approx(0.25)
    assert ahri["banrate"] == pytest.approx(0.5)
    assert yasuo["banrate"] == 0


async def test_filtro_de_rota(api, riot_mock):
    await salvar(*(partida(i, True, False) for i in range(20)))

    assert (await api.get(TIER_LIST, params={"rota": "TOP"})).json()["campeoes"] == []
    assert len((await api.get(TIER_LIST, params={"rota": "MIDDLE"})).json()["campeoes"]) == 2
    assert (await api.get(TIER_LIST, params={"rota": "MEIO"})).status_code == 422


async def test_sem_partidas(api, riot_mock):
    dados = (await api.get(TIER_LIST)).json()

    assert dados == {"patch": None, "partidas": 0, "minimo_jogos": 15, "prior_jogos": None, "campeoes": []}
