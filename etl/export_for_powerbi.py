"""
Exports all star schema tables from SQLite to CSVs for Power BI.
Output folder: data/powerbi/

Load each CSV into Power BI via Get Data -> Text/CSV, then build
the relationships in Model view using the _key columns below:

  fact_player_match_stats
      player_key  -> dim_players.player_key
      team_key    -> dim_teams.team_key
      opponent_key-> dim_teams.team_key   (second relationship)
      season_key  -> dim_seasons.season_key

  fact_match_results
      home_team_key    -> dim_teams.team_key
      away_team_key    -> dim_teams.team_key
      winning_team_key -> dim_teams.team_key
      venue_key        -> dim_venues.venue_key
      season_key       -> dim_seasons.season_key
      date_key         -> dim_date.date_key
"""

import os
import sqlite3
import pandas as pd
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scrapers"))
from config import DATABASE_PATH

OUTPUT_DIR = os.path.join(os.path.dirname(DATABASE_PATH), "..", "powerbi")
OUTPUT_DIR = os.path.normpath(OUTPUT_DIR)

TABLES = [
    "dim_players",
    "dim_teams",
    "dim_venues",
    "dim_seasons",
    "dim_date",
    "fact_player_match_stats",
    "fact_match_results",
]


def run():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)

    for table in TABLES:
        df = pd.read_sql(f"SELECT * FROM {table}", conn)
        out = os.path.join(OUTPUT_DIR, f"{table}.csv")
        df.to_csv(out, index=False)
        print(f"  {table:<35} {len(df):>8,} rows  ->  {out}")

    conn.close()
    print(f"\nAll tables exported to {OUTPUT_DIR}")
    print("\nPower BI load order:")
    print("  1. Load all 7 CSVs via Get Data -> Text/CSV")
    print("  2. Model view: connect keys as listed in this file's docstring")
    print("  3. Mark dim_date as a Date Table (date column = full_date)")


if __name__ == "__main__":
    run()
