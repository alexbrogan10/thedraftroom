# Methodology Overview

## Core philosophy

There is no single "correct" draft board. A prospect's value depends on
talent, projected NFL performance, positional value, risk, expected draft
position, and the needs of the specific organization evaluating that
player. The Draft Room is built around that premise rather than around
producing one master ranking:

- A **league-wide analytical board** (Draft Grade) ranks prospects
  independent of any team's needs.
- A **team-specific board** re-ranks the same prospects by blending Draft
  Grade with that team's roster context (need, depth, scheme, timeline).
- A **consensus view** (via `draft_projections`) represents what the broader
  scouting community expects, which the app compares against — but never
  treats as ground truth — in the Hidden Value Finder.

Every score the application shows is accompanied by an explanation of what
went into it. There is no "black box" number anywhere in the UI: the Draft
Grade breakdown, Risk factor breakdown, and Team Fit component breakdown are
all first-class, always-visible parts of the interface, not something the
user has to dig for.

## What each section answers

| Section | Question it answers |
|---|---|
| Dashboard | What does today's class look like for my team, at a glance? |
| Big Board | Who are the best prospects, league-wide vs. for my team specifically? |
| Prospect Explorer | Let me search/filter the full class by any criteria |
| Prospect Profile | Everything knowable about one prospect, and why the model grades them the way it does |
| Hidden Values | Where does the model disagree with consensus, and in which direction? |
| Risk Analysis | How much uncertainty surrounds this evaluation, and why? |
| Team Fit | How well does this prospect fit *my* organization specifically? |
| Draft Simulator | If I make this pick, what happens next — and what's the trade math? |
| Historical Comparisons | Who has looked like this before entering the league? |
| Data & Model | What is this built on, and how good (or not) is the ML actually? |

## Analytical rules this project follows throughout

1. **No fabricated statistics.** Everything not clearly real public
   knowledge (team names, conferences) is procedurally generated and
   labeled as demo data — see `docs/data_sources.md`.
2. **No claim of proprietary NFL data or professional-scouting equivalence.**
   The disclaimer in the README and in the app footer is not boilerplate;
   it reflects how this project should actually be read.
3. **Observed data, model output, and user assumptions are kept visually and
   semantically distinct.** Combine numbers and college statistics are
   observed inputs; Draft Grade/Risk/Team Fit/Value are model outputs;
   Draft Grade component weights are user-adjustable assumptions.
4. **No data leakage into outcome prediction.** See
   `docs/model_documentation.md` for the specific rule and how it's enforced
   in code.
5. **Every score is explainable.** See `docs/scoring_methodology.md` for the
   exact formula behind every number in the UI.
6. **Position-specific analysis.** Production and Athletic Profile scoring
   use different metrics per position group rather than one generic formula
   — see the tables in `backend/app/analytics/reference.py`.
7. **Confidence and risk are shown, not hidden.** A prospect is never
   presented as a sure thing, and is never called a "bust" — only
   lower/moderate/higher-risk.
8. **Historical performance does not guarantee future predictive accuracy.**
   Stated next to every ML metrics display.

For the exact math behind Draft Grade, Risk, Team Fit, and Value, see
`docs/scoring_methodology.md`. For the ML comparison/prediction models, see
`docs/model_documentation.md`. For what data this repo ships with, see
`docs/data_sources.md`.
