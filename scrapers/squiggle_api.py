"""
Squiggle API client — pulls teams, venues, and match results.
Docs: https://api.squiggle.com.au/
"""

import os
import time
import requests
import pandas as pd
from config import SQUIGGLE_BASE_URL, SQUIGGLE_USER_AGENT, RAW_DATA_DIR, START_YEAR, END_YEAR


HEADERS = {"User-Agent": SQUIGGLE_USER_AGENT}


def _get(params: dict) -> dict:
    resp = requests.get(SQUIGGLE_BASE_URL, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_teams() -> pd.DataFrame:
    data = _get({"q": "teams"})
    df = pd.DataFrame(data["teams"])
    print(f"  Fetched {len(df)} teams")
    return df


def fetch_venues() -> pd.DataFrame:
    # Squiggle doesn't have a dedicated venues endpoint — extract from games
    data = _get({"q": "games", "year": END_YEAR})
    games = pd.DataFrame(data["games"])
    venues = (
        games[["venue"]]
        .dropna()
        .drop_duplicates()
        .rename(columns={"venue": "venue_name"})
        .reset_index(drop=True)
    )
    print(f"  Extracted {len(venues)} unique venues from {END_YEAR} games")
    return venues


def fetch_games(year: int) -> pd.DataFrame:
    data = _get({"q": "games", "year": year})
    df = pd.DataFrame(data["games"])
    print(f"  {year}: {len(df)} games")
    return df


def fetch_standings(year: int) -> pd.DataFrame:
    data = _get({"q": "standings", "year": year})
    df = pd.DataFrame(data["standings"])
    df["year"] = year
    return df


def run():
    os.makedirs(RAW_DATA_DIR, exist_ok=True)

    print("Fetching teams...")
    teams = fetch_teams()
    teams.to_csv(f"{RAW_DATA_DIR}/squiggle_teams.csv", index=False)

    print("Fetching venues...")
    venues = fetch_venues()
    venues.to_csv(f"{RAW_DATA_DIR}/squiggle_venues.csv", index=False)

    print("Fetching games by year...")
    all_games = []
    for year in range(START_YEAR, END_YEAR + 1):
        games = fetch_games(year)
        all_games.append(games)
        time.sleep(1)
    pd.concat(all_games, ignore_index=True).to_csv(
        f"{RAW_DATA_DIR}/squiggle_games.csv", index=False
    )

    print("Fetching standings by year...")
    all_standings = []
    for year in range(START_YEAR, END_YEAR + 1):
        standings = fetch_standings(year)
        all_standings.append(standings)
        time.sleep(1)
    pd.concat(all_standings, ignore_index=True).to_csv(
        f"{RAW_DATA_DIR}/squiggle_standings.csv", index=False
    )

    print("Done. Raw Squiggle data saved to data/raw/")


if __name__ == "__main__":
    run()
