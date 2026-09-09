from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import draft, model, prospects, teams
from app.config import get_settings
from app.database.session import Base, engine

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Idempotent — ensures the schema exists even before scripts/ingest.py
    # has been run, so the API doesn't 500 on a fresh database.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    description=(
        "The Draft Room — an independent NFL draft analytics and scouting "
        "platform. Not affiliated with the NFL. See /docs for the API and "
        "the project README for the full disclaimer."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prospects.router)
app.include_router(teams.router)
app.include_router(draft.router)
app.include_router(model.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "environment": settings.environment}
