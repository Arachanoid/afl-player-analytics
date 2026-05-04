"""
Cleans raw AFL Tables player stats CSV and enriches with Squiggle match_id.
Input:  data/raw/afltables_player_stats.csv
        data/raw/squiggle_games.csv
Output: data/cleaned/player_stats.csv
"""

import json
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scrapers"))
from config import RAW_DATA_DIR, CLEANED_DATA_DIR

TEAM_MAP_PATH = os.path.join(os.path.dirname(__file__), "team_name_mapping.json")
VENUE_MAP_PATH = os.path.join(os.path.dirname(__file__), "venue_name_mapping.json")

NUMERIC_COLS = [
    "kicks", "marks", "handballs", "disposals", "goals", "behinds",
    "hit_outs", "tackles", "rebounds", "inside_50s", "clearances",
    "clangers", "frees_for", "frees_against", "brownlow_votes",
    "contested_possessions", "uncontested_possessions", "contested_marks",
    "marks_inside_50", "one_percenters", "bounces", "goal_assists",
    "pct_game_played",
]

# AFL Tables finals abbreviation -> week offset from last regular round
FINALS_OFFSET = {"EF": 1, "QF": 1, "SF": 2, "PF": 3, "GF": 4}


def _build_round_lookup(sq: pd.DataFrame) -> dict:
    """
    Returns {(year, round_int): match_id, ...} from Squiggle games,
    keyed by both hteam and ateam so we can look up from either side.
    Result: {(year, round_int, team_name): match_id}
    """
    lookup = {}
    for _, row in sq.iterrows():
        key_home = (row["year"], row["round"], row["hteam"])
        key_away = (row["year"], row["round"], row["ateam"])
        lookup[key_home] = row["id"]
        lookup[key_away] = row["id"]
    return lookup


def _to_round_int(round_str, year: int, max_reg_rounds: dict) -> int | None:
    """Convert AFL Tables round string (R1, QF, SF, etc.) to Squiggle integer."""
    s = str(round_str).strip()
    if s.startswith("R") and s[1:].isdigit():
        return int(s[1:])
    if s in FINALS_OFFSET:
        base = max_reg_rounds.get(year, 23)
        return base + FINALS_OFFSET[s]
    return None


def enrich_with_match_id(df: pd.DataFrame, team_map: dict, venue_map: dict) -> pd.DataFrame:
    """Join player_stats against Squiggle games to add match_id column."""
    sq_path = f"{RAW_DATA_DIR}/squiggle_games.csv"
    if not os.path.exists(sq_path):
        print("  WARNING: squiggle_games.csv not found — match_id will be NULL")
        df["match_id"] = None
        return df

    sq = pd.read_csv(sq_path)

    # Apply same team name mapping so names match
    for col in ["hteam", "ateam"]:
        sq[col] = sq[col].map(team_map).fillna(sq[col])

    # Max regular round per year (is_final == 0)
    max_reg_rounds = sq[sq["is_final"] == 0].groupby("year")["round"].max().to_dict()

    # Build (year, round_int, team) -> match_id lookup
    round_lookup = _build_round_lookup(sq)

    # Convert player_stats round strings to integers
    df["_round_int"] = df.apply(
        lambda r: _to_round_int(r["round"], int(r["year"]), max_reg_rounds), axis=1
    )

    # Look up match_id
    df["match_id"] = df.apply(
        lambda r: round_lookup.get((int(r["year"]), r["_round_int"], r["team"]))
        if pd.notna(r["_round_int"]) else None,
        axis=1
    )

    df = df.drop(columns=["_round_int"])

    matched = df["match_id"].notna().sum()
    total = len(df)
    print(f"  match_id enrichment: {matched:,}/{total:,} rows matched ({matched/total*100:.1f}%)")

    return df


def clean(df: pd.DataFrame, team_map: dict) -> pd.DataFrame:
    df = df.copy()

    df["team"] = df["team"].map(team_map).fillna(df["team"])
    df["player_name"] = df["player_name"].str.strip()

    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["player_name", "team"])

    # Keep original round string for finals lookup, then convert to int after enrichment
    return df.reset_index(drop=True)


def run():
    os.makedirs(CLEANED_DATA_DIR, exist_ok=True)

    with open(TEAM_MAP_PATH) as f:
        team_map = json.load(f)
    with open(VENUE_MAP_PATH) as f:
        venue_map = json.load(f)

    path = f"{RAW_DATA_DIR}/afltables_player_stats.csv"
    print(f"Reading {path}")
    df = pd.read_csv(path, low_memory=False)
    print(f"  Raw rows: {len(df)}")

    df = clean(df, team_map)
    print(f"  Cleaned rows: {len(df)}")

    print("  Enriching with match_id from Squiggle...")
    df = enrich_with_match_id(df, team_map, venue_map)

    # Now convert round to integer (after enrichment used the string form)
    if "round" in df.columns:
        df["round"] = df["round"].astype(str).str.extract(r"(\d+)")[0]
        df["round"] = pd.to_numeric(df["round"], errors="coerce").astype("Int64")

    # Place match_id as second column for visibility
    cols = df.columns.tolist()
    cols.insert(0, cols.pop(cols.index("match_id")))
    df = df[cols]

    out = f"{CLEANED_DATA_DIR}/player_stats.csv"
    df.to_csv(out, index=False)
    print(f"  Saved to {out}")


if __name__ == "__main__":
    run()
