"""
AFL Tables scraper — per-game player stats via team Game-by-Game pages.

Strategy:
  1. Fetch the season stats index page to get each team's GBG link.
  2. For each team's GBG page, parse 23 stat tables (pivot: player × round).
  3. Melt each stat to long format, join all stats into one player-game DataFrame.
  4. Append opponent abbreviation from the header row.
"""

import os
import re
import time
import argparse
import requests
import pandas as pd
from bs4 import BeautifulSoup
from config import (
    AFLTABLES_STATS_URL,
    REQUEST_DELAY_SECONDS,
    REQUEST_TIMEOUT,
    RAW_DATA_DIR,
    START_YEAR,
    END_YEAR,
)

AFLTABLES_BASE = "https://afltables.com/afl/stats/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# Maps stat table title → clean column name
STAT_MAP = {
    "Disposals":               "disposals",
    "Kicks":                   "kicks",
    "Marks":                   "marks",
    "Handballs":               "handballs",
    "Goals":                   "goals",
    "Behinds":                 "behinds",
    "Hit Outs":                "hit_outs",
    "Tackles":                 "tackles",
    "Rebounds":                "rebounds",
    "Inside 50s":              "inside_50s",
    "Clearances":              "clearances",
    "Clangers":                "clangers",
    "Frees":                   "frees_for",
    "Frees Against":           "frees_against",
    "Brownlow Votes":          "brownlow_votes",
    "Contested Possessions":   "contested_possessions",
    "Uncontested Possessions": "uncontested_possessions",
    "Contested Marks":         "contested_marks",
    "Marks Inside 50":         "marks_inside_50",
    "One Percenters":          "one_percenters",
    "Bounces":                 "bounces",
    "Goal Assists":            "goal_assists",
    "% Played":                "pct_game_played",
    "Subs":                    "subs",
}


def _fetch(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


def get_team_gbg_links(year: int) -> dict[str, str]:
    """Returns {team_name: full_gbg_url} for every team in the season."""
    soup = _fetch(AFLTABLES_STATS_URL.format(year=year))
    teams = {}
    for t in soup.find_all("table"):
        th = t.find("th")
        if not th:
            continue
        link = th.find("a", href=lambda h: h and "gbg" in h)
        if not link:
            continue
        team_name = th.get_text(strip=True).split("[")[0].strip()
        gbg_url = AFLTABLES_BASE + link["href"]
        teams[team_name] = gbg_url
    return teams


def parse_gbg_page(gbg_url: str, team_name: str, year: int) -> pd.DataFrame:
    """
    Parses one team's GBG page.
    Returns a DataFrame with columns: player_name, team, year, round, opponent, <all stats>
    """
    soup = _fetch(gbg_url)
    tables = soup.find_all("table")
    if not tables:
        return pd.DataFrame()

    # Build round labels and opponent mapping from the first table's th elements.
    # TH structure: [stat_name, 'Player', R2, R3, ..., Rn, 'Tot', <totals...>,
    #                'Opponent', opp1, opp2, ..., oppN, '']
    first_table = tables[0]
    all_ths = [th.get_text(strip=True) for th in first_table.find_all("th")]

    round_labels = []
    opponents_raw = []
    in_rounds = False
    in_opponents = False
    for label in all_ths:
        if label == "Player":
            in_rounds = True
            continue
        if in_rounds:
            if label in ("Tot", "Totals", ""):
                in_rounds = False
            elif re.match(r"^R\d+$|^EF$|^QF$|^SF$|^PF$|^GF$", label):
                round_labels.append(label)
        if label == "Opponent":
            in_opponents = True
            continue
        if in_opponents:
            if label == "":
                in_opponents = False
            else:
                opponents_raw.append(label)

    round_to_opp = {r: o for r, o in zip(round_labels, opponents_raw)}

    # Parse each stat table
    stat_dfs = {}
    for tbl in tables:
        ths = tbl.find_all("th")
        if not ths:
            continue
        stat_label = ths[0].get_text(strip=True)
        col_name = STAT_MAP.get(stat_label)
        if col_name is None:
            continue

        tbl_rows = tbl.find_all("tr")
        player_data = {}
        for row in tbl_rows:
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if not cells or cells[0] in ("Opponent", "Totals", ""):
                continue
            player = cells[0]
            values = cells[1:]
            # values align with round_labels; remaining cells are totals — trim
            game_values = values[: len(round_labels)]
            player_data[player] = game_values

        if player_data:
            stat_dfs[col_name] = player_data

    if not stat_dfs:
        return pd.DataFrame()

    # Build long-format DataFrame: one row per player-round
    records = []
    all_players = list(next(iter(stat_dfs.values())).keys())
    for player in all_players:
        for i, round_label in enumerate(round_labels):
            row = {
                "player_name": player,
                "team": team_name,
                "year": year,
                "round": round_label,
                "opponent": round_to_opp.get(round_label, ""),
            }
            for col_name, player_data in stat_dfs.items():
                val = player_data.get(player, [""] * len(round_labels))
                raw = val[i] if i < len(val) else ""
                # "-" means the player played but recorded zero for this stat
                if raw == "-":
                    row[col_name] = 0
                elif raw == "" or raw is None:
                    row[col_name] = None
                else:
                    try:
                        row[col_name] = float(raw)
                    except ValueError:
                        row[col_name] = raw
            # Skip rows where player has no stats at all (didn't play)
            stat_cols = [c for c in row if c not in ("player_name", "team", "year", "round", "opponent")]
            if all(row[c] is None for c in stat_cols):
                continue
            records.append(row)

    return pd.DataFrame(records)


def scrape_year(year: int) -> pd.DataFrame:
    print(f"\n  Getting team links for {year}...")
    teams = get_team_gbg_links(year)
    print(f"  Found {len(teams)} teams")

    all_frames = []
    for team_name, gbg_url in teams.items():
        print(f"    {team_name}...", end=" ", flush=True)
        try:
            df = parse_gbg_page(gbg_url, team_name, year)
            print(f"{len(df)} rows")
            if not df.empty:
                all_frames.append(df)
        except Exception as e:
            print(f"ERROR: {e}")
        time.sleep(REQUEST_DELAY_SECONDS)

    if not all_frames:
        return pd.DataFrame()

    combined = pd.concat(all_frames, ignore_index=True)
    print(f"  {year} total: {len(combined)} player-game rows")
    return combined


def run(start: int = START_YEAR, end: int = END_YEAR):
    os.makedirs(RAW_DATA_DIR, exist_ok=True)

    all_years = []
    for year in range(start, end + 1):
        print(f"\nScraping {year}...")
        df = scrape_year(year)
        if not df.empty:
            all_years.append(df)
        time.sleep(REQUEST_DELAY_SECONDS)

    if all_years:
        final = pd.concat(all_years, ignore_index=True)
        out = os.path.join(RAW_DATA_DIR, "afltables_player_stats.csv")
        final.to_csv(out, index=False)
        print(f"\nSaved {len(final):,} total rows -> {out}")
    else:
        print("No data scraped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start_year", type=int, default=START_YEAR)
    parser.add_argument("--end_year", type=int, default=END_YEAR)
    args = parser.parse_args()
    run(args.start_year, args.end_year)
