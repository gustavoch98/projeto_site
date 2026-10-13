"""Testes da ingestão de partidas (GET .../matches) e do histórico de ranked."""

from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import func, select, update

from app.db import SessionLocal
from app.models import Account, Match, RankedHistory
from tests.test_api_players import PERFIL, PUUID, SOLO, URL_LEAGUE, simular_riot

PARTIDAS = PERFIL + "/matches"
URL_IDS = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{PUUID}/ids"
URL_PARTIDA = "https://americas.api.riotgames.com/lol/match/v5/matches/"

INICIO = datetime(2026, 10, 1, 20, 0, tzinfo=UTC)


def participante(puuid: str, time: int, vitoria: bool, **extra) -> dict:
    return {
        "puuid": puuid,
        "riotIdGameName": f"Jogador {puuid[-2:]}",
        "riotIdTagline": "BR1",
        "teamId": time,
        "teamPosition": "MIDDLE",
        "championId": 157,
        "championName": "Yasuo",
        "win": vitoria,
        "kills": 7,
        "deaths": 2,
        "assists": 5,
        "totalMinionsKilled": 200,
        "neutralMinionsKilled": 10,
        "goldEarned": 12000,
        "totalDamageDealtToChampions": 20000,
        "visionScore": 15,
        "challenges": {"killParticipation": 0.5},
        **{f"item{i}": 1000 + i for i in range(7)},
        "summoner1Id": 4,
        "summoner2Id": 14,
        "gameEndedInEarlySurrender": False,
        **extra,
    }


def partida_falsa(match_id: str, horas_atras: int = 0, duracao: int = 1800, vitoria=True) -> dict:
    """JSON no formato do Match-V5, com o jogador do teste e mais 9 participantes."""
    inicio = INICIO - timedelta(hours=horas_atras)
    jogadores = [participante(PUUID, 100, vitoria)]
    jogadores += [participante(f"outro-{i:02d}", 100 if i < 4 else 200, vitoria == (i < 4)) for i in range(9)]
    return {
        "metadata": {"matchId": match_id, "participants": [j["puuid"] for j in jogadores]},
        "info": {
            "gameStartTimestamp": int(inicio.timestamp() * 1000),
            "gameDuration": duracao,
            "gameVersion": "16.20.824.8524",
            "platformId": "BR1",
            "queueId": 420,
            "participants": jogadores,
        },
    }


def simular_partidas(riot_mock, partidas: list[dict]):
    """Registra a lista de IDs e o detalhe de cada partida. Devolve as rotas para contar chamadas."""
    rota_ids = riot_mock.get(url__startswith=URL_IDS).respond(
        200, json=[p["metadata"]["matchId"] for p in partidas]
    )
    rotas = {
        p["metadata"]["matchId"]: riot_mock.get(URL_PARTIDA + p["metadata"]["matchId"]).respond(
            200, json=p
        )
        for p in partidas
    }
    return rota_ids, rotas


async def envelhecer_sincronizacao(minutos: int):
    async with SessionLocal() as session:
        antigo = datetime.now(UTC) - timedelta(minutes=minutos)
        await session.execute(update(Account).values(updated_at=antigo, matches_synced_at=antigo))
        await session.commit()


async def test_primeira_consulta_busca_e_salva_as_partidas(api, riot_mock):
    simular_riot(riot_mock)
    simular_partidas(riot_mock, [partida_falsa("BR1_2", horas_atras=1), partida_falsa("BR1_1", horas_atras=5)])

    resposta = await api.get(PARTIDAS)

    assert resposta.status_code == 200
    partidas = resposta.json()
    assert [p["match_id"] for p in partidas] == ["BR1_2", "BR1_1"]  # mais recente primeiro
    assert partidas[0]["champion_name"] == "Yasuo"
    assert partidas[0]["cs"] == 210
    assert partidas[0]["kda"] == 6.0  # (7 + 5) / 2
    assert partidas[0]["cs_per_minute"] == 7.0  # 210 / 30 min
    assert partidas[0]["remake"] is False
    async with SessionLocal() as session:
        assert await session.scalar(select(func.count()).select_from(Match)) == 2


async def test_dentro_do_ttl_nao_consulta_a_riot_de_novo(api, riot_mock):
    simular_riot(riot_mock)
    rota_ids, _ = simular_partidas(riot_mock, [partida_falsa("BR1_1")])
    await api.get(PARTIDAS)

    await api.get(PARTIDAS)

    assert rota_ids.call_count == 1


async def test_partidas_ja_salvas_nao_sao_buscadas_de_novo(api, riot_mock):
    simular_riot(riot_mock)
    antiga = partida_falsa("BR1_1", horas_atras=5)
    _, rotas = simular_partidas(riot_mock, [antiga])
    await api.get(PARTIDAS)
    await envelhecer_sincronizacao(minutos=11)

    riot_mock.routes.clear()
    simular_riot(riot_mock)
    _, rotas = simular_partidas(riot_mock, [partida_falsa("BR1_2", horas_atras=1), antiga])
    partidas = (await api.get(PARTIDAS)).json()

    assert [p["match_id"] for p in partidas] == ["BR1_2", "BR1_1"]
    assert rotas["BR1_2"].call_count == 1
    assert rotas["BR1_1"].call_count == 0  # já estava no banco


async def test_partida_curta_e_marcada_como_remake(api, riot_mock):
    simular_riot(riot_mock)
    simular_partidas(riot_mock, [partida_falsa("BR1_1", duracao=200)])

    assert (await api.get(PARTIDAS)).json()[0]["remake"] is True


async def test_falha_da_riot_devolve_partidas_do_banco(api, riot_mock):
    simular_riot(riot_mock)
    simular_partidas(riot_mock, [partida_falsa("BR1_1")])
    await api.get(PARTIDAS)
    await envelhecer_sincronizacao(minutos=11)

    riot_mock.routes.clear()
    simular_riot(riot_mock)
    riot_mock.get(url__startswith=URL_IDS).mock(side_effect=httpx.ConnectError("fora do ar"))
    resposta = await api.get(PARTIDAS)

    assert resposta.status_code == 200
    assert [p["match_id"] for p in resposta.json()] == ["BR1_1"]


async def contar_fotos() -> int:
    async with SessionLocal() as session:
        return await session.scalar(select(func.count()).select_from(RankedHistory))


async def test_historico_de_ranked_so_grava_quando_muda(api, riot_mock):
    simular_riot(riot_mock)
    await api.get(PERFIL)
    assert await contar_fotos() == 1

    # Nova consulta à Riot com o mesmo elo: nenhuma foto nova
    await envelhecer_sincronizacao(minutos=11)
    await api.get(PERFIL)
    assert await contar_fotos() == 1

    # PDL mudou: grava outra foto
    await envelhecer_sincronizacao(minutos=11)
    riot_mock.get(URL_LEAGUE).respond(200, json=[{**SOLO, "leaguePoints": 66, "wins": 31}])
    await api.get(PERFIL)
    assert await contar_fotos() == 2
