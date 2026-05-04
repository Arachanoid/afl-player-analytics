"""
Cleans raw match results from both AFL Tables and Squiggle.
Input:  data/raw/afltables_match_results.csv
        data/raw/squiggle_games.csv
Output: data/cleaned/match_results.csv
"""

import json
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scrapers"))
from config import RAW_DATA_DIR, CLEANED_DATA_DIR

TEAM_MAP_PATH = os.path.join(os.path.dirname(__file__), "team_name_mapping.json")
VENUE_MAP_PATH = os.path.join(os.path.dirname(__file__), "venue_name_mapping.json")


def _parse_score(score_str) -> tuple[int | None, int | None]:
    """Parse 'G.B (Total)' or 'Total' format into total score."""
    if pd.isna(score_str):
        return None
    s = str(score_str).strip()
    # Format: "12.8 (80)" → extract the number in parens
    import re
    m = re.search(r"\((\d+)\)", s)
    if m:
        return int(m.group(1))
    # Format: plain integer
    if s.isdigit():
        return int(s)
    return None


def clean_afltables(df: pd.DataFrame, team_map: dict, venue_map: dict) -> pd.DataFrame:
    df = df.copy()
    df["home_team"] = df["home_team"].map(team_map).fillna(df["home_team"])
    df["away_team"] = df["away_team"].map(team_map).fillna(df["away_team"])
    if "venue" in df.columns:
        df["venue"] = df["venue"].map(venue_map).fillna(df["venue"])
    df["home_total_score"] = df["home_score"].apply(_parse_score)
    df["away_total_score"] = df["away_score"].apply(_parse_score)
    df = df.dropna(subset=["home_team", "away_team"])
    return df


def clean_squiggle(df: pd.DataFrame, team_map: dict, venue_map: dict) -> pd.DataFrame:
    df = df.copy()
    for col in ["hteam", "ateam"]:
        if col in df.columns:
            df[col] = df[col].map(team_map).fillna(df[col])
    if "venue" in df.columns:
        df["venue"] = df["venue"].map(venue_map).fillna(df["venue"])
    return df


def run():
    os.makedirs(CLEANED_DATA_DIR, exist_ok=True)

    with open(TEAM_MAP_PATH) as f:
        team_map = json.load(f)
    with open(VENUE_MAP_PATH) as f:
        venue_map = json.load(f)

    afl_path = f"{RAW_DATA_DIR}/afltables_match_results.csv"
    sq_path = f"{RAW_DATA_DIR}/squiggle_games.csv"

    results = []

    if os.path.exists(afl_path):
        df_afl = pd.read_csv(afl_path)
        print(f"AFL Tables match results: {len(df_afl)} rows")
        results.append(("afltables", clean_afltables(df_afl, team_map, venue_map)))

    if os.path.exists(sq_path):
        df_sq = pd.read_csv(sq_path)
        print(f"Squiggle games: {len(df_sq)} rows")
        results.append(("squiggle", clean_squiggle(df_sq, team_map, venue_map)))

    for source, df in results:
        out = f"{CLEANED_DATA_DIR}/match_results_{source}.csv"
        df.to_csv(out, index=False)
        print(f"  Saved {source} → {out} ({len(df)} rows)")


if __name__ == "__main__":
    run()
