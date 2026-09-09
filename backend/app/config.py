"""
Application configuration.

Draft Grade component weights are intentionally configurable here rather than
hard-coded into the scoring logic, per the project's analytical philosophy:
there is no single objectively "correct" weighting of a prospect's evaluation.
Operators can override any weight via environment variables (see .env.example).
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class DraftGradeWeights(BaseSettings):
    """Weights must sum to 1.0. Adjust via env vars prefixed DRAFT_GRADE_."""

    production: float = 0.25
    athletic_profile: float = 0.15
    age_experience: float = 0.10
    position_value: float = 0.15
    nfl_projection: float = 0.25
    risk_adjustment: float = 0.10

    model_config = SettingsConfigDict(env_prefix="DRAFT_GRADE_", extra="ignore")

    def normalized(self) -> dict:
        total = (
            self.production
            + self.athletic_profile
            + self.age_experience
            + self.position_value
            + self.nfl_projection
            + self.risk_adjustment
        )
        if total <= 0:
            total = 1.0
        return {
            "production": self.production / total,
            "athletic_profile": self.athletic_profile / total,
            "age_experience": self.age_experience / total,
            "position_value": self.position_value / total,
            "nfl_projection": self.nfl_projection / total,
            "risk_adjustment": self.risk_adjustment / total,
        }


class Settings(BaseSettings):
    app_name: str = "The Draft Room API"
    environment: str = "development"
    database_url: str = (
        "postgresql+psycopg2://draftroom:draftroom@localhost:5432/draftroom"
    )
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    current_draft_year: int = 2026

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_draft_grade_weights() -> DraftGradeWeights:
    return DraftGradeWeights()
