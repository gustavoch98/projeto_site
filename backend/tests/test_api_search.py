"""Testes do autocomplete (GET /api/players/search)."""

from datetime import UTC, datetime

import pytest

from app.db import SessionLocal
from app.models import Account, RankedEntry

BUSCA = "/api/players/search"


async def salvar_contas(*riot_ids: str, region: str = "br"):
    """Insere contas direto no banco, como se já tivessem sido buscadas antes."""
    agora = datetime.now(UTC)
    async with SessionLocal() as session:
        for i, riot_id in enumerate(riot_ids):
            nome, tag = riot_id.split("#")
            session.add(
                Account(
                    puuid=f"puuid-{region}-{i}",
                    game_name=nome,
                    tag_line=tag,
                    region=region,
                    profile_icon_id=1,
                    summoner_level=30,
                    updated_at=agora,
                )
            )
        await session.commit()


def nomes(resposta) -> list[str]:
    return [f"{j['game_name']}#{j['tag_line']}" for j in resposta.json()]


async def test_busca_por_prefixo_sem_diferenciar_maiusculas(api, riot_mock):
    await salvar_contas("Hazze Gu#hazze", "HAZZEL#BR1", "Outro#BR1")

    resposta = await api.get(BUSCA, params={"q": "hAzZ"})

    assert resposta.status_code == 200
    assert nomes(resposta) == ["HAZZEL#BR1", "Hazze Gu#hazze"]  # mais curto primeiro
    assert len(riot_mock.calls) == 0  # autocomplete nunca consulta a Riot


async def test_texto_curto_demais_nao_busca(api):
    await salvar_contas("Hazze Gu#hazze")

    assert (await api.get(BUSCA, params={"q": "h"})).json() == []


async def test_texto_com_tag_filtra_pela_tag(api):
    await salvar_contas("Fulano#BR1", "Fulano#abc")

    resposta = await api.get(BUSCA, params={"q": "fulano#a"})

    assert nomes(resposta) == ["Fulano#abc"]


async def test_espacos_extras_sao_ignorados(api):
    await salvar_contas("Hazze Gu#hazze")

    assert nomes(await api.get(BUSCA, params={"q": "  hazze   g"})) == ["Hazze Gu#hazze"]


@pytest.mark.parametrize("curinga", ["%%", "__"])
async def test_curingas_do_like_sao_texto_literal(api, curinga):
    await salvar_contas("Qualquer#BR1")

    assert (await api.get(BUSCA, params={"q": curinga})).json() == []


async def test_so_busca_na_regiao_pedida(api):
    await salvar_contas("Fulano#BR1", region="na")

    assert (await api.get(BUSCA, params={"q": "fulano"})).json() == []


async def test_limita_a_oito_resultados(api):
    await salvar_contas(*[f"Teste{i}#BR1" for i in range(12)])

    assert len((await api.get(BUSCA, params={"q": "teste"})).json()) == 8


async def test_inclui_elo_solo(api):
    await salvar_contas("Fulano#BR1")
    async with SessionLocal() as session:
        session.add(
            RankedEntry(
                puuid="puuid-br-0",
                queue_type="RANKED_SOLO_5x5",
                tier="GOLD",
                rank="I",
                league_points=10,
                wins=1,
                losses=1,
                updated_at=datetime.now(UTC),
            )
        )
        await session.commit()

    sugestao = (await api.get(BUSCA, params={"q": "ful"})).json()[0]

    assert sugestao["solo"]["tier"] == "GOLD"
