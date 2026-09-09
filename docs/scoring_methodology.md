# Scoring Methodology

This document specifies exactly how The Draft Room computes every score a
user sees. Every formula here is implemented in `backend/app/analytics/` —
there is no hidden or separate "real" calculation; this document and the
code are meant to always agree.

All scores are computed **within a prospect's own draft class and position
group** unless otherwise noted, using the prospects currently loaded into
the database. Nothing here is a claim of objective or universal truth — see
"Configurability" at the end of this document.

## 1. Draft Grade (0–100)

`app/analytics/scoring.py::compute_draft_grade`

Draft Grade is a weighted sum of six 0–100 sub-scores:

| Component | Default Weight | How it's computed |
|---|---|---|
| Production | 25% | Percentile rank within position peers on position-specific college statistics (see `PRODUCTION_METRIC_WEIGHTS` in `reference.py`), each metric weighted and combined |
| Athletic Profile | 15% | Percentile rank within position peers on position-weighted NFL Combine testing (`COMBINE_METRIC_WEIGHTS`) |
| Age / Experience | 10% | A curve favoring younger age, with a class-year bonus/penalty for proven experience vs. small sample size |
| Position Value | 15% | A static, configurable positional-scarcity assumption (`POSITION_VALUE`) — independent of any one prospect |
| NFL Projection | 25% | An MVP heuristic blend of Production, Athletic Profile, and (when available) how early the broader scouting community consensus expects the prospect drafted. This is **not yet** the trained ML model — see `docs/model_documentation.md` for the separate, leakage-safe outcome-probability model in `app/ml/` |
| Risk Adjustment | 10% | `100 − overall Risk Score` (see below) |

Weights are defined in `app/config.py::DraftGradeWeights`, are overridable
via `DRAFT_GRADE_*` environment variables (see `.env.example`), and are
always re-normalized to sum to 1.0 regardless of what's configured.

The full component breakdown (including per-metric percentile detail) is
returned by `GET /api/prospects/{id}/analytics` and rendered on every
prospect's profile page — the score is never shown without its breakdown.

## 2. Risk Score (0–100, higher = more risk)

`app/analytics/scoring.py::compute_risk_profile`

An unweighted average of five 0–100 factors:

- **Production Risk** — blends data completeness (how many of the
  position's expected statistical metrics are actually present) with the
  Production sub-score itself. Thin/incomplete college production data
  raises this factor.
- **Projection Risk** — derived from how much multiple scouting sources'
  projected picks disagree (their spread). A single source, or no sources,
  defaults to a moderate risk value rather than assuming certainty.
- **Competition Risk** — `100 − competition level`, where competition level
  is a conference-strength proxy (`CONFERENCE_STRENGTH` in `reference.py`).
- **Athletic Dependency Risk** — rises when Athletic Profile is
  substantially higher than Production, i.e., a "workout warrior" profile
  whose grade leans more on testing than proven on-field production.
- **Position Risk** — a static, documented per-position projection-volatility
  assumption (`POSITION_PROJECTION_RISK`), independent of any one prospect.

Overall Risk Score buckets into **LOWER RISK** (<34), **MODERATE RISK**
(34–66), or **HIGHER RISK** (≥67). The application never labels a prospect
a "bust" — see `tests/test_scoring.py::test_risk_profile_never_labels_a_player_a_bust`.

## 3. Team Fit Score (0–100)

`app/analytics/team_fit.py::compute_team_fit`

A weighted sum of six components, computed for one prospect against one
specific team:

| Component | Default Weight | Source |
|---|---|---|
| Current Need | 30% | That team's `team_needs` row for the prospect's position, current season |
| Future Need | 15% | Average of that team's `team_needs` rows for future seasons |
| Roster Depth | 15% | `100 − 25 × (players currently on the roster at this position)` — more existing depth lowers the score |
| Scheme Fit | 20% | A baseline of 75, adjusted by a documented scheme/position compatibility table (`SCHEME_FIT_BONUS`) against the team's offensive or defensive scheme |
| Development Timeline | 10% | Compares the prospect's age to the roster's average age at that position — favors young prospects behind an aging position group |
| Positional Value | 10% | The same static positional-value assumption used in Draft Grade |

Weights live in `app/analytics/team_fit.py::DEFAULT_TEAM_FIT_WEIGHTS`.

### Team-specific Big Board

A team's board (`GET /api/teams/{id}/draft-board`) is **not** simply
re-sorted by Team Fit — it's ranked by `0.5 × Draft Grade + 0.5 × Team Fit`,
so it stays a blend of talent and organizational context rather than need
alone. Each row is paired with a human-readable, template-generated reason
(`app/services/analytics_service.py::build_team_board_reason`) explaining
why the prospect moved up or down relative to the league-wide board.

## 4. Value / Hidden Value (0–100 + classification)

`app/analytics/value.py`

```
differential = expected_rank − analytical_rank
```

where `analytical_rank` is the prospect's rank on the league-wide Draft
Grade board (1..N within the loaded draft class) and `expected_rank` is the
average projected pick across all `draft_projections` sources for that
prospect. A **positive** differential means the analytical model ranks the
prospect ahead of where the broader scouting consensus expects them to be
drafted.

Classification bands (on the differential, in draft-pick-equivalent units):

| Differential | Classification |
|---|---|
| ≥ +25 | 🔥 Significant Value |
| +10 to +24 | 🟢 Potential Value |
| −9 to +9 | ⚪ Fair Value |
| −24 to −10 | 🟠 Potential Reach |
| ≤ −25 | 🔴 Significant Reach |

`value_score = clip(50 + differential, 0, 100)` — a bounded 0–100 display
score derived from the same differential.

**Important scale note:** analytical rank and expected pick are only
comparable when the loaded prospect pool spans roughly the same range as a
real draft class (~260 draft-eligible prospects). See
`scripts/generate_demo_data.py` for how the demo dataset is sized to satisfy
this.

The application never asserts a prospect is objectively undervalued — see
the standard explanation text in `value.py`.

## 5. Draft Capital Model

`app/analytics/draft_capital.py`

`traditional_value(pick)` is a smooth exponential curve (`1000 × e^(−0.0455 ×
(pick−1))`), calibrated so pick #1 = 1000 points and pick #32 ≈ 25% of pick
#1 — approximating the general *shape* of publicly known trade value charts.
It is **not** a reproduction of any team's or media outlet's proprietary
chart. "Traditional Value" is one configurable valuation model; "Historical
Player Value" and a fully custom model are roadmap items (Feature 14).

`availability_probability(pick_number, consensus_pick, spread)` is a
logistic function centered on the consensus projected pick, used by the
Trade-Up/Trade-Down analysis to estimate the odds a target prospect is still
on the board at a given pick.

## Configurability

Every table in this document that represents a modeling *assumption* rather
than an observed fact — position value, position projection risk, scheme
fit bonuses, conference strength — lives in
`backend/app/analytics/reference.py` in plain Python, specifically so it can
be found, audited, and changed without touching the scoring logic itself.
Draft Grade and Team Fit component weights are further exposed as
environment variables / constructor arguments. None of these are presented
as objectively correct.
