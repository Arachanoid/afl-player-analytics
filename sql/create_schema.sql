-- Star schema DDL for AFL Analytics (SQLite)
-- Run this manually if you want to pre-create tables before ETL load.
-- load_star_schema.py uses pandas .to_sql() which auto-creates tables,
-- so this file is documentation / for PostgreSQL migration reference.

CREATE TABLE IF NOT EXISTS dim_seasons (
    season_key  INTEGER PRIMARY KEY,
    year        INTEGER NOT NULL UNIQUE,
    num_rounds  INTEGER,
    premiers    TEXT
);

CREATE TABLE IF NOT EXISTS dim_players (
    player_key  INTEGER PRIMARY KEY,
    player_name TEXT NOT NULL,
    first_name  TEXT,
    last_name   TEXT,
    dob         TEXT,
    height_cm   REAL,
    weight_kg   REAL,
    position    TEXT,
    draft_year  INTEGER,
    draft_pick  INTEGER
);

CREATE TABLE IF NOT EXISTS dim_teams (
    team_key     INTEGER PRIMARY KEY,
    team_name    TEXT NOT NULL UNIQUE,
    abbreviation TEXT,
    state        TEXT,
    home_ground  TEXT
);

CREATE TABLE IF NOT EXISTS dim_venues (
    venue_key  INTEGER PRIMARY KEY,
    venue_name TEXT NOT NULL UNIQUE,
    city       TEXT,
    state      TEXT,
    capacity   INTEGER,
    surface    TEXT
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key    INTEGER PRIMARY KEY,
    full_date   TEXT NOT NULL UNIQUE,
    year        INTEGER,
    month       INTEGER,
    day         INTEGER,
    day_of_week TEXT,
    is_weekend  INTEGER,  -- 0/1
    is_finals   INTEGER   -- 0/1
);

CREATE TABLE IF NOT EXISTS fact_player_match_stats (
    stat_key                 INTEGER PRIMARY KEY,
    player_key               INTEGER REFERENCES dim_players(player_key),
    team_key                 INTEGER REFERENCES dim_teams(team_key),
    opponent_key             INTEGER REFERENCES dim_teams(team_key),
    venue_key                INTEGER REFERENCES dim_venues(venue_key),
    season_key               INTEGER REFERENCES dim_seasons(season_key),
    date_key                 INTEGER REFERENCES dim_date(date_key),
    round                    INTEGER,
    result                   TEXT,
    kicks                    INTEGER,
    marks                    INTEGER,
    handballs                INTEGER,
    disposals                INTEGER,
    goals                    INTEGER,
    behinds                  INTEGER,
    hit_outs                 INTEGER,
    tackles                  INTEGER,
    rebounds                 INTEGER,
    inside_50s               INTEGER,
    clearances               INTEGER,
    clangers                 INTEGER,
    frees_for                INTEGER,
    frees_against            INTEGER,
    brownlow_votes           INTEGER,
    contested_possessions    INTEGER,
    uncontested_possessions  INTEGER,
    contested_marks          INTEGER,
    marks_inside_50          INTEGER,
    one_percenters           INTEGER,
    bounces                  INTEGER,
    goal_assists             INTEGER,
    pct_game_played          REAL
);

CREATE TABLE IF NOT EXISTS fact_match_results (
    match_key        INTEGER PRIMARY KEY,
    season_key       INTEGER REFERENCES dim_seasons(season_key),
    venue_key        INTEGER REFERENCES dim_venues(venue_key),
    date_key         INTEGER REFERENCES dim_date(date_key),
    home_team_key    INTEGER REFERENCES dim_teams(team_key),
    away_team_key    INTEGER REFERENCES dim_teams(team_key),
    round            INTEGER,
    home_total_score INTEGER,
    away_total_score INTEGER,
    winning_team_key INTEGER REFERENCES dim_teams(team_key),
    margin           INTEGER,
    attendance       INTEGER
);
