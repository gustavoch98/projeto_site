"""Ponto de entrada da API.

Rodar localmente (na pasta backend, com o .venv ativado):
    uvicorn app.main:app --reload
Documentação interativa: http://localhost:8000/docs
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import get_settings
from app.db import SessionLocal
from app.riot.client import (
    RiotChaveInvalida,
    RiotClient,
    RiotIndisponivel,
    RiotLimiteExcedido,
    RiotNaoEncontrado,
)
from app.riot.routing import RegiaoInvalida
from app.routes import players
from app.services.players import RiotIdInvalido

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Executa ao iniciar o servidor: um único cliente HTTP reaproveita conexões
    # e mantém um único controle de rate limit para toda a aplicação.
    app.state.riot = RiotClient(get_settings().riot_api_key.get_secret_value())
    yield
    # Executa ao desligar
    await app.state.riot.close()


app = FastAPI(title="LoL Stats API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins_list,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(players.router)


@app.get("/health", tags=["health"])
async def health():
    """Usado pelo monitoramento do deploy: confirma que a API e o banco respondem."""
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Health check: banco indisponível")
        return JSONResponse(status_code=503, content={"status": "erro", "database": "indisponível"})
    return {"status": "ok", "database": "ok"}


# --- Tradução das exceções em respostas HTTP ---------------------------------


def erro(status: int, mensagem: str, headers: dict | None = None) -> JSONResponse:
    return JSONResponse(status_code=status, content={"detail": mensagem}, headers=headers)


@app.exception_handler(RegiaoInvalida)
async def tratar_regiao_invalida(request: Request, exc: RegiaoInvalida):
    return erro(404, str(exc))


@app.exception_handler(RiotIdInvalido)
async def tratar_riot_id_invalido(request: Request, exc: RiotIdInvalido):
    return erro(422, str(exc))


@app.exception_handler(RiotNaoEncontrado)
async def tratar_nao_encontrado(request: Request, exc: RiotNaoEncontrado):
    return erro(404, "Jogador não encontrado.")


@app.exception_handler(RiotLimiteExcedido)
async def tratar_limite(request: Request, exc: RiotLimiteExcedido):
    return erro(
        503,
        "Muitas buscas no momento. Tente novamente em instantes.",
        headers={"Retry-After": str(exc.retry_after)},
    )


@app.exception_handler(RiotChaveInvalida)
async def tratar_chave_invalida(request: Request, exc: RiotChaveInvalida):
    # Problema nosso (chave expirada); não expomos detalhes ao usuário
    logger.error("Chave da Riot inválida ou expirada (%s). Gere uma nova e atualize o .env.", exc)
    return erro(502, "Serviço da Riot indisponível no momento.")


@app.exception_handler(RiotIndisponivel)
async def tratar_riot_indisponivel(request: Request, exc: RiotIndisponivel):
    logger.error("Riot indisponível: %s", exc)
    return erro(502, "Serviço da Riot indisponível no momento.")
