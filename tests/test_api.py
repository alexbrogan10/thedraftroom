import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base, get_db
from app.main import app
from app.models.prospect import CombineResult, DraftProjection, Prospect, ProspectStatistic
from app.models.team import Team, TeamNeed, TeamScheme


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    team = Team(name="Test Team", abbreviation="TST", conference="AFC", division="North")
    db.add(team)
    db.flush()
    db.add(TeamScheme(team_id=team.id, offensive_scheme="Zone Run", defensive_scheme="4-3 Zone"))
    db.add(TeamNeed(team_id=team.id, position="CB", season=2026, need_score=75.0))

    for i in range(3):
        prospect = Prospect(
            name=f"Prospect {i}", position="CB", college="Test State",
            age=21.0 + i, height_inches=71, weight_lbs=190, class_year="Jr", draft_year=2026,
        )
        db.add(prospect)
        db.flush()
        db.add(ProspectStatistic(prospect_id=prospect.id, season=2025, metric_name="interceptions", metric_value=3 + i))
        db.add(ProspectStatistic(prospect_id=prospect.id, season=2025, metric_name="pass_breakups", metric_value=10 + i))
        db.add(ProspectStatistic(prospect_id=prospect.id, season=2025, metric_name="tackles", metric_value=40 + i))
        db.add(CombineResult(prospect_id=prospect.id, forty_yard_dash=4.4 + i * 0.02))
        db.add(DraftProjection(prospect_id=prospect.id, source="Test Source", projected_pick=10 + i * 20))
    db.commit()
    db.close()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_list_teams(client):
    resp = client.get("/api/teams")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["abbreviation"] == "TST"


def test_list_prospects_and_grade_ordering(client):
    resp = client.get("/api/prospects", params={"draft_year": 2026})
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 3
    grades = [r["draft_grade"] for r in rows]
    assert grades == sorted(grades, reverse=True)
    for r in rows:
        assert 0 <= r["draft_grade"] <= 100
        assert r["risk_level"] in {"LOWER RISK", "MODERATE RISK", "HIGHER RISK"}


def test_prospect_detail_and_analytics(client):
    prospect_id = client.get("/api/prospects", params={"draft_year": 2026}).json()[0]["id"]

    detail = client.get(f"/api/prospects/{prospect_id}")
    assert detail.status_code == 200
    assert detail.json()["position"] == "CB"

    analytics = client.get(f"/api/prospects/{prospect_id}/analytics")
    assert analytics.status_code == 200
    body = analytics.json()
    assert "draft_grade" in body and "risk" in body and "value" in body


def test_prospect_not_found(client):
    resp = client.get("/api/prospects/9999")
    assert resp.status_code == 404


def test_team_draft_board_reorders_and_explains(client):
    team_id = client.get("/api/teams").json()[0]["id"]
    resp = client.get(f"/api/teams/{team_id}/draft-board", params={"draft_year": 2026})
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 3
    for r in rows:
        assert r["team_fit"] is not None
        assert r["reason"]


def test_draft_recommend_and_simulate(client):
    team_id = client.get("/api/teams").json()[0]["id"]

    rec = client.post("/api/draft/recommend", json={
        "team_id": team_id, "draft_year": 2026, "pick_number": 12, "excluded_prospect_ids": [],
    })
    assert rec.status_code == 200
    body = rec.json()
    assert body["recommended"]["is_primary"] is True
    assert body["reasoning"]

    sim = client.post("/api/draft/simulate", json={
        "team_id": team_id, "draft_year": 2026, "pick_number": 12, "drafted_prospect_ids": [],
    })
    assert sim.status_code == 200
    assert sim.json()["remaining_prospect_count"] == 3
