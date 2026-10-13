"""Testes do painel de insights (GET .../insights) e do histórico em segundo plano."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import Account, Match
from app.riot.client import RiotClient
from app.riot.routing import REGIOES
from app.services.insights import wilson
from app.services.matches import completar_historico, salvar_partida
from tests.test_api_matches import URL_IDS, partida_falsa, simular_partidas
from tests.test_api_players import PERFIL, PUUID, simular_riot

INSIGHTS = PERFIL + "/insights"


def partida_em(match_id: str, inicio_utc: datetime, vitoria: bool, duracao: int = 1800) -> dict:
    dados = partida_falsa(match_id, duracao=duracao, vitoria=vitoria)
    dados["info"]["gameStartTimestamp"] = int(inicio_utc.timestamp() * 1000)
    return dados


async def salvar(*partidas: dict):
    async with SessionLocal() as session:
        for p in partidas:
            await salvar_partida(session, p)
        await session.commit()


def faixa(dados: dict, grupo: str, chave: str) -> dict:
    return next(f for f in dados[grupo] if f["chave"] == chave)


async def test_agrupa_por_periodo_no_horario_de_brasilia(api, riot_mock):
    simular_riot(riot_mock)
    await salvar(
        partida_em("BR1_1", datetime(2026, 10, 1, 15, 0, tzinfo=UTC), True),  # 12h BRT: tarde
        partida_em("BR1_2", datetime(2026, 10, 1, 16, 0, tzinfo=UTC), False),  # 13h: tarde
        partida_em("BR1_3", datetime(2026, 10, 1, 23, 30, tzinfo=UTC), True),  # 20h30: noite
        partida_em("BR1_4", datetime(2026, 10, 2, 4, 0, tzinfo=UTC), False),  # 01h: madrugada
    )

    dados = (await api.get(INSIGHTS)).json()

    assert dados["partidas_analisadas"] == 4
    assert dados["winrate_geral"] == 0.5
    tarde = faixa(dados, "por_periodo", "tarde")
    assert (tarde["jogos"], tarde["vitorias"], tarde["winrate"]) == (2, 1, 0.5)
    assert tarde["ic_baixo"] < 0.5 < tarde["ic_alto"]
    assert faixa(dados, "por_periodo", "noite")["vitorias"] == 1
    assert faixa(dados, "por_periodo", "madrugada")["jogos"] == 1
    # Faixa sem partidas aparece, mas sem winrate
    assert faixa(dados, "por_periodo", "manha") == {
        "chave": "manha", "rotulo": "Manhã (6h–11h)", "jogos": 0, "vitorias": 0,
        "winrate": None, "ic_baixo": None, "ic_alto": None,
    }


async def test_dia_da_semana_usa_o_horario_de_brasilia(api, riot_mock):
    simular_riot(riot_mock)
    # Sábado 03/10 às 02h UTC = sexta 02/10 às 23h em Brasília
    await salvar(partida_em("BR1_1", datetime(2026, 10, 3, 2, 0, tzinfo=UTC), True))

    dados = (await api.get(INSIGHTS)).json()

    assert faixa(dados, "por_dia_semana", "5")["jogos"] == 1  # sexta
    assert faixa(dados, "por_dia_semana", "6")["jogos"] == 0  # sábado


async def test_remakes_ficam_fora(api, riot_mock):
    simular_riot(riot_mock)
    await salvar(
        partida_em("BR1_1", datetime(2026, 10, 1, 15, 0, tzinfo=UTC), True),
        partida_em("BR1_2", datetime(2026, 10, 1, 16, 0, tzinfo=UTC), False, duracao=200),
    )

    assert (await api.get(INSIGHTS)).json()["partidas_analisadas"] == 1


async def test_jogador_sem_partidas(api, riot_mock):
    simular_riot(riot_mock)

    dados = (await api.get(INSIGHTS)).json()

    assert dados["partidas_analisadas"] == 0
    assert dados["winrate_geral"] is None
    assert dados["coletando_historico"] is False  # HISTORICO_PARTIDAS=0 nos testes


def test_wilson():
    baixo, alto = wilson(5, 10)
    assert baixo == pytest.approx(0.2366, abs=1e-4)
    assert alto == pytest.approx(0.7634, abs=1e-4)
    assert wilson(10, 10)[1] == 1.0  # nunca passa de 100%


async def test_completar_historico_busca_as_partidas_que_faltam(api, riot_mock):
    simular_riot(riot_mock)
    await api.get(PERFIL)  # cria a conta
    partidas = [partida_falsa(f"BR1_{i}", horas_atras=i) for i in range(3)]
    await salvar(partidas[0])  # uma já está no banco
    riot_mock.routes.clear()
    rota_ids, rotas = simular_partidas(riot_mock, partidas)

    riot = RiotClient("RGAPI-chave-de-teste")
    await completar_historico(riot, REGIOES["br"], PUUID, alvo=3)
    await riot.close()

    assert rota_ids.called
    assert rotas["BR1_0"].call_count == 0  # já estava salva
    assert rotas["BR1_1"].call_count == rotas["BR1_2"].call_count == 1
    async with SessionLocal() as session:
        assert await session.scalar(select(func.count()).select_from(Match)) == 3
        conta = await session.get(Account, PUUID)
        assert conta.history_backfilled_at is not None


async def test_completar_historico_com_falha_tenta_de_novo_depois(api, riot_mock):
    simular_riot(riot_mock)
    await api.get(PERFIL)
    riot_mock.get(url__startswith=URL_IDS).respond(503)

    riot = RiotClient("RGAPI-chave-de-teste")
    await completar_historico(riot, REGIOES["br"], PUUID, alvo=3)
    await riot.close()

    async with SessionLocal() as session:
        assert (await session.get(Account, PUUID)).history_backfilled_at is None
