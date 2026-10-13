from datetime import datetime

from pydantic import BaseModel, computed_field


class RankedQueue(BaseModel):
    tier: str  # IRON ... CHALLENGER
    rank: str  # I, II, III, IV
    league_points: int
    wins: int
    losses: int

    @computed_field
    @property
    def winrate(self) -> float:
        """Percentual de vitórias com uma casa decimal (ex.: 54.5)."""
        total = self.wins + self.losses
        return round(100 * self.wins / total, 1) if total else 0.0


class PlayerProfile(BaseModel):
    puuid: str
    game_name: str
    tag_line: str
    region: str
    profile_icon_id: int
    summoner_level: int
    solo: RankedQueue | None  # None = Unranked
    flex: RankedQueue | None
    updated_at: datetime
    refresh_available_at: datetime  # a partir de quando o botão "Atualizar" consulta a Riot
    cached: bool  # True = veio do banco; False = acabou de vir da Riot
