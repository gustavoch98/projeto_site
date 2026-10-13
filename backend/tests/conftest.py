"""Configuração compartilhada dos testes.

As variáveis abaixo são definidas ANTES de importar o app, para que ele use um
banco separado (lolstats_test) e uma chave falsa. Variáveis de ambiente têm
prioridade sobre o .env.
"""

import os

os.environ["DATABASE_URL"] = "postgresql+asyncpg://lolstats:lolstats@localhost:5432/lolstats_test"
os.environ["RIOT_API_KEY"] = "RGAPI-chave-de-teste"

import asyncpg  # noqa: E402
import httpx  # noqa: E402
import pytest  # noqa: E402
import respx  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.riot.client import RiotClient  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
async def banco_de_teste():
    """Cria o banco lolstats_test (se não existir) e as tabelas, uma vez por sessão de testes."""
    conexao = await asyncpg.connect("postgresql://lolstats:lolstats@localhost:5432/lolstats")
    existe = await conexao.fetchval("SELECT 1 FROM pg_database WHERE datname = 'lolstats_test'")
    if not existe:
        await conexao.execute("CREATE DATABASE lolstats_test")
    await conexao.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest.fixture
async def banco_limpo():
    """Esvazia as tabelas antes de cada teste que usa o banco."""
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE accounts, ranked_entries CASCADE"))


@pytest.fixture
def riot_mock():
    """Intercepta todas as chamadas HTTP para a Riot; nenhuma sai para a internet."""
    with respx.mock(assert_all_called=False) as mock:
        yield mock


@pytest.fixture
async def api(banco_limpo, riot_mock):
    """Cliente HTTP que chama o app FastAPI direto em memória, sem subir servidor."""
    app.state.riot = RiotClient("RGAPI-chave-de-teste")
    transporte = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transporte, base_url="http://teste") as cliente:
        yield cliente
    await app.state.riot.close()


@pytest.fixture(autouse=True)
def sem_espera(monkeypatch):
    """Troca o asyncio.sleep por uma versão instantânea durante cada teste.

    Assim os retries após 429/5xx e as esperas do rate limiter não atrasam os testes.
    """

    async def dormir_nada(_segundos):
        return None

    monkeypatch.setattr("asyncio.sleep", dormir_nada)
