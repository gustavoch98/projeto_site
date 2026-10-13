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
    # Última vez que buscamos as partidas na Riot (None = nunca)
    matches_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Quando o histórico longo (para o painel de insights) foi completado (None = ainda não)
    history_backfilled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

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

# Autocomplete: busca por prefixo do nome (LIKE 'hazz%'). Com a collation en_US do banco,
# o índice só serve para LIKE se usar text_pattern_ops (compara byte a byte).
Index(
    "ix_accounts_nome_prefixo",
    Account.region,
    func.lower(Account.game_name).label("nome_minusculo"),
    postgresql_ops={"nome_minusculo": "text_pattern_ops"},
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


class RankedHistory(Base):
    """Uma "foto" do elo em uma fila, gravada sempre que algo muda (PDL, vitórias, derrotas).

    Permite desenhar a evolução do PDL ao longo do tempo. Só existe a partir do momento em que
    começamos a gravar, por isso vale coletar desde cedo.
    """

    __tablename__ = "ranked_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    puuid: Mapped[str] = mapped_column(ForeignKey("accounts.puuid", ondelete="CASCADE"))
    queue_type: Mapped[str] = mapped_column(String(32))
    tier: Mapped[str] = mapped_column(String(16))
    rank: Mapped[str] = mapped_column(String(4))
    league_points: Mapped[int] = mapped_column(Integer)
    wins: Mapped[int] = mapped_column(Integer)
    losses: Mapped[int] = mapped_column(Integer)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


Index(
    "ix_ranked_history_puuid_fila_data",
    RankedHistory.puuid,
    RankedHistory.queue_type,
    RankedHistory.recorded_at,
)

