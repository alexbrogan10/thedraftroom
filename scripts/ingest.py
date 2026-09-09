"""
CSV -> PostgreSQL ingestion pipeline.

Steps: load -> validate -> clean -> standardize positions -> handle missing
values -> normalize measurements -> save processed CSVs -> load into
PostgreSQL. Does not fabricate values: rows with unusable required fields are
dropped and reported; optional metrics are simply left absent.

Run from the backend's virtualenv (needs the same dependencies as the API):
    python scripts/ingest.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(os.environ.get("BACKEND_DIR", ROOT / "backend"))
sys.path.insert(0, str(BACKEND_DIR))

from app.database.session import Base, SessionLocal, engine  # noqa: E402
from app.models import (  # noqa: E402
    CombineResult,
    DraftProjection,
    HistoricalDraftResult,
    NflOutcome,
    Player,
    Prospect,
    ProspectStatistic,
    Team,
    TeamNeed,
    TeamRoster,
    TeamScheme,
)

DATA_DIR = Path(os.environ.get("DATA_DIR", ROOT / "data"))
RAW = DATA_DIR / "raw"
PROCESSED = DATA_DIR / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)

VALID_POSITIONS = {"QB", "RB", "WR", "TE", "OT", "IOL", "EDGE", "IDL", "LB", "CB", "S"}

POSITION_ALIASES = {
    "OG": "IOL", "G": "IOL", "C": "IOL", "OL": "IOL", "T": "OT",
    "DE": "EDGE", "OLB": "EDGE", "DT": "IDL", "NT": "IDL", "DL": "IDL",
    "ILB": "LB", "MLB": "LB", "FS": "S", "SS": "S", "DB": "CB",
}


def standardize_position(pos: str) -> str:
    pos = str(pos).strip().upper()
    return POSITION_ALIASES.get(pos, pos)


def load_csv(name: str) -> pd.DataFrame:
    path = RAW / name
    if not path.exists():
        print(f"  [skip] {name} not found")
        return pd.DataFrame()
    return pd.read_csv(path)


def clean_teams(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["name", "abbreviation"]).drop_duplicates(subset=["abbreviation"])
    return df


def clean_prospects(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["name", "position", "college", "draft_year"]).copy()
    df["position"] = df["position"].apply(standardize_position)
    df = df[df["position"].isin(VALID_POSITIONS)]
    for col in ("age", "height_inches", "weight_lbs"):
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["draft_year"] = df["draft_year"].astype(int)
    return df


def run():
    print("== The Draft Room: ingestion pipeline ==")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("Loading + cleaning teams.csv ...")
        teams_df = clean_teams(load_csv("teams.csv"))
        teams_df.to_csv(PROCESSED / "teams.csv", index=False)
        team_id_map = {}
        for row in teams_df.itertuples():
            team = Team(
                name=row.name, abbreviation=row.abbreviation,
                conference=row.conference, division=row.division,
            )
            db.add(team)
            db.flush()
            team_id_map[row.id] = team.id
        print(f"  -> {len(teams_df)} teams")

        schemes_df = load_csv("team_schemes.csv")
        for row in schemes_df.itertuples():
            tid = team_id_map.get(row.team_id)
            if tid is None:
                continue
            db.add(TeamScheme(
                team_id=tid, offensive_scheme=row.offensive_scheme,
                defensive_scheme=row.defensive_scheme,
            ))
        print(f"  -> {len(schemes_df)} team schemes")

        print("Loading + cleaning prospects.csv ...")
        prospects_df = clean_prospects(load_csv("prospects.csv"))
        prospects_df.to_csv(PROCESSED / "prospects.csv", index=False)
        prospect_id_map = {}
        for row in prospects_df.itertuples():
            prospect = Prospect(
                name=row.name, position=row.position, college=row.college,
                age=None if pd.isna(row.age) else float(row.age),
                height_inches=None if pd.isna(row.height_inches) else float(row.height_inches),
                weight_lbs=None if pd.isna(row.weight_lbs) else float(row.weight_lbs),
                class_year=None if pd.isna(row.class_year) else row.class_year,
                draft_year=int(row.draft_year),
            )
            db.add(prospect)
            db.flush()
            prospect_id_map[row.id] = prospect.id
        print(f"  -> {len(prospects_df)} prospects")

        print("Loading college_stats.csv ...")
        stats_df = load_csv("college_stats.csv").dropna(subset=["prospect_id", "metric_name", "metric_value"])
        n = 0
        for row in stats_df.itertuples():
            pid = prospect_id_map.get(row.prospect_id)
            if pid is None:
                continue
            db.add(ProspectStatistic(
                prospect_id=pid, season=int(row.season),
                metric_name=row.metric_name, metric_value=float(row.metric_value),
            ))
            n += 1
        print(f"  -> {n} statistic rows")

        print("Loading combine_results.csv ...")
        combine_df = load_csv("combine_results.csv")
        n = 0
        for row in combine_df.itertuples():
            pid = prospect_id_map.get(row.prospect_id)
            if pid is None:
                continue
            d = row._asdict()
            db.add(CombineResult(
                prospect_id=pid,
                forty_yard_dash=d.get("forty_yard_dash") if pd.notna(d.get("forty_yard_dash")) else None,
                vertical_jump=d.get("vertical_jump") if pd.notna(d.get("vertical_jump")) else None,
                broad_jump=d.get("broad_jump") if pd.notna(d.get("broad_jump")) else None,
                bench_press=d.get("bench_press") if pd.notna(d.get("bench_press")) else None,
                three_cone=d.get("three_cone") if pd.notna(d.get("three_cone")) else None,
                shuttle=d.get("shuttle") if pd.notna(d.get("shuttle")) else None,
            ))
            n += 1
        print(f"  -> {n} combine result rows")

        print("Loading draft_projections.csv ...")
        proj_df = load_csv("draft_projections.csv")
        n = 0
        for row in proj_df.itertuples():
            pid = prospect_id_map.get(row.prospect_id)
            if pid is None:
                continue
            db.add(DraftProjection(
                prospect_id=pid, source=row.source,
                projected_pick=None if pd.isna(row.projected_pick) else int(row.projected_pick),
                projected_round=None if pd.isna(row.projected_round) else int(row.projected_round),
            ))
            n += 1
        print(f"  -> {n} draft projection rows")

        print("Loading historical_drafts.csv + nfl_outcomes.csv ...")
        hist_df = load_csv("historical_drafts.csv").dropna(subset=["player_name", "position"])
        hist_df["position"] = hist_df["position"].apply(standardize_position)
        outcomes_df = load_csv("nfl_outcomes.csv")
        outcomes_by_hist_id = (
            {int(r.historical_id): r for r in outcomes_df.itertuples()}
            if not outcomes_df.empty
            else {}
        )

        n_outcomes = 0
        for row in hist_df.itertuples():
            # Each historical comparison player also becomes a `Player` row so
            # its post-draft outcome can be recorded in `nfl_outcomes` without
            # ever feeding that outcome back into pre-draft feature data.
            player = Player(
                name=row.player_name, position=row.position,
                college=None if pd.isna(row.college) else row.college,
                draft_year=int(row.draft_year),
                age=None if pd.isna(row.age) else float(row.age),
                height_inches=None if pd.isna(row.height_inches) else float(row.height_inches),
                weight_lbs=None if pd.isna(row.weight_lbs) else float(row.weight_lbs),
            )
            db.add(player)
            db.flush()

            db.add(HistoricalDraftResult(
                player_name=row.player_name, position=row.position,
                college=None if pd.isna(row.college) else row.college,
                draft_year=int(row.draft_year),
                draft_round=None if pd.isna(row.draft_round) else int(row.draft_round),
                draft_pick=None if pd.isna(row.draft_pick) else int(row.draft_pick),
                age=None if pd.isna(row.age) else float(row.age),
                height_inches=None if pd.isna(row.height_inches) else float(row.height_inches),
                weight_lbs=None if pd.isna(row.weight_lbs) else float(row.weight_lbs),
                forty_yard_dash=None if pd.isna(row.forty_yard_dash) else float(row.forty_yard_dash),
                college_production_score=None if pd.isna(row.college_production_score) else float(row.college_production_score),
                player_id=player.id,
            ))

            outcome = outcomes_by_hist_id.get(int(row.id))
            if outcome is not None:
                db.add(NflOutcome(
                    player_id=player.id,
                    season=int(outcome.season),
                    games=int(outcome.games),
                    starts=int(outcome.starts),
                    performance_metrics={
                        "started": bool(outcome.started),
                        "productive_starter": bool(outcome.productive_starter),
                        "long_term_contributor": bool(outcome.long_term_contributor),
                    },
                ))
                n_outcomes += 1
        print(f"  -> {len(hist_df)} historical draft result rows, {n_outcomes} NFL outcome rows")

        print("Loading players.csv + rosters.csv ...")
        players_df = load_csv("players.csv").dropna(subset=["name", "position"])
        players_df["position"] = players_df["position"].apply(standardize_position)
        player_id_map = {}
        for row in players_df.itertuples():
            player = Player(
                name=row.name, position=row.position,
                college=None if pd.isna(row.college) else row.college,
                draft_year=None if pd.isna(row.draft_year) else int(row.draft_year),
                age=None if pd.isna(row.age) else float(row.age),
                height_inches=None if pd.isna(row.height_inches) else float(row.height_inches),
                weight_lbs=None if pd.isna(row.weight_lbs) else float(row.weight_lbs),
            )
            db.add(player)
            db.flush()
            player_id_map[row.id] = player.id
        print(f"  -> {len(players_df)} players")

        rosters_df = load_csv("rosters.csv")
        n = 0
        for row in rosters_df.itertuples():
            tid = team_id_map.get(row.team_id)
            plid = player_id_map.get(row.player_id)
            if tid is None or plid is None:
                continue
            db.add(TeamRoster(
                team_id=tid, player_id=plid, season=int(row.season),
                depth_chart_position=int(row.depth_chart_position),
            ))
            n += 1
        print(f"  -> {n} roster rows")

        print("Loading team_needs.csv ...")
        needs_df = load_csv("team_needs.csv")
        n = 0
        for row in needs_df.itertuples():
            tid = team_id_map.get(row.team_id)
            if tid is None:
                continue
            db.add(TeamNeed(
                team_id=tid, position=standardize_position(row.position),
                season=int(row.season), need_score=float(row.need_score),
            ))
            n += 1
        print(f"  -> {n} team need rows")

        db.commit()
        print("== Ingestion complete ==")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
