import httpx
import pytest

from app.riot.client import (
    RiotChaveInvalida,
    RiotClient,
    RiotIndisponivel,
    RiotLimiteExcedido,
    RiotNaoEncontrado,
)
from app.riot.routing import REGIOES

BR = REGIOES["br"]
URL_CONTA = "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/Fulano%20de%20Tal/BR1"
CONTA = {"puuid": "puuid-1", "gameName": "Fulano de Tal", "tagLine": "BR1"}


@pytest.fixture
async def cliente():
    c = RiotClient("RGAPI-chave-de-teste")
    yield c
    await c.close()


async def test_sucesso_envia_a_chave_no_header(cliente, riot_mock):
    rota = riot_mock.get(URL_CONTA).respond(200, json=CONTA)

    assert await cliente.conta_por_riot_id(BR, "Fulano de Tal", "BR1") == CONTA
    assert rota.calls.last.request.headers["X-Riot-Token"] == "RGAPI-chave-de-teste"


async def test_summoner_e_league_usam_host_de_plataforma(cliente, riot_mock):
    riot_mock.get("https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/p1").respond(
        200, json={"puuid": "p1", "profileIconId": 1, "summonerLevel": 30}
    )
    riot_mock.get("https://br1.api.riotgames.com/lol/league/v4/entries/by-puuid/p1").respond(200, json=[])

    assert (await cliente.summoner_por_puuid(BR, "p1"))["summonerLevel"] == 30
    assert await cliente.ranked_por_puuid(BR, "p1") == []


@pytest.mark.parametrize(
    ("status", "excecao"),
    [(404, RiotNaoEncontrado), (401, RiotChaveInvalida), (403, RiotChaveInvalida)],
)
async def test_erros_viram_excecoes(cliente, riot_mock, status, excecao):
    riot_mock.get(URL_CONTA).respond(status)
    with pytest.raises(excecao):
        await cliente.conta_por_riot_id(BR, "Fulano de Tal", "BR1")


async def test_429_espera_retry_after_e_tenta_de_novo(cliente, riot_mock):
    rota = riot_mock.get(URL_CONTA)
    rota.side_effect = [
        httpx.Response(429, headers={"Retry-After": "2"}),
        httpx.Response(200, json=CONTA),
    ]

    assert await cliente.conta_por_riot_id(BR, "Fulano de Tal", "BR1") == CONTA
    assert rota.call_count == 2


async def test_429_com_espera_longa_desiste(cliente, riot_mock):
    riot_mock.get(URL_CONTA).respond(429, headers={"Retry-After": "60"})

    with pytest.raises(RiotLimiteExcedido) as info:
        await cliente.conta_por_riot_id(BR, "Fulano de Tal", "BR1")
    assert info.value.retry_after == 60


async def test_5xx_tenta_tres_vezes_e_desiste(cliente, riot_mock):
    rota = riot_mock.get(URL_CONTA).respond(503)

    with pytest.raises(RiotIndisponivel):
        await cliente.conta_por_riot_id(BR, "Fulano de Tal", "BR1")
    assert rota.call_count == 3


async def test_falha_de_rede_vira_riot_indisponivel(cliente, riot_mock):
    riot_mock.get(URL_CONTA).mock(side_effect=httpx.ConnectError("sem rede"))

    with pytest.raises(RiotIndisponivel):
        await cliente.conta_por_riot_id(BR, "Fulano de Tal", "BR1")
