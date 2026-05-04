"""
Builds dimension tables (CSV) from cleaned data.
Outputs to data/cleaned/:  dim_players, dim_teams, dim_venues, dim_seasons, dim_date
"""

import os
import pandas as pd
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scrapers"))
from config import CLEANED_DATA_DIR, START_YEAR, END_YEAR


def build_dim_teams(player_df: pd.DataFrame, squiggle_teams_path: str) -> pd.DataFrame:
    teams = player_df["team"].dropna().unique().tolist()

    if os.path.exists(squiggle_teams_path):
        sq = pd.read_csv(squiggle_teams_path)
        # Squiggle teams have: id, name, abbrev, logo, ...
        sq_teams = sq["name"].dropna().unique().tolist() if "name" in sq.columns else []
        all_teams = sorted(set(teams + sq_teams))
    else:
        all_teams = sorted(set(teams))

    dim = pd.DataFrame({"team_name": all_teams})
    dim.index += 1
    dim.index.name = "team_key"
    dim = dim.reset_index()

    # Placeholder columns — to be enriched manually or via another source
    dim["abbreviation"] = None
    dim["state"] = None
    dim["home_ground"] = None
    return dim


def build_dim_venues(match_df: pd.DataFrame) -> pd.DataFrame:
    venues = match_df["venue"].dropna().unique().tolist() if "venue" in match_df.columns else []
    dim = pd.DataFrame({"venue_name": sorted(set(venues))})
    dim.index += 1
    dim.index.name = "venue_key"
    dim = dim.reset_index()
    dim["city"] = None
    dim["state"] = None
    dim["capacity"] = None
    dim["surface"] = None
    return dim


def build_dim_seasons(start: int = START_YEAR, end: int = END_YEAR) -> pd.DataFrame:
    rows = [{"year": y} for y in range(start, end + 1)]
    dim = pd.DataFrame(rows)
    dim.index += 1
    dim.index.name = "season_key"
    dim = dim.reset_index()
    dim["num_rounds"] = None
    dim["premiers"] = None
    return dim


def build_dim_date(start: int = START_YEAR, end: int = END_YEAR) -> pd.DataFrame:
    dates = pd.date_range(start=f"{start}-01-01", end=f"{end}-12-31", freq="D")
    dim = pd.DataFrame({
        "full_date": dates,
        "year": dates.year,
        "month": dates.month,
        "day": dates.day,
        "day_of_week": dates.day_name(),
        "is_weekend": dates.dayofweek >= 5,
    })
    # is_finals placeholder — will be updated after match data is loaded
    dim["is_finals"] = False
    dim.index += 1
    dim.index.name = "date_key"
    dim = dim.reset_index()
    return dim


def build_dim_players(player_df: pd.DataFrame) -> pd.DataFrame:
    players = (
        player_df[["player_name"]]
        .dropna()
        .drop_duplicates()
        .sort_values("player_name")
        .reset_index(drop=True)
    )
    players.index += 1
    players.index.name = "player_key"
    players = players.reset_index()
    # Bio fields — AFL Tables doesn't provide these; left as None for enrichment
    players["first_name"] = players["player_name"].str.split(",").str[-1].str.strip()
    players["last_name"] = players["player_name"].str.split(",").str[0].str.strip()
    players["dob"] = None
    players["height_cm"] = None
    players["weight_kg"] = None
    players["position"] = None
    players["draft_year"] = None
    players["draft_pick"] = None
    return players


def run():
    os.makedirs(CLEANED_DATA_DIR, exist_ok=True)

    player_path = f"{CLEANED_DATA_DIR}/player_stats.csv"
    match_path_afl = f"{CLEANED_DATA_DIR}/match_results_afltables.csv"
    squiggle_teams_path = f"{CLEANED_DATA_DIR}/../data/raw/squiggle_teams.csv"

    if not os.path.exists(player_path):
        print("ERROR: run clean_player_stats.py first")
        return

    print("Loading cleaned data...")
    player_df = pd.read_csv(player_path, low_memory=False)
    match_df = pd.read_csv(match_path_afl) if os.path.exists(match_path_afl) else pd.DataFrame()

    print("Building dim_players...")
    dim_players = build_dim_players(player_df)
    dim_players.to_csv(f"{CLEANED_DATA_DIR}/dim_players.csv", index=False)
    print(f"  {len(dim_players)} players")

    print("Building dim_teams...")
    dim_teams = build_dim_teams(player_df, squiggle_teams_path)
    dim_teams.to_csv(f"{CLEANED_DATA_DIR}/dim_teams.csv", index=False)
    print(f"  {len(dim_teams)} teams")

    print("Building dim_venues...")
    dim_venues = build_dim_venues(match_df)
    dim_venues.to_csv(f"{CLEANED_DATA_DIR}/dim_venues.csv", index=False)
    print(f"  {len(dim_venues)} venues")

    print("Building dim_seasons...")
    dim_seasons = build_dim_seasons()
    dim_seasons.to_csv(f"{CLEANED_DATA_DIR}/dim_seasons.csv", index=False)
    print(f"  {len(dim_seasons)} seasons")

    print("Building dim_date...")
    dim_date = build_dim_date()
    dim_date.to_csv(f"{CLEANED_DATA_DIR}/dim_date.csv", index=False)
    print(f"  {len(dim_date)} date rows")

    print("\nAll dimension tables saved to data/cleaned/")


if __name__ == "__main__":
    run()
