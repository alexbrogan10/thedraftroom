# Data Sources

## Summary

| Dataset | Source | Status |
|---|---|---|
| Teams (name, abbreviation, conference, division) | Public knowledge — NFL team organization | Real |
| Prospects, college statistics, combine results, draft projections | `scripts/generate_demo_data.py` | **Synthetic demo data** |
| Historical comparison players + NFL outcome labels | `scripts/generate_demo_data.py` | **Synthetic demo data** |
| Team rosters, team needs, team schemes | `scripts/generate_demo_data.py` | **Synthetic demo data** |

**Date accessed:** N/A — no external dataset was fetched or scraped for this
project. Team names/abbreviations/conferences/divisions are treated as
general public knowledge about NFL organizational structure, not sourced
from any single proprietary feed.

**License / usage restrictions:** None of the synthetic data in this repo is
subject to any third-party license, because none of it is real player data —
it is procedurally generated. No web scraping was performed to build this
dataset, per this project's data-source policy.

## Why synthetic demo data?

The Draft Room is a portfolio/demonstration project. Real NFL Scouting
Combine results, college production statistics, and consensus draft
projections are typically licensed data products; using them here without a
license would misrepresent this project's data rights. Instead,
`scripts/generate_demo_data.py` procedurally generates an **internally
consistent** dataset — every prospect has a hidden "talent" value that
coherently drives its generated statistics, testing numbers, and projected
draft position, so the analytics engine has something realistic to operate
on end-to-end.

**Every prospect, historical comparison player, roster player, statistic,
combine number, and team need in a stock deployment of this repo is
fictional.** This is stated in the app itself (see the Dashboard footer and
the "Data & Model" page) and should stay true of any deployment built from
this repo unless real, properly licensed data is connected.

## Connecting real data

The ingestion pipeline (`scripts/ingest.py`) reads from `data/raw/*.csv` in
a fixed schema (documented in each CSV's header row and in
`backend/app/models/`). To connect real, licensed data:

1. Replace the files in `data/raw/` with real data in the same column
   schema (see `scripts/generate_demo_data.py` for the exact columns each
   file expects).
2. Update this document with the real dataset's name, source, license, and
   date accessed.
3. Remove or update the "demo data" banners in the frontend
   (`frontend/src/components/Layout.tsx`, `frontend/src/pages/Methodology.tsx`).
4. Re-run `scripts/ingest.py` and `scripts/train_outcome_model.py`.

## Fields used, by file

- `teams.csv` — `id, name, abbreviation, conference, division`
- `prospects.csv` — `id, name, position, college, age, height_inches,
  weight_lbs, class_year, draft_year`
- `college_stats.csv` — `prospect_id, season, metric_name, metric_value`
  (position-specific metric names — see `docs/scoring_methodology.md`)
- `combine_results.csv` — `prospect_id, forty_yard_dash, vertical_jump,
  broad_jump, bench_press, three_cone, shuttle`
- `draft_projections.csv` — `prospect_id, source, projected_pick,
  projected_round`
- `historical_drafts.csv` — `id, player_name, position, college, draft_year,
  draft_round, draft_pick, age, height_inches, weight_lbs, forty_yard_dash,
  college_production_score`
- `nfl_outcomes.csv` — `historical_id, season, games, starts, started,
  productive_starter, long_term_contributor`
- `players.csv` / `rosters.csv` — current-roster players and their
  team/season/depth-chart assignment, used only for the Team Fit engine's
  roster-depth and average-age components
- `team_needs.csv` — `team_id, position, season, need_score`
- `team_schemes.csv` — `team_id, offensive_scheme, defensive_scheme`
