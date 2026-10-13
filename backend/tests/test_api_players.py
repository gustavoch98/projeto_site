"""Testes do fluxo completo: rota -> serviço -> banco de teste, com a Riot simulada."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import update

from app.db import SessionLocal
from app.models import Account

PUUID = "puuid-fulano"
URL_CONTA = "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/fulano%20de%20tal/br1"
URL_SUMMONER = f"https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{PUUID}"
URL_LEAGUE = f"https://br1.api.riotgames.com/lol/league/v4/entries/by-puuid/{PUUID}"

PERFIL = "/api/players/br/fulano de tal/br1"

SOLO = {
    "queueType": "RANKED_SOLO_5x5",
    "tier": "GOLD",
    "rank": "II",
    "puuid": PUUID,
    "leaguePoints": 45,
    "wins": 30,
    "losses": 20,
}


def simular_riot(riot_mock, ranked=None, nivel=100):
    """Registra respostas falsas da Riot e devolve a rota da Account-V1 (para contar chamadas)."""
    conta = riot_mock.get(URL_CONTA).respond(
        200, json={"puuid": PUUID, "gameName": "Fulano de Tal", "tagLine": "BR1"}
    )
    riot_mock.get(URL_SUMMONER).respond(
        200, json={"puuid": PUUID, "profileIconId": 29, "summonerLevel": nivel}
    )
    riot_mock.get(URL_LEAGUE).respond(200, json=[SOLO] if ranked is None else ranked)
    return conta


async def envelhecer_cache(minutos: int):
    """Simula que os dados no banco foram salvos há X minutos."""
    async with SessionLocal() as session:
        await session.execute(
            update(Account).values(updated_at=datetime.now(UTC) - timedelta(minutes=minutos))
        )
        await session.commit()


async def test_primeira_busca_consulta_a_riot_e_salva(api, riot_mock):
    simular_riot(riot_mock)

    resposta = await api.get(PERFIL)

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["cached"] is False
    assert dados["game_name"] == "Fulano de Tal"  # nome "oficial", não o digitado
    assert dados["tag_line"] == "BR1"
    assert dados["summoner_level"] == 100
    assert dados["solo"] == {
        "tier": "GOLD",
        "rank": "II",
        "league_points": 45,
        "wins": 30,
        "losses": 20,
        "winrate": 60.0,
    }
    assert dados["flex"] is None  # Unranked


async def test_segunda_busca_vem_do_cache(api, riot_mock):
    rota_conta = simular_riot(riot_mock)
    await api.get(PERFIL)

    resposta = await api.get("/api/players/BR/FULANO DE TAL/Br1")  # maiúsculas diferentes

    assert resposta.json()["cached"] is True
    assert rota_conta.call_count == 1


async def test_cache_expirado_consulta_a_riot_de_novo(api, riot_mock):
    rota_conta = simular_riot(riot_mock)
    await api.get(PERFIL)
    await envelhecer_cache(minutos=11)

    resposta = await api.get(PERFIL)

    assert resposta.json()["cached"] is False
    assert rota_conta.call_count == 2


async def test_refresh_respeita_intervalo_minimo(api, riot_mock):
    rota_conta = simular_riot(riot_mock)
    await api.get(PERFIL)

    resposta = await api.post(PERFIL + "/refresh")

    assert resposta.json()["cached"] is True
    assert rota_conta.call_count == 1


async def test_refresh_apos_intervalo_minimo_ignora_ttl(api, riot_mock):
    rota_conta = simular_riot(riot_mock)
    await api.get(PERFIL)
    await envelhecer_cache(minutos=3)  # dentro do TTL de 10 min, fora do intervalo de 2 min

    assert (await api.get(PERFIL)).json()["cached"] is True
    resposta = await api.post(PERFIL + "/refresh")

    assert resposta.json()["cached"] is False
    assert rota_conta.call_count == 2


async def test_atualizacao_substitui_ranked(api, riot_mock):
    simular_riot(riot_mock)
    await api.get(PERFIL)
    await envelhecer_cache(minutos=11)

    riot_mock.routes.clear()
    flex = {**SOLO, "queueType": "RANKED_FLEX_SR", "tier": "SILVER"}
    simular_riot(riot_mock, ranked=[flex], nivel=101)
    dados = (await api.get(PERFIL)).json()

    assert dados["summoner_level"] == 101
    assert dados["solo"] is None
    assert dados["flex"]["tier"] == "SILVER"


async def test_jogador_inexistente_retorna_404(api, riot_mock):
    riot_mock.get(URL_CONTA).respond(404)

    resposta = await api.get(PERFIL)

    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Jogador não encontrado."}


async def test_riot_fora_do_ar_sem_cache_retorna_502(api, riot_mock):
    riot_mock.get(URL_CONTA).respond(503)

    assert (await api.get(PERFIL)).status_code == 502


async def test_riot_fora_do_ar_com_cache_antigo_devolve_cache(api, riot_mock):
    simular_riot(riot_mock)
    await api.get(PERFIL)
    await envelhecer_cache(minutos=60)

    riot_mock.routes.clear()
    riot_mock.get(URL_CONTA).respond(503)
    resposta = await api.get(PERFIL)

    assert resposta.status_code == 200
    assert resposta.json()["cached"] is True


async def test_limite_excedido_retorna_503_com_retry_after(api, riot_mock):
    riot_mock.get(URL_CONTA).respond(429, headers={"Retry-After": "90"})

    resposta = await api.get(PERFIL)

    assert resposta.status_code == 503
    assert resposta.headers["Retry-After"] == "90"


async def test_regiao_nao_suportada_retorna_404(api):
    assert (await api.get("/api/players/kr/Fulano/KR1")).status_code == 404


async def test_health(api):
    assert (await api.get("/health")).json() == {"status": "ok", "database": "ok"}


async def test_pedidos_simultaneos_com_cache_vencido_nao_quebram(api, riot_mock):
    """A página do perfil faz vários pedidos ao mesmo tempo (layout + seções). Com o cache
    vencido, todos tentam regravar o elo juntos: precisa funcionar sem erro de chave duplicada."""
    import asyncio

    flex = {**SOLO, "queueType": "RANKED_FLEX_SR", "tier": "SILVER"}
    simular_riot(riot_mock, ranked=[SOLO, flex])
    await api.get(PERFIL)
    await envelhecer_cache(minutos=60)

    respostas = await asyncio.gather(*(api.get(PERFIL) for _ in range(4)))

    assert [r.status_code for r in respostas] == [200, 200, 200, 200]
    assert respostas[0].json()["flex"]["tier"] == "SILVER"


async def test_pedidos_simultaneos_de_jogador_novo_nao_quebram(api, riot_mock):
    import asyncio

    simular_riot(riot_mock)

    respostas = await asyncio.gather(*(api.get(PERFIL) for _ in range(4)))

    assert [r.status_code for r in respostas] == [200, 200, 200, 200]
