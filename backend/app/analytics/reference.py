"""
Reference tables that encode analytical *assumptions* rather than observed
data: positional value curves, position-specific production/athletic testing
weights, and college conference strength used as a competition-level proxy.

These are inherently debatable modeling choices, not facts. They are kept in
one place, in plain Python, so they are easy to find, audit, and override —
see docs/scoring_methodology.md for the full rationale of each table.
"""

# Positional value: a 0-100 proxy for how much draft capital / positional
# scarcity typically applies to a position, independent of any one prospect.
# This is the "Position-adjusted Value" component of the Draft Grade and one
# input to Team Fit's "Positional Value" component.
POSITION_VALUE = {
    "QB": 100,
    "EDGE": 92,
    "OT": 90,
    "CB": 88,
    "WR": 85,
    "IDL": 78,
    "S": 72,
    "LB": 68,
    "TE": 65,
    "IOL": 60,
    "RB": 55,
}

POSITION_GROUP_LABELS = {
    "QB": "Quarterback",
    "RB": "Running Back",
    "WR": "Wide Receiver",
    "TE": "Tight End",
    "OT": "Offensive Tackle",
    "IOL": "Interior Offensive Line",
    "EDGE": "Edge Rusher",
    "IDL": "Interior Defensive Line",
    "LB": "Linebacker",
    "CB": "Cornerback",
    "S": "Safety",
}

# Position-specific college-production metrics and their relative weight
# toward the Production sub-score. Metric names correspond to `metric_name`
# rows ingested into `prospect_statistics`. Negative weight = higher value
# hurts the score (e.g. interceptions thrown).
PRODUCTION_METRIC_WEIGHTS = {
    "QB": {
        "completion_pct": 0.20,
        "yards_per_attempt": 0.20,
        "passing_tds": 0.20,
        "interceptions": -0.15,
        "sack_rate": -0.10,
        "rush_yards": 0.15,
    },
    "RB": {
        "rush_yards": 0.30,
        "yards_per_carry": 0.25,
        "explosive_run_rate": 0.15,
        "rush_tds": 0.15,
        "receiving_yards": 0.15,
    },
    "WR": {
        "receptions": 0.20,
        "receiving_yards": 0.30,
        "yards_per_reception": 0.20,
        "receiving_tds": 0.20,
        "target_share": 0.10,
    },
    "TE": {
        "receptions": 0.25,
        "receiving_yards": 0.35,
        "yards_per_reception": 0.15,
        "receiving_tds": 0.25,
    },
    "OT": {"games_played": 0.40, "starts": 0.60},
    "IOL": {"games_played": 0.40, "starts": 0.60},
    "EDGE": {
        "tackles": 0.15,
        "tackles_for_loss": 0.25,
        "sacks": 0.35,
        "pressures": 0.15,
        "forced_fumbles": 0.10,
    },
    "IDL": {
        "tackles": 0.25,
        "tackles_for_loss": 0.30,
        "sacks": 0.20,
        "pressures": 0.15,
        "forced_fumbles": 0.10,
    },
    "LB": {
        "tackles": 0.35,
        "tackles_for_loss": 0.20,
        "sacks": 0.15,
        "interceptions": 0.15,
        "pass_breakups": 0.15,
    },
    "CB": {
        "tackles": 0.15,
        "interceptions": 0.35,
        "pass_breakups": 0.35,
        "defensive_tds": 0.15,
    },
    "S": {
        "tackles": 0.25,
        "interceptions": 0.30,
        "pass_breakups": 0.30,
        "defensive_tds": 0.15,
    },
}

# Position-specific combine testing weights. Keys must match CombineResult
# fields. `lower_is_better` marks timed drills.
COMBINE_METRIC_WEIGHTS = {
    "QB": {"forty_yard_dash": 0.20, "vertical_jump": 0.15, "broad_jump": 0.15, "bench_press": 0.05, "three_cone": 0.20, "shuttle": 0.25},
    "RB": {"forty_yard_dash": 0.30, "vertical_jump": 0.15, "broad_jump": 0.15, "bench_press": 0.10, "three_cone": 0.15, "shuttle": 0.15},
    "WR": {"forty_yard_dash": 0.35, "vertical_jump": 0.20, "broad_jump": 0.15, "bench_press": 0.05, "three_cone": 0.15, "shuttle": 0.10},
    "TE": {"forty_yard_dash": 0.25, "vertical_jump": 0.15, "broad_jump": 0.15, "bench_press": 0.15, "three_cone": 0.15, "shuttle": 0.15},
    "OT": {"forty_yard_dash": 0.10, "vertical_jump": 0.05, "broad_jump": 0.10, "bench_press": 0.30, "three_cone": 0.25, "shuttle": 0.20},
    "IOL": {"forty_yard_dash": 0.10, "vertical_jump": 0.05, "broad_jump": 0.10, "bench_press": 0.30, "three_cone": 0.25, "shuttle": 0.20},
    "EDGE": {"forty_yard_dash": 0.25, "vertical_jump": 0.15, "broad_jump": 0.15, "bench_press": 0.15, "three_cone": 0.15, "shuttle": 0.15},
    "IDL": {"forty_yard_dash": 0.15, "vertical_jump": 0.10, "broad_jump": 0.10, "bench_press": 0.30, "three_cone": 0.15, "shuttle": 0.20},
    "LB": {"forty_yard_dash": 0.25, "vertical_jump": 0.15, "broad_jump": 0.10, "bench_press": 0.15, "three_cone": 0.15, "shuttle": 0.20},
    "CB": {"forty_yard_dash": 0.35, "vertical_jump": 0.20, "broad_jump": 0.15, "bench_press": 0.05, "three_cone": 0.15, "shuttle": 0.10},
    "S": {"forty_yard_dash": 0.30, "vertical_jump": 0.20, "broad_jump": 0.15, "bench_press": 0.05, "three_cone": 0.15, "shuttle": 0.15},
}

LOWER_IS_BETTER = {"forty_yard_dash", "three_cone", "shuttle"}

# Conference strength used as a proxy for competition level (0-100). This is
# a coarse, documented assumption — not a measure of any individual game.
CONFERENCE_STRENGTH = {
    "SEC": 95,
    "Big Ten": 93,
    "Big 12": 88,
    "ACC": 87,
    "Independent": 80,
    "American": 70,
    "Mountain West": 65,
    "Sun Belt": 62,
    "MAC": 58,
    "Conference USA": 58,
    "FCS": 45,
}

# College -> conference lookup for the demo dataset. Extend as new colleges
# are added to data/raw/prospects.csv.
COLLEGE_CONFERENCE = {
    "Georgia": "SEC", "Alabama": "SEC", "LSU": "SEC", "Texas A&M": "SEC",
    "Tennessee": "SEC", "Ole Miss": "SEC", "Auburn": "SEC", "Florida": "SEC",
    "Missouri": "SEC", "Texas": "SEC", "Oklahoma": "SEC", "Kentucky": "SEC",
    "Ohio State": "Big Ten", "Michigan": "Big Ten", "Penn State": "Big Ten",
    "Michigan State": "Big Ten", "Wisconsin": "Big Ten", "Iowa": "Big Ten",
    "Oregon": "Big Ten", "Washington": "Big Ten", "USC": "Big Ten",
    "Minnesota": "Big Ten", "Indiana": "Big Ten", "Illinois": "Big Ten",
    "Texas Tech": "Big 12", "Kansas State": "Big 12", "Iowa State": "Big 12",
    "Baylor": "Big 12", "TCU": "Big 12", "Oklahoma State": "Big 12",
    "Utah": "Big 12", "Arizona": "Big 12", "Arizona State": "Big 12",
    "Colorado": "Big 12", "BYU": "Big 12", "Kansas": "Big 12",
    "Clemson": "ACC", "Florida State": "ACC", "Miami": "ACC",
    "North Carolina": "ACC", "NC State": "ACC", "Louisville": "ACC",
    "Virginia Tech": "ACC", "Duke": "ACC", "Pittsburgh": "ACC",
    "SMU": "ACC", "California": "ACC", "Stanford": "ACC",
    "Georgia Tech": "ACC", "Boston College": "ACC", "Syracuse": "ACC",
    "Notre Dame": "Independent",
    "Memphis": "American", "Tulane": "American", "UTSA": "American",
    "Boise State": "Mountain West", "San Diego State": "Mountain West",
    "Air Force": "Mountain West",
    "App State": "Sun Belt", "Coastal Carolina": "Sun Belt",
    "Toledo": "MAC", "Ohio": "MAC",
    "Liberty": "Conference USA", "Western Kentucky": "Conference USA",
    "James Madison": "FCS", "North Dakota State": "FCS",
    "Montana": "FCS", "South Dakota State": "FCS",
}


# Offensive positions consult offensive_scheme, defensive positions consult
# defensive_scheme. Baseline fit is 75; bonuses below are added and capped at
# 100. A documented modeling assumption used by the Team Fit engine.
OFFENSIVE_POSITIONS = {"QB", "RB", "WR", "TE", "OT", "IOL"}
DEFENSIVE_POSITIONS = {"EDGE", "IDL", "LB", "CB", "S"}

SCHEME_FIT_BONUS = {
    ("West Coast Offense", "WR"): 10, ("West Coast Offense", "TE"): 8, ("West Coast Offense", "RB"): 5,
    ("Air Raid", "WR"): 15, ("Air Raid", "QB"): 10,
    ("Vertical Passing", "WR"): 12, ("Vertical Passing", "QB"): 6,
    ("Power Run", "RB"): 12, ("Power Run", "IOL"): 10, ("Power Run", "OT"): 8,
    ("Zone Run", "RB"): 8, ("Zone Run", "IOL"): 10, ("Zone Run", "OT"): 6,
    ("4-3 Zone", "EDGE"): 8, ("4-3 Zone", "IDL"): 8, ("4-3 Zone", "LB"): 6,
    ("3-4 Multiple", "EDGE"): 10, ("3-4 Multiple", "LB"): 10, ("3-4 Multiple", "IDL"): 6,
    ("Man Press", "CB"): 15, ("Man Press", "S"): 5,
    ("Cover 3 Zone", "S"): 10, ("Cover 3 Zone", "CB"): 8,
}


def compute_scheme_fit(position: str, offensive_scheme: str, defensive_scheme: str) -> float:
    scheme = offensive_scheme if position in OFFENSIVE_POSITIONS else defensive_scheme
    bonus = SCHEME_FIT_BONUS.get((scheme, position), 0)
    return float(min(100, 75 + bonus))


def get_conference(college: str) -> str:
    return COLLEGE_CONFERENCE.get(college, "American")


def get_competition_level(college: str) -> float:
    conference = get_conference(college)
    return CONFERENCE_STRENGTH.get(conference, 65)
