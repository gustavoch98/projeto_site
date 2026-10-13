from datetime import datetime

from pydantic import BaseModel, computed_field


class MatchSummary(BaseModel):
    """Uma partida do ponto de vista de um jogador (uma linha do histórico)."""

    match_id: str
    queue_id: int
    game_start: datetime
    game_duration: int  # segundos
    remake: bool
    champion_id: int
    champion_name: str
    team_position: str
    win: bool
    kills: int
    deaths: int
    assists: int
    cs: int
    gold: int
    damage_to_champions: int
    vision_score: int
    kill_participation: float | None
    items: list[int]
    summoner_spells: list[int]

    @computed_field
    @property
    def kda(self) -> float:
        """(abates + assistências) / mortes; sem mortes, conta como 1 morte."""
        return round((self.kills + self.assists) / max(self.deaths, 1), 2)

    @computed_field
    @property
    def cs_per_minute(self) -> float:
        return round(self.cs / (self.game_duration / 60), 1) if self.game_duration else 0.0
