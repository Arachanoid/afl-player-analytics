# AFL Analytics — Build Progress Log

A running record of what has been built, decisions made, and what comes next.

---

## Project Status: Phase 1 — Data Ingestion (In Progress)

---

## What's Been Built

### Folder Structure
```
data/
  raw/        ← scraped CSVs land here
  cleaned/    ← cleaned/standardised CSVs
  database/   ← SQLite .db file
scrapers/     ← Python scrapers
etl/          ← cleaning + loading scripts
sql/          ← SQL queries
analysis/     ← Jupyter notebooks
powerbi/      ← .pbix file (Phase 5)
docs/         ← data dictionary, methodology
```

### Config & Setup
- `requirements.txt` — all Python dependencies pinned
- `.gitignore` — excludes raw data, database, venv, notebooks checkpoints
- `scrapers/config.py` — central config: years (2012–2026), URLs, paths
  - Paths are resolved as absolute from the project root so scripts can be run from any directory

---

## Data Sources

### Squiggle API — COMPLETE
**Script:** `scrapers/squiggle_api.py`
**Run:** `python scrapers/squiggle_api.py` from project root

| File | Rows | Notes |
|---|---|---|
| `data/raw/squiggle_teams.csv` | 18 | id, name, abbrev, debut year |
| `data/raw/squiggle_venues.csv` | 17 | venue names only (from 2026 games) |
| `data/raw/squiggle_games.csv` | 3,095 | All matches 2012–2026 |
| `data/raw/squiggle_standings.csv` | 270 | Season ladder, 18 teams × 15 seasons |

**Key columns in squiggle_games.csv:**
`id, year, round, roundname, date, venue, hteam, ateam, hteamid, ateamid, hgoals, hbehinds, hscore, agoals, abehinds, ascore, winner, winnerteamid, is_final, is_grand_final, complete, timestr`

**Known issues / notes:**
- Venue names are raw (e.g. `M.C.G.`, `Carrara`) — normalised in ETL via `venue_name_mapping.json`
- Team names are short form (e.g. `Adelaide` not `Adelaide Crows`) — normalised via `team_name_mapping.json`
- 2020 season has 162 games (COVID-shortened season)
- `complete` field = 100 means final result, lower values = live/incomplete

### AFL Tables Scraper — COMPLETE
**Script:** `scrapers/afltables_scraper.py`

| File | Rows | Notes |
|---|---|---|
| `data/raw/afltables_player_stats.csv` | 132,112 | Per-game stats, 2012–2026, all 18 teams |

**Columns:** `player_name, team, year, round, opponent, disposals, kicks, marks, handballs, goals, behinds, hit_outs, tackles, rebounds, inside_50s, clearances, clangers, frees_for, frees_against, brownlow_votes, contested_possessions, uncontested_possessions, contested_marks, marks_inside_50, one_percenters, bounces, goal_assists, pct_game_played, subs`

**How it works:**
- Scrapes team Game-by-Game pages (`afltables.com/afl/stats/teams/{slug}/{year}_gbg.html`) — one page per team per year (270 requests total)
- Each page has 23 stat tables in pivot format (player × round); melted to long format and joined
- Opponent abbreviations extracted from `th` header elements
- `-` cells converted to `0` (player played, recorded zero); blank cells = `None` (did not play)

**Known notes:**
- 2020 season has fewer rows (COVID-shortened season, 17 rounds)
- 2026 has 3,312 rows (season in progress at time of scrape)
- `subs` column = substitution status (On/Off/0); not a numeric stat

---

## ETL Pipeline — PENDING (scripts written, not yet run)

| Script | Input | Output | Status |
|---|---|---|---|
| `etl/clean_player_stats.py` | `raw/afltables_player_stats.csv` | `cleaned/player_stats.csv` | Not run |
| `etl/clean_match_results.py` | `raw/afltables_match_results.csv` + `raw/squiggle_games.csv` | `cleaned/match_results_*.csv` | Not run |
| `etl/build_dimensions.py` | cleaned CSVs | `cleaned/dim_*.csv` | Not run |
| `etl/load_star_schema.py` | all cleaned CSVs | `data/database/afl_analytics.db` | Not run |

**Reference files:**
- `etl/team_name_mapping.json` — 30 historical name variants → canonical names (e.g. Footscray → Western Bulldogs)
- `etl/venue_name_mapping.json` — 40 venue name variants → canonical names (e.g. Etihad Stadium → Marvel Stadium)

---

## Star Schema — DESIGNED, NOT YET LOADED

```
fact_player_match_stats   ← player-game grain (from AFL Tables)
fact_match_results        ← match grain (from Squiggle, primary)

dim_players    ← name only for now; bio fields (DOB, height, weight, position) left NULL
dim_teams      ← 18 teams; abbreviation/state/home_ground to be filled manually
dim_venues     ← city/state/capacity/surface left NULL — to be filled manually
dim_seasons    ← 2012–2026; premiers/num_rounds to be filled after data loads
dim_date       ← full date spine 2012–2026; is_finals flag set from match data
```

**Design decisions made:**
- SQLite for dev (no server needed, ships with Python)
- Surrogate integer keys throughout
- No SCD Type 2 — team name changes handled via mapping JSON instead
- `fact_match_results` uses Squiggle as primary source (cleaner than AFL Tables HTML)
- `dim_players` bio fields left NULL until a second enrichment source is added (FootyWire has DOB/height/weight/position)

---

## SQL Queries — COMPLETE & TESTED

| File | What it does | Rows returned |
|---|---|---|
| `sql/create_schema.sql` | DDL reference + PostgreSQL migration target | — |
| `sql/player_rankings.sql` | Season averages ranked with RANK() window function | 100 (top 100) |
| `sql/team_form.sql` | Rolling last-5-game form string using LAG() | 6,172 |
| `sql/venue_analysis.sql` | Home win rates + Melbourne venue scoring for ANOVA | 19 venues + 1,482 game rows |
| `sql/cohort_analysis.sql` | Player debut cohort career trajectory | 120 cohort-year rows |
| `sql/home_away_splits.sql` | Home vs away win %, score, margin per team per season | 540 |
| `sql/scoring_trends.sql` | League-wide scoring averages + range by season | 15 seasons |

**Early findings from SQL:**
- Adelaide Oval has highest home win rate (58.4%) — MCG only 51.0%, Marvel Stadium 46.7% (away team actually wins more often)
- League average total score has declined: 183.7 (2012) → need to check recent years
- 2012 cohort: 671 players, retention drops to 564 by year 2, 489 by year 3

---

## Analysis Notebooks — STARTER ONLY

| File | Status | Purpose |
|---|---|---|
| `analysis/01_eda.ipynb` | Starter written | Row counts, score distributions, top players |
| `analysis/02_venue_anova.ipynb` | Not started | ANOVA: MCG vs Marvel vs GMHBA scoring |
| `analysis/03_match_prediction.ipynb` | Not started | Logistic regression: predict match outcomes |
| `analysis/04_expected_score_model.ipynb` | Not started | Poisson regression: expected score |
| `analysis/05_player_impact.ipynb` | Not started | Bootstrapped player metrics |
| `analysis/06_correlation_analysis.ipynb` | Not started | KPIs vs ladder position |

---

## Known Gaps / To Enrich Later

| Gap | Source to fix it | Priority |
|---|---|---|
| Player bio data (DOB, height, weight, position, draft) | FootyWire scraper | Medium |
| Venue metadata (city, state, capacity, surface) | Manual fill / Wikipedia | Low |
| Quarter-by-quarter scores in fact_match_results | AFL Tables season pages | Low |
| Attendance per match | Squiggle has it in games data | Easy — already in squiggle_games.csv |

---

## Run Order (full pipeline)

```bash
# 1. Squiggle API (done)
python scrapers/squiggle_api.py

# 2. AFL Tables — test one year first
python scrapers/afltables_scraper.py --start_year 2024 --end_year 2024
# inspect data/raw/afltables_player_stats.csv, verify columns, then:
python scrapers/afltables_scraper.py --start_year 2012 --end_year 2026

# 3. Clean
python etl/clean_player_stats.py
python etl/clean_match_results.py

# 4. Build dimensions + load DB
python etl/build_dimensions.py
python etl/load_star_schema.py

# 5. Verify in notebook
jupyter notebook analysis/01_eda.ipynb
```

---

## Change Log

| Date | Change |
|---|---|
| 2026-05-04 | Project initialised — folder structure, all scripts, mappings created |
| 2026-05-04 | Squiggle API run successfully — 3,095 games, 18 teams, 15 seasons |
| 2026-05-04 | Fixed config.py path resolution — paths now absolute from project root |
| 2026-05-04 | AFL Tables scraper rewritten for GBG page structure — 132,112 rows (2012–2026) |
| 2026-05-04 | ETL pipeline complete — star schema loaded into SQLite (132,112 + 3,095 rows) |
| 2026-05-04 | Phase 3 SQL queries complete — 6 queries tested and validated against live DB |
