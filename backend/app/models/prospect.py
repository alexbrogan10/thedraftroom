from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Prospect(Base):
    __tablename__ = "prospects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    position: Mapped[str] = mapped_column(String(8), nullable=False)
    college: Mapped[str] = mapped_column(String(128), nullable=False)
    age: Mapped[float] = mapped_column(Float, nullable=True)
    height_inches: Mapped[float] = mapped_column(Float, nullable=True)
    weight_lbs: Mapped[float] = mapped_column(Float, nullable=True)
    class_year: Mapped[str] = mapped_column(String(16), nullable=True)  # Fr/So/Jr/Sr/RS-Jr etc.
    draft_year: Mapped[int] = mapped_column(Integer, nullable=False)

    statistics: Mapped[list["ProspectStatistic"]] = relationship(
        back_populates="prospect", cascade="all, delete-orphan"
    )
    combine_result: Mapped["CombineResult"] = relationship(
        back_populates="prospect", uselist=False, cascade="all, delete-orphan"
    )
    projections: Mapped[list["DraftProjection"]] = relationship(
        back_populates="prospect", cascade="all, delete-orphan"
    )


class ProspectStatistic(Base):
    __tablename__ = "prospect_statistics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prospect_id: Mapped[int] = mapped_column(ForeignKey("prospects.id"), nullable=False)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    metric_name: Mapped[str] = mapped_column(String(64), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)

    prospect: Mapped["Prospect"] = relationship(back_populates="statistics")


class CombineResult(Base):
    __tablename__ = "combine_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prospect_id: Mapped[int] = mapped_column(
        ForeignKey("prospects.id"), nullable=False, unique=True
    )
    forty_yard_dash: Mapped[float] = mapped_column(Float, nullable=True)
    vertical_jump: Mapped[float] = mapped_column(Float, nullable=True)
    broad_jump: Mapped[float] = mapped_column(Float, nullable=True)
    bench_press: Mapped[float] = mapped_column(Float, nullable=True)
    three_cone: Mapped[float] = mapped_column(Float, nullable=True)
    shuttle: Mapped[float] = mapped_column(Float, nullable=True)

    prospect: Mapped["Prospect"] = relationship(back_populates="combine_result")


class DraftProjection(Base):
    __tablename__ = "draft_projections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prospect_id: Mapped[int] = mapped_column(ForeignKey("prospects.id"), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    projected_pick: Mapped[int] = mapped_column(Integer, nullable=True)
    projected_round: Mapped[int] = mapped_column(Integer, nullable=True)

    prospect: Mapped["Prospect"] = relationship(back_populates="projections")
