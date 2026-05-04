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

### AFL Tables Scraper — PENDING
**Script:** `scrapers/afltables_scraper.py`
**Run:** `python scrapers/afltables_scraper.py --start_year 2024 --end_year 2024` (test first)

- Scrapes per-season player stats from `afltables.com/afl/stats/{year}.html`
- One row per player-game, all teams, full season
- Target columns: player_name, team, kicks, marks, handballs, disposals, goals, behinds, hit_outs, tackles, rebounds, inside_50s, clearances, clangers, frees_for, frees_against, brownlow_votes, contested_possessions, uncontested_possessions, contested_marks, marks_inside_50, one_percenters, bounces, goal_assists, pct_game_played
- **Run single year first** to verify column order before doing full 2012–2026

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

## SQL Queries — WRITTEN, NOT YET TESTED

| File | What it does |
|---|---|
| `sql/create_schema.sql` | DDL reference + PostgreSQL migration target |
| `sql/player_rankings.sql` | Season averages ranked with RANK() window function |
| `sql/team_form.sql` | Rolling last-5-game form string using LAG() |
| `sql/venue_analysis.sql` | Home win rates + Melbourne venue scoring for ANOVA |
| `sql/cohort_analysis.sql` | Player debut cohort career trajectory |

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
