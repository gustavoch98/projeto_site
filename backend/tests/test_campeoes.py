"""Testes da aba de campeões (GET .../champions)."""

import pytest

from tests.test_api_matches import partida_falsa
from tests.test_api_players import PERFIL, simular_riot
from tests.test_insights import salvar

CAMPEOES = PERFIL + "/champions"


def partida_com(match_id: str, campeao: tuple[int, str], vitoria: bool, rota="MIDDLE", **stats) -> dict:
    """Partida falsa em que o jogador do teste (participante 0) joga o campeão indicado."""
    dados = partida_falsa(match_id, vitoria=vitoria)
    eu = dados["info"]["participants"][0]
    eu.update(championId=campeao[0], championName=campeao[1], teamPosition=rota, **stats)
    return dados


YASUO = (157, "Yasuo")
AHRI = (103, "Ahri")


async def test_agrupa_por_campeao_do_mais_jogado_ao_menos(api, riot_mock):
    simular_riot(riot_mock)
    await salvar(
        partida_com("BR1_1", YASUO, True),
        partida_com("BR1_2", YASUO, False),
        partida_com("BR1_3", YASUO, True, rota="TOP"),
        partida_com("BR1_4", AHRI, True),
    )

    dados = (await api.get(CAMPEOES)).json()

    assert dados["partidas_analisadas"] == 4
    assert dados["minimo_partidas"] == 10
    assert [c["champion_name"] for c in dados["campeoes"]] == ["Yasuo", "Ahri"]
    yasuo = dados["campeoes"][0]
    assert (yasuo["jogos"], yasuo["vitorias"]) == (3, 2)
    assert yasuo["winrate"] == pytest.approx(2 / 3)
    assert yasuo["rota_principal"] == "MIDDLE"  # 2 de 3 partidas no meio


async def test_calcula_medias_e_taxas_por_minuto(api, riot_mock):
    simular_riot(riot_mock)
    # 30 min cada: CS 210 -> 7/min; dano 20000 -> 666,7/min
    await salvar(
        partida_com("BR1_1", YASUO, True, kills=10, deaths=2, assists=4),
        partida_com("BR1_2", YASUO, False, kills=2, deaths=6, assists=0),
    )

    yasuo = (await api.get(CAMPEOES)).json()["campeoes"][0]

    assert yasuo["kda"] == pytest.approx((12 + 4) / 8)  # soma de tudo, não média de KDAs
    assert yasuo["abates"] == 6
    assert yasuo["mortes"] == 4
    assert yasuo["cs_por_minuto"] == pytest.approx(7.0)
    assert yasuo["dano_por_minuto"] == pytest.approx(20000 / 30)
    assert yasuo["participacao_abates"] == pytest.approx(0.5)


async def test_geral_soma_todos_os_campeoes(api, riot_mock):
    simular_riot(riot_mock)
    await salvar(
        partida_com("BR1_1", YASUO, True),
        partida_com("BR1_2", AHRI, False),
    )

    geral = (await api.get(CAMPEOES)).json()["geral"]

    assert geral["champion_id"] is None
    assert (geral["jogos"], geral["vitorias"], geral["winrate"]) == (2, 1, 0.5)


async def test_remakes_ficam_fora(api, riot_mock):
    simular_riot(riot_mock)
    remake = partida_com("BR1_2", AHRI, False)
    remake["info"]["gameDuration"] = 200
    await salvar(partida_com("BR1_1", YASUO, True), remake)

    dados = (await api.get(CAMPEOES)).json()

    assert [c["champion_name"] for c in dados["campeoes"]] == ["Yasuo"]


async def test_jogador_sem_partidas(api, riot_mock):
    simular_riot(riot_mock)

    dados = (await api.get(CAMPEOES)).json()

    assert dados["partidas_analisadas"] == 0
    assert dados["geral"] is None
    assert dados["campeoes"] == []
