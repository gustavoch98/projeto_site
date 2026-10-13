"""Testes da aba de evolução (GET .../evolution) e das médias por rota (GET .../champions)."""

from datetime import UTC, datetime, timedelta

import pytest

from app.services.insights import pontos_do_elo, sequencias
from tests.test_api_matches import partida_falsa
from tests.test_api_players import PERFIL, SOLO, envelhecer_cache, simular_riot
from tests.test_campeoes import AHRI, YASUO, partida_com
from tests.test_insights import salvar

EVOLUCAO = PERFIL + "/evolution"
INICIO = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)


def partidas_em_sequencia(resultados: str, fila: int = 420) -> list[dict]:
    """'VVD' -> três partidas, uma por hora, na ordem: vitória, vitória, derrota."""
    partidas = []
    for i, letra in enumerate(resultados):
        dados = partida_falsa(f"BR1_{i}", vitoria=letra == "V")
        dados["info"]["gameStartTimestamp"] = int((INICIO + timedelta(hours=i)).timestamp() * 1000)
        dados["info"]["queueId"] = fila
        partidas.append(dados)
    return partidas


def test_pontos_do_elo():
    assert pontos_do_elo("IRON", "IV", 0) == 0
    assert pontos_do_elo("IRON", "III", 50) == 150
    assert pontos_do_elo("EMERALD", "II", 12) == 2212  # 5 elos x 400 + 2 divisões x 100 + 12
    assert pontos_do_elo("DIAMOND", "I", 99) == 2799
    assert pontos_do_elo("MASTER", "I", 150) == 2950  # sem divisões: 2800 + PDL
    assert pontos_do_elo("CHALLENGER", "I", 1500) == 4300


@pytest.mark.parametrize(
    ("resultados", "esperado"),
    [
        ("", (0, 0, 0)),
        ("VVVDV", (3, 1, 1)),
        ("DDVDDD", (1, 3, -3)),
        ("VVDDDVV", (2, 3, 2)),
    ],
)
def test_sequencias(resultados, esperado):
    assert sequencias([letra == "V" for letra in resultados]) == esperado


async def test_saldo_e_sequencias(api, riot_mock):
    simular_riot(riot_mock)
    await salvar(*partidas_em_sequencia("VVDVDDD"))

    dados = (await api.get(EVOLUCAO)).json()

    assert [p["saldo"] for p in dados["partidas"]] == [1, 2, 1, 2, 1, 0, -1]
    assert (dados["vitorias"], dados["derrotas"]) == (3, 4)
    assert dados["maior_sequencia_vitorias"] == 2
    assert dados["maior_sequencia_derrotas"] == 3
    assert dados["sequencia_atual"] == -3


async def test_winrate_movel_so_aparece_com_10_partidas(api, riot_mock):
    simular_riot(riot_mock)
    await salvar(*partidas_em_sequencia("VD" * 12))  # 24 partidas alternadas

    partidas = (await api.get(EVOLUCAO)).json()["partidas"]

    assert all(p["winrate_movel"] is None for p in partidas[:9])
    assert partidas[9]["winrate_movel"] == pytest.approx(0.5)  # 10 partidas: 5V 5D
    assert partidas[-1]["winrate_movel"] == pytest.approx(0.5)  # janela de 20


async def test_so_conta_solo_duo(api, riot_mock):
    simular_riot(riot_mock)
    await salvar(*partidas_em_sequencia("VVV", fila=440))  # Flex

    assert (await api.get(EVOLUCAO)).json()["partidas"] == []


async def test_fotos_de_pdl_em_ordem(api, riot_mock):
    simular_riot(riot_mock)
    await api.get(PERFIL)  # 1ª foto: Ouro II 45 PDL
    await envelhecer_cache(minutos=11)
    riot_mock.get(
        "https://br1.api.riotgames.com/lol/league/v4/entries/by-puuid/puuid-fulano"
    ).respond(200, json=[{**SOLO, "tier": "GOLD", "rank": "I", "leaguePoints": 10, "wins": 31}])
    await api.get(PERFIL)  # 2ª foto: Ouro I 10 PDL

    fotos = (await api.get(EVOLUCAO)).json()["fotos"]

    assert [(f["tier"], f["rank"], f["pdl"]) for f in fotos] == [("GOLD", "II", 45), ("GOLD", "I", 10)]
    assert [f["pontos"] for f in fotos] == [1445, 1510]  # Ouro = 3 elos x 400 + divisão x 100 + PDL


async def test_medias_por_rota(api, riot_mock):
    simular_riot(riot_mock)
    await salvar(
        partida_com("BR1_1", YASUO, True, rota="MIDDLE", totalMinionsKilled=240, neutralMinionsKilled=0),
        partida_com("BR1_2", AHRI, False, rota="MIDDLE", totalMinionsKilled=240, neutralMinionsKilled=0),
        partida_com("BR1_3", AHRI, True, rota="UTILITY", totalMinionsKilled=30, neutralMinionsKilled=0),
    )

    medias = (await api.get(PERFIL + "/champions")).json()["medias_por_rota"]

    assert set(medias) == {"MIDDLE", "UTILITY"}
    assert medias["MIDDLE"]["jogos"] == 2
    assert medias["MIDDLE"]["cs_por_minuto"] == pytest.approx(8.0)  # 240 em 30 min
    assert medias["UTILITY"]["cs_por_minuto"] == pytest.approx(1.0)
