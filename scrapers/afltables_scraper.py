"""
AFL Tables scraper — scrapes per-season player stats and match results.

Player stats URL:  https://afltables.com/afl/stats/{year}.html
  - One row per player-game, all teams, full season.

Match results URL: https://afltables.com/afl/seas/{year}.html
  - Match-by-match scores with quarter breakdowns.
"""

import os
import time
import argparse
import requests
import pandas as pd
from bs4 import BeautifulSoup
from config import (
    AFLTABLES_STATS_URL,
    AFLTABLES_GAMES_URL,
    REQUEST_DELAY_SECONDS,
    REQUEST_TIMEOUT,
    RAW_DATA_DIR,
    START_YEAR,
    END_YEAR,
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _fetch_html(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


def scrape_player_stats(year: int) -> pd.DataFrame:
    """
    Scrapes the season player stats table from afltables.com.
    Returns a DataFrame with one row per player-game.
    """
    url = AFLTABLES_STATS_URL.format(year=year)
    soup = _fetch_html(url)

    # The stats page has a large table; first table with 'Player' header is what we want
    tables = soup.find_all("table")
    target = None
    for t in tables:
        headers = [th.get_text(strip=True) for th in t.find_all("th")]
        if "Player" in headers and "Kicks" in headers:
            target = t
            break

    if target is None:
        print(f"  WARNING: could not find stats table for {year}")
        return pd.DataFrame()

    rows = []
    for tr in target.find_all("tr")[1:]:  # skip header row
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if cells:
            rows.append(cells)

    # Column names as they appear on the site
    cols = [
        "player_name", "team", "year", "games_played", "opponent", "round",
        "result", "jersey_number", "kicks", "marks", "handballs", "disposals",
        "goals", "behinds", "hit_outs", "tackles", "rebounds", "inside_50s",
        "clearances", "clangers", "frees_for", "frees_against",
        "brownlow_votes", "contested_possessions", "uncontested_possessions",
        "contested_marks", "marks_inside_50", "one_percenters", "bounces",
        "goal_assists", "pct_game_played",
    ]

    df = pd.DataFrame(rows)
    # Trim or pad columns to match expected count
    if len(df.columns) >= len(cols):
        df = df.iloc[:, : len(cols)]
        df.columns = cols
    else:
        df.columns = cols[: len(df.columns)]

    df["year"] = year
    print(f"  {year}: {len(df)} player-game rows")
    return df


def scrape_match_results(year: int) -> pd.DataFrame:
    """
    Scrapes match results (scores by quarter) from the season page.
    Returns a DataFrame with one row per match.
    """
    url = AFLTABLES_GAMES_URL.format(year=year)
    soup = _fetch_html(url)

    matches = []
    # Match blocks are wrapped in <a name="roundX"> then table rows
    current_round = None
    for tag in soup.find_all(["a", "table"]):
        if tag.name == "a" and tag.get("name", "").startswith("r"):
            current_round = tag.get("name")
        if tag.name == "table":
            rows = tag.find_all("tr")
            if len(rows) < 2:
                continue
            cells_row1 = [td.get_text(strip=True) for td in rows[0].find_all("td")]
            cells_row2 = [td.get_text(strip=True) for td in rows[1].find_all("td")]
            # Expect: team, Q1.G.B, Q2.G.B, Q3.G.B, Q4.G.B, Total, Venue, Date, Attendance
            if len(cells_row1) >= 6 and len(cells_row2) >= 6:
                match = {
                    "year": year,
                    "round": current_round,
                    "home_team": cells_row1[0] if cells_row1 else None,
                    "away_team": cells_row2[0] if cells_row2 else None,
                    "home_score": cells_row1[-1] if cells_row1 else None,
                    "away_score": cells_row2[-1] if cells_row2 else None,
                }
                if len(cells_row1) > 6:
                    match["venue"] = cells_row1[-3]
                    match["date"] = cells_row1[-2]
                matches.append(match)

    df = pd.DataFrame(matches)
    print(f"  {year}: {len(df)} matches")
    return df


def run(start: int = START_YEAR, end: int = END_YEAR):
    os.makedirs(RAW_DATA_DIR, exist_ok=True)

    all_stats = []
    all_results = []

    for year in range(start, end + 1):
        print(f"\nScraping {year}...")
        try:
            stats = scrape_player_stats(year)
            if not stats.empty:
                all_stats.append(stats)
        except Exception as e:
            print(f"  ERROR scraping player stats {year}: {e}")

        time.sleep(REQUEST_DELAY_SECONDS)

        try:
            results = scrape_match_results(year)
            if not results.empty:
                all_results.append(results)
        except Exception as e:
            print(f"  ERROR scraping match results {year}: {e}")

        time.sleep(REQUEST_DELAY_SECONDS)

    if all_stats:
        pd.concat(all_stats, ignore_index=True).to_csv(
            f"{RAW_DATA_DIR}/afltables_player_stats.csv", index=False
        )
        print(f"\nPlayer stats saved ({sum(len(d) for d in all_stats)} total rows)")

    if all_results:
        pd.concat(all_results, ignore_index=True).to_csv(
            f"{RAW_DATA_DIR}/afltables_match_results.csv", index=False
        )
        print(f"Match results saved ({sum(len(d) for d in all_results)} total rows)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start_year", type=int, default=START_YEAR)
    parser.add_argument("--end_year", type=int, default=END_YEAR)
    args = parser.parse_args()
    run(args.start_year, args.end_year)
