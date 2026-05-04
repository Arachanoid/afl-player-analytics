# 🏉 AFL Player Performance & Match Analytics

A full-stack data engineering and analytics portfolio project — from raw web scraping through statistical modelling to an executive-ready Power BI dashboard.

---

## 📌 Project Overview

This project builds an end-to-end analytics pipeline for Australian Football League (AFL) data, demonstrating skills across the full data lifecycle: ingestion, modelling, analysis, machine learning, and visualisation.

**What this project proves:** You can go from raw, messy, real-world data → proper dimensional modelling → complex SQL analysis → rigorous statistical testing → ML-driven insights → polished interactive dashboard.

---

## 🎯 Skills Covered

| Skill Area | What's Demonstrated |
|---|---|
| **Web Scraping** | Python scraper (BeautifulSoup + requests) to ingest raw HTML tables from AFL Tables |
| **Data Cleaning** | Handling inconsistent team names, venue name changes, missing stats, dirty HTML |
| **SQL & Data Modelling** | Star schema design, complex window functions, CTEs, cohort analysis |
| **Statistics** | ANOVA, logistic regression, Poisson regression, bootstrapped confidence intervals |
| **Python** | pandas, scikit-learn, scipy, statsmodels — full analytical pipeline |
| **DAX & Power BI** | Time intelligence, RANKX, CALCULATE with complex filters, what-if parameters |
| **Domain Knowledge** | AFL-specific metrics, contextual analysis, Melbourne venue comparisons |
| **Critical Thinking** | Hypothesis formulation, statistical rigour, interpreting results in context |

---

## 📊 Data Sources

### Source 1: AFL Tables (afltables.com) — Primary Data
- **What:** Raw HTML tables containing player statistics and match results
- **Coverage:** Player stats 1965–2026, match scores 1897–2026
- **How:** Custom Python scraper built with BeautifulSoup and requests
- **Player stats columns:** Team, Year, Games Played, Opponent, Round, Result, Jersey Number, Kicks, Marks, Handballs, Disposals, Goals, Behinds, Hit Outs, Tackles, Rebound 50s, Inside 50s, Clearances, Clangers, Free Kicks For/Against, Brownlow Votes, Contested Possessions, Uncontested Possessions, Contested Marks, Marks Inside 50, One Percenters, Bounces, Goal Assist, % Game Played
- **Match data columns:** Year, Round, Venue, Date, Home/Away Team, Goals & Behinds by Quarter, Total Score, Winning Team, Margin

### Source 2: Squiggle API (api.squiggle.com.au) — Supplementary Data
- **What:** REST API providing match results, fixtures, ladder standings, venue and team metadata
- **Coverage:** Match data ~2001–2026 (current season included)
- **How:** Python `requests` library, no authentication required
- **Key endpoints:** `?q=games`, `?q=standings`, `?q=teams`
- **Purpose:** Populates dimension tables (teams, venues, seasons) and provides current 2026 season data

### Project Scope
- **Analysis window:** 2012–2026 seasons (detailed stats availability from Footywire-era onwards)
- **Grain:** Player-level per-match statistics

---

## 🗄️ Data Model — Star Schema

```
                    ┌──────────────┐
                    │  dim_seasons │
                    │──────────────│
                    │ season_key   │
                    │ year         │
                    │ num_rounds   │
                    │ premiers     │
                    └──────┬───────┘
                           │
┌──────────────┐   ┌───────┴────────────────┐   ┌──────────────┐
│  dim_players │   │ fact_player_match_stats │   │  dim_teams   │
│──────────────│   │────────────────────────│   │──────────────│
│ player_key   │◄──│ player_key             │   │ team_key     │
│ first_name   │   │ team_key               │──►│ team_name    │
│ last_name    │   │ opponent_key           │   │ abbreviation │
│ dob          │   │ venue_key              │   │ state        │
│ height_cm    │   │ season_key             │   │ home_ground  │
│ weight_kg    │   │ date_key               │   └──────────────┘
│ position     │   │ round                  │
│ draft_year   │   │ result                 │   ┌──────────────┐
│ draft_pick   │   │ kicks                  │   │  dim_venues  │
└──────────────┘   │ marks                  │   │──────────────│
                   │ handballs              │   │ venue_key    │
┌──────────────┐   │ disposals              │──►│ venue_name   │
│  dim_date    │   │ goals                  │   │ city         │
│──────────────│   │ behinds                │   │ state        │
│ date_key     │◄──│ hit_outs               │   │ capacity     │
│ full_date    │   │ tackles                │   │ surface      │
│ day_of_week  │   │ rebounds               │   └──────────────┘
│ month        │   │ inside_50s             │
│ is_finals    │   │ clearances             │
│ is_weekend   │   │ clangers               │
└──────────────┘   │ frees_for              │
                   │ frees_against          │
                   │ contested_possessions  │
                   │ uncontested_possessions│
                   │ contested_marks        │
                   │ marks_inside_50        │
                   │ one_percenters         │
                   │ bounces                │
                   │ goal_assists           │
                   │ pct_game_played        │
                   │ brownlow_votes         │
                   └────────────────────────┘

              ┌─────────────────────────┐
              │   fact_match_results    │
              │─────────────────────────│
              │ match_key               │
              │ season_key              │
              │ venue_key               │
              │ date_key                │
              │ home_team_key           │
              │ away_team_key           │
              │ round                   │
              │ home_q1–q4_goals/behind │
              │ away_q1–q4_goals/behind │
              │ home_total_score        │
              │ away_total_score        │
              │ winning_team_key        │
              │ margin                  │
              │ attendance              │
              └─────────────────────────┘
```

**Design decisions:**
- Separate fact tables for player stats (player-match grain) and match results (match grain) to avoid fan traps
- Surrogate keys throughout — natural keys (player names, venue names) change over time
- `dim_date` with `is_finals` flag enables easy filtering for finals-only analysis in DAX
- Team name changes handled via SCD Type 2 in `dim_teams` (e.g., Footscray → Western Bulldogs)
- Venue name inconsistencies resolved during ETL (e.g., "M.C.G." → "MCG", "Docklands" → "Marvel Stadium")

---

## 🔧 Project Phases

### Phase 1: Data Ingestion & Scraping
- Build Python scraper for AFL Tables (BeautifulSoup + requests)
- Hit Squiggle API for supplementary team/venue/fixture data
- Raw data lands in `/data/raw/` as CSVs
- Handle rate limiting, retries, and incremental scraping

### Phase 2: Data Cleaning & Transformation
- Standardise team names across eras
- Resolve venue name inconsistencies
- Handle missing stats (pre-2012 seasons have fewer columns)
- Parse dates, calculate derived fields
- Output cleaned CSVs to `/data/cleaned/`

### Phase 3: Data Modelling & SQL Layer
- Load into SQLite (or PostgreSQL) with star schema
- Build surrogate keys and dimension tables
- **Complex SQL queries:**
  - Player efficiency ratings using `RANK()` / `DENSE_RANK()` window functions
  - Team form calculations with `LAG/LEAD` across rounds
  - Venue-specific win rates with CTEs
  - Home vs away performance splits
  - Cohort analysis: player debut year cohorts and career trajectory

### Phase 4: Statistical Analysis (Python)
- **ANOVA:** Does scoring output differ significantly across Melbourne venues (MCG vs Marvel Stadium vs GMHBA Park)?
- **Logistic Regression:** Predict match outcomes using disposals differential, contested possessions, and inside-50s
- **Poisson Regression:** Model expected score from team-level stats
- **Bootstrapped Confidence Intervals:** Player impact metrics with uncertainty quantification
- **Correlation Analysis:** Key performance indicators vs season ladder position

### Phase 5: Power BI Dashboard
- Connect to SQL database
- **DAX measures:**
  - `RANKX` + `TOPN` for dynamic player rankings across stats
  - Time intelligence for career trajectory analysis (YoY, rolling averages)
  - `CALCULATE` with complex filters: "finals only" vs "home-and-away"
  - What-if parameters: "what if Team X improved contested possessions by 10%?"
- **Report pages:**
  1. **Season Overview** — ladder, team form, key stats summary
  2. **Head-to-Head Matchups** — team comparison with slicer-driven filtering
  3. **Player Deep Dive** — drill-through from team → position → individual player
  4. **Predictive Insights** — model outputs, feature importance, scenario analysis

---

## 📁 Project Structure

```
afl-analytics/
├── README.md
├── requirements.txt
├── .gitignore
│
├── data/
│   ├── raw/                    # Raw scraped data (CSVs from AFL Tables + Squiggle)
│   ├── cleaned/                # Cleaned and standardised CSVs
│   └── database/               # SQLite database file
│
├── scrapers/
│   ├── afltables_scraper.py    # AFL Tables web scraper
│   ├── squiggle_api.py         # Squiggle API client
│   └── config.py               # Scraping config (years, endpoints, rate limits)
│
├── etl/
│   ├── clean_player_stats.py   # Data cleaning pipeline
│   ├── clean_match_results.py  # Match data cleaning
│   ├── build_dimensions.py     # Generate dimension tables
│   ├── load_star_schema.py     # Load into SQLite star schema
│   └── team_name_mapping.json  # Historical team name → current name mapping
│
├── sql/
│   ├── create_schema.sql       # DDL for star schema
│   ├── player_rankings.sql     # Window function queries
│   ├── team_form.sql           # LAG/LEAD form calculations
│   ├── venue_analysis.sql      # Venue-specific win rates
│   └── cohort_analysis.sql     # Player debut cohort queries
│
├── analysis/
│   ├── 01_eda.ipynb                    # Exploratory data analysis
│   ├── 02_venue_anova.ipynb            # ANOVA: scoring across venues
│   ├── 03_match_prediction.ipynb       # Logistic regression: match outcomes
│   ├── 04_expected_score_model.ipynb   # Poisson regression: expected scores
│   ├── 05_player_impact.ipynb          # Bootstrapped player metrics
│   └── 06_correlation_analysis.ipynb   # KPIs vs ladder position
│
├── powerbi/
│   └── AFL_Analytics.pbix      # Power BI report file
│
└── docs/
    ├── data_dictionary.md      # Full column definitions
    └── methodology.md          # Statistical methodology notes
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| Scraping | Python, BeautifulSoup, requests |
| Storage | SQLite (dev) / PostgreSQL (optional) |
| Data Cleaning | Python, pandas |
| Statistical Analysis | scipy, statsmodels, scikit-learn |
| Visualisation | matplotlib, seaborn (notebooks) |
| Dashboard | Power BI, DAX |
| Version Control | Git, GitHub |

---

## 🚀 Getting Started

```bash
# Clone the repo
git clone https://github.com/<your-username>/afl-analytics.git
cd afl-analytics

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the scraper (pulls data from AFL Tables)
python scrapers/afltables_scraper.py --start_year 2012 --end_year 2026

# Pull Squiggle API data
python scrapers/squiggle_api.py

# Clean and load into star schema
python etl/clean_player_stats.py
python etl/clean_match_results.py
python etl/build_dimensions.py
python etl/load_star_schema.py

# Open notebooks for analysis
jupyter notebook analysis/
```

---

## 📝 Key Hypotheses to Test

1. **Venue Effect:** Does scoring output differ significantly across MCG, Marvel Stadium, and GMHBA Park? (ANOVA)
2. **Match Prediction:** Can disposals differential, contested possessions, and inside-50s predict match outcomes? (Logistic Regression)
3. **Expected Scoring:** Does a Poisson model adequately capture team scoring patterns? (Poisson Regression)
4. **Home Advantage:** Is the home ground advantage statistically significant after controlling for team strength? (t-test)
5. **Friday Night Effect:** Does the Friday night timeslot actually boost disposal counts? (Hypothesis test)

---

## 📄 License

MIT License
