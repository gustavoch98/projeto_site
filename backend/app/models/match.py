from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Match(Base):
    """Uma partida. Partidas não mudam depois de terminadas: buscamos na Riot uma única vez."""

    __tablename__ = "matches"

    match_id: Mapped[str] = mapped_column(String(32), primary_key=True)  # ex.: BR1_3292532308
    platform: Mapped[str] = mapped_column(String(8))
    queue_id: Mapped[int] = mapped_column(Integer)  # 420 = Solo/Duo, 440 = Flex
    game_version: Mapped[str] = mapped_column(String(32))
    game_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    game_duration: Mapped[int] = mapped_column(Integer)  # segundos
    remake: Mapped[bool] = mapped_column(Boolean)  # partida encerrada nos primeiros minutos
    raw: Mapped[dict] = mapped_column(JSONB)  # resposta completa da Riot, para análises futuras
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MatchParticipant(Base):
    """Um jogador em uma partida: as colunas mais usadas nas análises, já extraídas do JSON.

    queue_id, game_start, game_duration e remake são cópias de Match (desnormalização):
    as análises por jogador ("horário", "tilt") filtram e ordenam por eles sem precisar de JOIN.
    """

    __tablename__ = "match_participants"

    match_id: Mapped[str] = mapped_column(
        ForeignKey("matches.match_id", ondelete="CASCADE"), primary_key=True
    )
    # Sem FK para accounts: a maioria dos participantes nunca foi buscada no site
    puuid: Mapped[str] = mapped_column(String(100), primary_key=True)

    queue_id: Mapped[int] = mapped_column(Integer)
    game_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    game_duration: Mapped[int] = mapped_column(Integer)
    remake: Mapped[bool] = mapped_column(Boolean)

    riot_id_game_name: Mapped[str] = mapped_column(String(32))
    riot_id_tagline: Mapped[str] = mapped_column(String(10))
    team_id: Mapped[int] = mapped_column(SmallInteger)  # 100 = azul, 200 = vermelho
    team_position: Mapped[str] = mapped_column(String(16))  # TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY
    champion_id: Mapped[int] = mapped_column(Integer)
    champion_name: Mapped[str] = mapped_column(String(32))
    win: Mapped[bool] = mapped_column(Boolean)

    kills: Mapped[int] = mapped_column(SmallInteger)
    deaths: Mapped[int] = mapped_column(SmallInteger)
    assists: Mapped[int] = mapped_column(SmallInteger)
    cs: Mapped[int] = mapped_column(SmallInteger)  # tropas + monstros neutros
    gold: Mapped[int] = mapped_column(Integer)
    damage_to_champions: Mapped[int] = mapped_column(Integer)
    vision_score: Mapped[int] = mapped_column(SmallInteger)
    kill_participation: Mapped[float | None] = mapped_column(Float)  # 0 a 1
    items: Mapped[list[int]] = mapped_column(ARRAY(Integer))  # 7 espaços (0 = vazio)
    summoner_spells: Mapped[list[int]] = mapped_column(ARRAY(Integer))


# Consulta principal: "as partidas deste jogador, da mais recente para a mais antiga"
Index(
    "ix_match_participants_puuid_inicio",
    MatchParticipant.puuid,
    MatchParticipant.game_start.desc(),
)
