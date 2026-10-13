from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db import get_session
from app.models import Account
from app.riot.client import RiotClient
from app.riot.routing import obter_roteamento
from app.schemas.insights import InsightsHorario
from app.schemas.match import MatchSummary
from app.schemas.player import PlayerProfile, PlayerSuggestion
from app.services.insights import calcular_insights_horario
from app.services.matches import (
    completar_historico,
    historico_em_andamento,
    listar_partidas,
    precisa_completar_historico,
)
from app.services.players import buscar_perfil, sugerir_jogadores

router = APIRouter(prefix="/api/players", tags=["players"])


def get_riot_client(request: Request) -> RiotClient:
    """O cliente é criado uma vez na inicialização (ver main.py) e compartilhado."""
    return request.app.state.riot


@router.get("/search", response_model=list[PlayerSuggestion])
async def sugerir(
    q: str = Query(max_length=40, description="Início do nome, opcionalmente com #TAG"),
    region: str = "br",
    session: AsyncSession = Depends(get_session),
):
    """Autocomplete: jogadores já salvos no banco cujo nome começa com `q`. Não consulta a Riot."""
    return await sugerir_jogadores(session, region, q)


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


@router.get("/{region}/{game_name}/{tag_line}/matches", response_model=list[MatchSummary])
async def obter_partidas(
    region: str,
    game_name: str,
    tag_line: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    riot: RiotClient = Depends(get_riot_client),
    settings: Settings = Depends(get_settings),
):
    """Partidas ranqueadas recentes. Busca as que faltam na Riot quando o cache expirou.

    Na primeira visita, agenda também a busca de um histórico mais longo (para o painel de
    insights). Ela roda depois que esta resposta é enviada, sem atrasar a página.
    """
    perfil = await buscar_perfil(session, riot, settings, region, game_name, tag_line)
    conta = await session.get(Account, perfil.puuid)
    rot = obter_roteamento(region)
    partidas = await listar_partidas(session, riot, settings, rot, conta)
    if precisa_completar_historico(conta, settings):
        background_tasks.add_task(
            completar_historico, riot, rot, conta.puuid, settings.historico_partidas
        )
    return partidas


@router.get("/{region}/{game_name}/{tag_line}/insights", response_model=InsightsHorario)
async def obter_insights(
    region: str,
    game_name: str,
    tag_line: str,
    session: AsyncSession = Depends(get_session),
    riot: RiotClient = Depends(get_riot_client),
    settings: Settings = Depends(get_settings),
):
    """Painel do jogador: desempenho por período do dia e dia da semana (horário de Brasília)."""
    perfil = await buscar_perfil(session, riot, settings, region, game_name, tag_line)
    conta = await session.get(Account, perfil.puuid)
    coletando = historico_em_andamento(conta.puuid) or precisa_completar_historico(conta, settings)
    return await calcular_insights_horario(session, conta.puuid, coletando)

