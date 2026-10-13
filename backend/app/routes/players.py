from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db import get_session
from app.riot.client import RiotClient
from app.schemas.player import PlayerProfile
from app.services.players import buscar_perfil

router = APIRouter(prefix="/api/players", tags=["players"])


def get_riot_client(request: Request) -> RiotClient:
    """O cliente é criado uma vez na inicialização (ver main.py) e compartilhado."""
    return request.app.state.riot


@router.get("/{region}/{game_name}/{tag_line}", response_model=PlayerProfile)
async def obter_perfil(
    region: str,
    game_name: str,
    tag_line: str,
    session: AsyncSession = Depends(get_session),
    riot: RiotClient = Depends(get_riot_client),
    settings: Settings = Depends(get_settings),
):
    """Perfil do jogador (conta + nível + ranked). Usa o cache do banco quando possível."""
    return await buscar_perfil(session, riot, settings, region, game_name, tag_line)


@router.post("/{region}/{game_name}/{tag_line}/refresh", response_model=PlayerProfile)
async def atualizar_perfil(
    region: str,
    game_name: str,
    tag_line: str,
    session: AsyncSession = Depends(get_session),
    riot: RiotClient = Depends(get_riot_client),
    settings: Settings = Depends(get_settings),
):
    """Força nova consulta à Riot, respeitando o intervalo mínimo entre atualizações."""
    return await buscar_perfil(
        session, riot, settings, region, game_name, tag_line, forcar=True
    )
