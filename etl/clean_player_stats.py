"""
Cleans raw AFL Tables player stats CSV.
Input:  data/raw/afltables_player_stats.csv
Output: data/cleaned/player_stats.csv
"""

import json
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scrapers"))
from config import RAW_DATA_DIR, CLEANED_DATA_DIR

TEAM_MAP_PATH = os.path.join(os.path.dirname(__file__), "team_name_mapping.json")

NUMERIC_COLS = [
    "kicks", "marks", "handballs", "disposals", "goals", "behinds",
    "hit_outs", "tackles", "rebounds", "inside_50s", "clearances",
    "clangers", "frees_for", "frees_against", "brownlow_votes",
    "contested_possessions", "uncontested_possessions", "contested_marks",
    "marks_inside_50", "one_percenters", "bounces", "goal_assists",
    "pct_game_played",
]


def clean(df: pd.DataFrame, team_map: dict) -> pd.DataFrame:
    df = df.copy()

    # Standardise team names
    df["team"] = df["team"].map(team_map).fillna(df["team"])

    # Strip whitespace from player names
    df["player_name"] = df["player_name"].str.strip()

    # Coerce numeric columns
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # year as int
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    # Drop rows missing player name or team
    df = df.dropna(subset=["player_name", "team"])

    # Round: strip leading 'R' if present, coerce to int
    if "round" in df.columns:
        df["round"] = df["round"].astype(str).str.extract(r"(\d+)")[0]
        df["round"] = pd.to_numeric(df["round"], errors="coerce").astype("Int64")

    return df.reset_index(drop=True)


def run():
    os.makedirs(CLEANED_DATA_DIR, exist_ok=True)

    with open(TEAM_MAP_PATH) as f:
        team_map = json.load(f)

    path = f"{RAW_DATA_DIR}/afltables_player_stats.csv"
    print(f"Reading {path}")
    df = pd.read_csv(path, low_memory=False)
    print(f"  Raw rows: {len(df)}")

    df = clean(df, team_map)
    print(f"  Cleaned rows: {len(df)}")

    out = f"{CLEANED_DATA_DIR}/player_stats.csv"
    df.to_csv(out, index=False)
    print(f"  Saved to {out}")


if __name__ == "__main__":
    run()
