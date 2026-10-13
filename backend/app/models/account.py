from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Account(Base):
    __tablename__ = "accounts"

    puuid: Mapped[str] = mapped_column(String(100), primary_key=True)
    game_name: Mapped[str] = mapped_column(String(32))
    tag_line: Mapped[str] = mapped_column(String(10))
    region: Mapped[str] = mapped_column(String(8))
    profile_icon_id: Mapped[int] = mapped_column(Integer)
    summoner_level: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    ranked_entries: Mapped[list["RankedEntry"]] = relationship(
        back_populates="account", cascade="all, delete-orphan", lazy="selectin"
    )


# Busca por Riot ID sem diferenciar maiúsculas/minúsculas
Index(
    "ix_accounts_riot_id",
    func.lower(Account.game_name),
    func.lower(Account.tag_line),
    Account.region,
    unique=True,
)


class RankedEntry(Base):
    __tablename__ = "ranked_entries"

    puuid: Mapped[str] = mapped_column(
        ForeignKey("accounts.puuid", ondelete="CASCADE"), primary_key=True
    )
    queue_type: Mapped[str] = mapped_column(String(32), primary_key=True)
    tier: Mapped[str] = mapped_column(String(16))
    rank: Mapped[str] = mapped_column(String(4))
    league_points: Mapped[int] = mapped_column(Integer)
    wins: Mapped[int] = mapped_column(Integer)
    losses: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    account: Mapped[Account] = relationship(back_populates="ranked_entries")
