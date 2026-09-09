from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    abbreviation: Mapped[str] = mapped_column(String(8), unique=True, nullable=False)
    conference: Mapped[str] = mapped_column(String(8), nullable=False)  # AFC / NFC
    division: Mapped[str] = mapped_column(String(16), nullable=False)  # North/South/East/West

    needs: Mapped[list["TeamNeed"]] = relationship(back_populates="team")
    roster_entries: Mapped[list["TeamRoster"]] = relationship(back_populates="team")
    scheme: Mapped["TeamScheme"] = relationship(back_populates="team", uselist=False)


class TeamScheme(Base):
    __tablename__ = "team_schemes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False, unique=True)
    offensive_scheme: Mapped[str] = mapped_column(String(64), nullable=False)
    defensive_scheme: Mapped[str] = mapped_column(String(64), nullable=False)

    team: Mapped["Team"] = relationship(back_populates="scheme")


class TeamNeed(Base):
    __tablename__ = "team_needs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    position: Mapped[str] = mapped_column(String(8), nullable=False)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    need_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-100, higher = greater need

    team: Mapped["Team"] = relationship(back_populates="needs")


class TeamRoster(Base):
    __tablename__ = "team_rosters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    depth_chart_position: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    team: Mapped["Team"] = relationship(back_populates="roster_entries")
    player: Mapped["Player"] = relationship(back_populates="roster_entries")
