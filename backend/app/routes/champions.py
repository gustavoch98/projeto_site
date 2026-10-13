from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.tierlist import TierList
from app.services.tierlist import calcular_tier_list

router = APIRouter(prefix="/api/champions", tags=["champions"])

Rota = Literal["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]


@router.get("/tierlist", response_model=TierList)
async def obter_tier_list(rota: Rota | None = None, session: AsyncSession = Depends(get_session)):
    """Tier list do patch mais recente (Solo/Duo), calculada com as partidas do nosso banco.

    `rota` filtra uma rota (TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY); sem ela, vêm todas.
    Não consulta a Riot.
    """
    return await calcular_tier_list(session, rota)
