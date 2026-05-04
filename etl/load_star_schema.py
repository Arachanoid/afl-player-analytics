"""
Loads cleaned CSVs into a SQLite star schema database.
Run after: clean_player_stats, clean_match_results, build_dimensions
"""

import os
import sqlite3
import pandas as pd
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scrapers"))
from config import CLEANED_DATA_DIR, DATABASE_PATH


def load_table(conn: sqlite3.Connection, csv_path: str, table_name: str):
    if not os.path.exists(csv_path):
        print(f"  SKIP {table_name} — file not found: {csv_path}")
        return
    df = pd.read_csv(csv_path, low_memory=False)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    print(f"  Loaded {table_name}: {len(df)} rows")


def build_fact_player_match_stats(conn: sqlite3.Connection):
    """
    Joins player stats with dimension surrogate keys to build the fact table.
    Note: venue_key and date_key are NULL here — the GBG scraper gives round+opponent
    but not date/venue. These can be enriched later by joining with fact_match_results.
    """
    query = """
    CREATE TABLE IF NOT EXISTS fact_player_match_stats AS
    SELECT
        ps.rowid          AS stat_key,
        dp.player_key,
        dt.team_key,
        ot.team_key       AS opponent_key,
        ds.season_key,
        ps.round,
        ps.kicks,
        ps.marks,
        ps.handballs,
        ps.disposals,
        ps.goals,
        ps.behinds,
        ps.hit_outs,
        ps.tackles,
        ps.rebounds,
        ps.inside_50s,
        ps.clearances,
        ps.clangers,
        ps.frees_for,
        ps.frees_against,
        ps.brownlow_votes,
        ps.contested_possessions,
        ps.uncontested_possessions,
        ps.contested_marks,
        ps.marks_inside_50,
        ps.one_percenters,
        ps.bounces,
        ps.goal_assists,
        ps.pct_game_played,
        ps.subs
    FROM player_stats ps
    LEFT JOIN dim_players dp ON ps.player_name = dp.player_name
    LEFT JOIN dim_teams   dt ON ps.team        = dt.team_name
    LEFT JOIN dim_teams   ot ON ps.opponent    = ot.team_name
    LEFT JOIN dim_seasons ds ON ps.year        = ds.year
    """
    conn.execute("DROP TABLE IF EXISTS fact_player_match_stats")
    conn.execute(query)
    count = conn.execute("SELECT COUNT(*) FROM fact_player_match_stats").fetchone()[0]
    print(f"  Built fact_player_match_stats: {count} rows")


def build_fact_match_results(conn: sqlite3.Connection):
    """Builds match results fact table from Squiggle data (richer than AFL Tables scrape)."""
    # Try Squiggle first (has scores, attendance, etc.), fallback to AFL Tables scrape
    for source in ["squiggle", "afltables"]:
        table = f"match_results_{source}"
        try:
            conn.execute(f"SELECT 1 FROM {table} LIMIT 1")
            break
        except Exception:
            source = None

    if source is None:
        print("  SKIP fact_match_results — no match results table found")
        return

    conn.execute("DROP TABLE IF EXISTS fact_match_results")
    if source == "squiggle":
        query = """
        CREATE TABLE fact_match_results AS
        SELECT
            mr.id               AS match_key,
            ds.season_key,
            dv.venue_key,
            dd.date_key,
            ht.team_key         AS home_team_key,
            at.team_key         AS away_team_key,
            mr.round,
            mr.roundname,
            mr.hgoals           AS home_goals,
            mr.hbehinds         AS home_behinds,
            mr.hscore           AS home_total_score,
            mr.agoals           AS away_goals,
            mr.abehinds         AS away_behinds,
            mr.ascore           AS away_total_score,
            CASE WHEN mr.hscore > mr.ascore THEN ht.team_key
                 WHEN mr.ascore > mr.hscore THEN at.team_key
                 ELSE NULL END  AS winning_team_key,
            ABS(COALESCE(mr.hscore,0) - COALESCE(mr.ascore,0)) AS margin,
            mr.is_final,
            mr.is_grand_final,
            NULL                AS attendance
        FROM match_results_squiggle mr
        LEFT JOIN dim_teams   ht ON mr.hteam   = ht.team_name
        LEFT JOIN dim_teams   at ON mr.ateam   = at.team_name
        LEFT JOIN dim_venues  dv ON mr.venue   = dv.venue_name
        LEFT JOIN dim_seasons ds ON mr.year    = ds.year
        LEFT JOIN dim_date    dd ON DATE(mr.date) = dd.full_date
        """
    else:
        query = """
        CREATE TABLE fact_match_results AS
        SELECT
            ROW_NUMBER() OVER ()   AS match_key,
            ds.season_key,
            dv.venue_key,
            dd.date_key,
            ht.team_key            AS home_team_key,
            at.team_key            AS away_team_key,
            mr.round,
            mr.home_total_score,
            mr.away_total_score,
            CASE WHEN mr.home_total_score > mr.away_total_score THEN ht.team_key
                 WHEN mr.away_total_score > mr.home_total_score THEN at.team_key
                 ELSE NULL END     AS winning_team_key,
            ABS(COALESCE(mr.home_total_score,0) - COALESCE(mr.away_total_score,0)) AS margin,
            NULL AS attendance
        FROM match_results_afltables mr
        LEFT JOIN dim_teams   ht ON mr.home_team = ht.team_name
        LEFT JOIN dim_teams   at ON mr.away_team = at.team_name
        LEFT JOIN dim_venues  dv ON mr.venue     = dv.venue_name
        LEFT JOIN dim_seasons ds ON mr.year      = ds.year
        LEFT JOIN dim_date    dd ON mr.date      = dd.full_date
        """
    conn.execute(query)
    count = conn.execute("SELECT COUNT(*) FROM fact_match_results").fetchone()[0]
    print(f"  Built fact_match_results ({source}): {count} rows")


def run():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    print(f"Connecting to {DATABASE_PATH}")
    conn = sqlite3.connect(DATABASE_PATH)

    print("\nLoading dimension tables...")
    for dim in ["dim_players", "dim_teams", "dim_venues", "dim_seasons", "dim_date"]:
        load_table(conn, f"{CLEANED_DATA_DIR}/{dim}.csv", dim)

    print("\nLoading staging tables...")
    load_table(conn, f"{CLEANED_DATA_DIR}/player_stats.csv", "player_stats")
    load_table(conn, f"{CLEANED_DATA_DIR}/match_results_squiggle.csv", "match_results_squiggle")
    load_table(conn, f"{CLEANED_DATA_DIR}/match_results_afltables.csv", "match_results_afltables")

    print("\nBuilding fact tables...")
    build_fact_player_match_stats(conn)
    build_fact_match_results(conn)

    conn.commit()
    conn.close()
    print(f"\nDatabase ready: {DATABASE_PATH}")


if __name__ == "__main__":
    run()
