from sqlalchemy import JSON, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Player(Base):
    """
    Registry of historical/former NFL players used for roster context and
    outcome-based model training. Distinct from `Prospect`, which represents
    a player who has not yet been drafted.
    """

    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    position: Mapped[str] = mapped_column(String(8), nullable=False)
    college: Mapped[str] = mapped_column(String(128), nullable=True)
    draft_year: Mapped[int] = mapped_column(Integer, nullable=True)
    age: Mapped[float] = mapped_column(Float, nullable=True)
    height_inches: Mapped[float] = mapped_column(Float, nullable=True)
    weight_lbs: Mapped[float] = mapped_column(Float, nullable=True)

    roster_entries: Mapped[list["TeamRoster"]] = relationship(back_populates="player")
    outcomes: Mapped[list["NflOutcome"]] = relationship(back_populates="player")


class HistoricalDraftResult(Base):
    __tablename__ = "historical_draft_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_name: Mapped[str] = mapped_column(String(128), nullable=False)
    position: Mapped[str] = mapped_column(String(8), nullable=False)
    college: Mapped[str] = mapped_column(String(128), nullable=True)
    draft_year: Mapped[int] = mapped_column(Integer, nullable=False)
    draft_round: Mapped[int] = mapped_column(Integer, nullable=True)
    draft_pick: Mapped[int] = mapped_column(Integer, nullable=True)
    # Pre-draft measurables, used as ML/comparison-engine input features only.
    age: Mapped[float] = mapped_column(Float, nullable=True)
    height_inches: Mapped[float] = mapped_column(Float, nullable=True)
    weight_lbs: Mapped[float] = mapped_column(Float, nullable=True)
    forty_yard_dash: Mapped[float] = mapped_column(Float, nullable=True)
    college_production_score: Mapped[float] = mapped_column(Float, nullable=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=True)


class NflOutcome(Base):
    """
    Post-draft NFL performance record for a historical player. These rows are
    the LABEL SOURCE for outcome classification (e.g. "started" a season) and
    must never be joined into pre-draft feature sets used to predict outcomes,
    to avoid data leakage. See docs/model_documentation.md.
    """

    __tablename__ = "nfl_outcomes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    games: Mapped[int] = mapped_column(Integer, nullable=True)
    starts: Mapped[int] = mapped_column(Integer, nullable=True)
    performance_metrics: Mapped[dict] = mapped_column(JSON, nullable=True)

    player: Mapped["Player"] = relationship(back_populates="outcomes")
