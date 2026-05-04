# Power BI Setup Guide

All data loading, cleaning, enrichment and modelling is done inside Power BI.
This demonstrates three layers of Power BI skill: Power Query (ETL), Model view (star schema), DAX (measures).

---

## Step 1 — Download Power BI Desktop

Free download: https://powerbi.microsoft.com/desktop

---

## Step 2 — Load the Raw CSVs

Home → Get Data → Text/CSV → load each file:

| File | Path | What it is |
|---|---|---|
| `player_stats` | `data/cleaned/player_stats.csv` | Fact — 132,112 player-game rows |
| `match_results` | `data/cleaned/match_results_squiggle.csv` | Fact — 3,095 match results |
| `dim_teams` | `data/cleaned/dim_teams.csv` | Dim — 18 teams |
| `dim_players` | `data/cleaned/dim_players.csv` | Dim — 1,859 players |
| `dim_venues` | `data/cleaned/dim_venues.csv` | Dim — 28 venues |
| `dim_seasons` | `data/cleaned/dim_seasons.csv` | Dim — 15 seasons |
| `dim_date` | `data/cleaned/dim_date.csv` | Dim — date spine |
| `squiggle_standings` | `data/raw/squiggle_standings.csv` | Reference — ladder standings |

When prompted after selecting each file click **Transform Data** — this opens Power Query where you do all enrichment before loading.

---

## Step 3 — Power Query Transformations

Power Query Editor is where you clean and enrich the data before it hits the model.
Open it any time via Home → Transform Data.

---

### 3a — Enrich dim_teams

`dim_teams` loads with `abbreviation`, `state` and `home_ground` all blank.
Fill them in inside Power Query so slicers and maps work properly.

**How:** In Power Query, select `dim_teams` → Home → **Enter Data** won't work here.
Instead:

1. Right-click `abbreviation` column → **Replace Values** for each team, OR
2. Better: create a new query with the lookup table, then merge it in.

**Create a new blank query** (Home → New Source → Blank Query), paste this into the formula bar:

```
= Table.FromRows(
    {
        {"Adelaide Crows",    "ADE", "SA",  "Adelaide Oval"},
        {"Brisbane Lions",    "BRI", "QLD", "The Gabba"},
        {"Carlton",           "CAR", "VIC", "Marvel Stadium"},
        {"Collingwood",       "COL", "VIC", "MCG"},
        {"Essendon",          "ESS", "VIC", "Marvel Stadium"},
        {"Fremantle",         "FRE", "WA",  "Optus Stadium"},
        {"Geelong",           "GEE", "VIC", "GMHBA Stadium"},
        {"Gold Coast Suns",   "GCS", "QLD", "People First Stadium"},
        {"GWS Giants",        "GWS", "NSW", "ENGIE Stadium"},
        {"Hawthorn",          "HAW", "VIC", "MCG"},
        {"Melbourne",         "MEL", "VIC", "MCG"},
        {"North Melbourne",   "NTH", "VIC", "Marvel Stadium"},
        {"Port Adelaide",     "PAP", "SA",  "Adelaide Oval"},
        {"Richmond",          "RIC", "VIC", "MCG"},
        {"St Kilda",          "STK", "VIC", "Marvel Stadium"},
        {"Sydney Swans",      "SYD", "NSW", "SCG"},
        {"West Coast Eagles", "WCE", "WA",  "Optus Stadium"},
        {"Western Bulldogs",  "WBD", "VIC", "Marvel Stadium"}
    },
    {"team_name", "abbreviation", "state", "home_ground"}
)
```

Name this query `team_lookup`. Then in `dim_teams`:
- Home → **Merge Queries** → merge on `team_name` = `team_lookup[team_name]`
- Expand the merged column → select `abbreviation`, `state`, `home_ground`
- Delete the original blank columns

---

### 3b — Enrich dim_venues

Same approach — create a blank query named `venue_lookup`:

```
= Table.FromRows(
    {
        {"MCG",            "Melbourne",  "VIC", 100024, "Grass"},
        {"Marvel Stadium", "Melbourne",  "VIC", 56347,  "Grass"},
        {"GMHBA Stadium",  "Geelong",    "VIC", 36000,  "Grass"},
        {"Adelaide Oval",  "Adelaide",   "SA",  53583,  "Grass"},
        {"Optus Stadium",  "Perth",      "WA",  60000,  "Grass"},
        {"The Gabba",      "Brisbane",   "QLD", 42000,  "Grass"},
        {"SCG",            "Sydney",     "NSW", 48000,  "Grass"},
        {"ENGIE Stadium",  "Sydney",     "NSW", 24000,  "Grass"},
        {"People First Stadium", "Gold Coast", "QLD", 26000, "Grass"},
        {"Manuka Oval",    "Canberra",   "ACT", 13000,  "Grass"},
        {"Mars Stadium",   "Ballarat",   "VIC", 13500,  "Grass"},
        {"UTAS Stadium",   "Launceston", "TAS", 20000,  "Grass"},
        {"TIO Stadium",    "Darwin",     "NT",  18000,  "Grass"},
        {"Cazaly's Stadium","Cairns",    "QLD", 10000,  "Grass"},
        {"Norwood Oval",   "Adelaide",   "SA",  20000,  "Grass"}
    },
    {"venue_name", "city", "state", "capacity", "surface"}
)
```

Merge into `dim_venues` on `venue_name` the same way as teams.

---

### 3c — Fill dim_seasons

`num_rounds` and `premiers` are blank. Fill them in directly:

In `dim_seasons` → select the `num_rounds` column → **Replace Values** or use a manual lookup query:

```
= Table.FromRows(
    {
        {2012, 23, "Sydney Swans"},
        {2013, 23, "Hawthorn"},
        {2014, 23, "Hawthorn"},
        {2015, 23, "Hawthorn"},
        {2016, 23, "Western Bulldogs"},
        {2017, 23, "Richmond"},
        {2018, 23, "West Coast Eagles"},
        {2019, 23, "Richmond"},
        {2020, 18, "Richmond"},
        {2021, 23, "Melbourne"},
        {2022, 23, "Geelong"},
        {2023, 24, "Collingwood"},
        {2024, 24, "Brisbane Lions"},
        {2025, 24, "TBC"},
        {2026, 24, "TBC"}
    },
    {"year", "num_rounds", "premiers"}
)
```

Merge into `dim_seasons` on `year`.

---

### 3d — Add match key to player_stats

`player_stats` has no direct link to `match_results`. Add a composite key column so you can later use it in DAX to filter player stats by match outcome.

In `player_stats` Power Query → Add Column → **Custom Column**:

```
Column name: match_key
Formula:     [team] & "_" & Text.From([year]) & "_R" & Text.From([round])
```

Do the same in `match_results` → Add Column → Custom Column:

```
Column name: match_key_home
Formula:     [hteam] & "_" & Text.From([year]) & "_R" & Text.From([round])

Column name: match_key_away
Formula:     [ateam] & "_" & Text.From([year]) & "_R" & Text.From([round])
```

This lets you write DAX like: "show stats only for games the team won" by cross-filtering through the match key.

---

### 3e — Fix data types

In each table, verify these types before closing Power Query:

| Table | Column | Type |
|---|---|---|
| `player_stats` | All stat columns (kicks, marks, etc.) | Decimal Number |
| `player_stats` | `year`, `round` | Whole Number |
| `match_results` | `hscore`, `ascore`, `margin` | Whole Number |
| `match_results` | `date` | Date |
| `dim_date` | `full_date` | Date |
| `dim_date` | `is_finals`, `is_weekend` | True/False |
| `squiggle_standings` | `wins`, `losses`, `pts`, `rank` | Whole Number |
| `squiggle_standings` | `percentage` | Decimal Number |

Click **Close & Apply** when done.

---

## Step 4 — Build the Star Schema (Model View)

Go to the **Model view** icon on the left sidebar. Drag and drop relationships, then double-click each to confirm the settings.

### Relationship settings explained

| Setting | What it means |
|---|---|
| **Many-to-one (\*→1)** | Many rows in the fact match one row in the dim — always this in a star schema |
| **Cross-filter: Single** | Dim filters fact only — use on all fact→dim links |
| **Active** | Default relationship used in all DAX |
| **Inactive** | Dormant — only fires when you call USERELATIONSHIP() in a measure |

---

### player_stats relationships

| From | To | Cardinality | Cross-filter | Active? |
|---|---|---|---|---|
| `player_stats[team]` | `dim_teams[team_name]` | Many-to-one (\*→1) | Single | Yes |
| `player_stats[year]` | `dim_seasons[year]` | Many-to-one (\*→1) | Single | Yes |
| `player_stats[player_name]` | `dim_players[player_name]` | Many-to-one (\*→1) | Single | Yes |
| `player_stats[opponent]` | `dim_teams[team_name]` | Many-to-one (\*→1) | Single | **No (Inactive)** |

---

### match_results relationships

| From | To | Cardinality | Cross-filter | Active? |
|---|---|---|---|---|
| `match_results[hteam]` | `dim_teams[team_name]` | Many-to-one (\*→1) | Single | Yes |
| `match_results[venue]` | `dim_venues[venue_name]` | Many-to-one (\*→1) | Single | Yes |
| `match_results[year]` | `dim_seasons[year]` | Many-to-one (\*→1) | Single | Yes |
| `match_results[date]` | `dim_date[full_date]` | Many-to-one (\*→1) | Single | Yes |
| `match_results[ateam]` | `dim_teams[team_name]` | Many-to-one (\*→1) | Single | **No (Inactive)** |
| `match_results[winner]` | `dim_teams[team_name]` | Many-to-one (\*→1) | Single | **No (Inactive)** |

---

### squiggle_standings relationships

| From | To | Cardinality | Cross-filter | Active? |
|---|---|---|---|---|
| `squiggle_standings[name]` | `dim_teams[team_name]` | Many-to-one (\*→1) | Single | Yes |
| `squiggle_standings[year]` | `dim_seasons[year]` | Many-to-one (\*→1) | Single | Yes |

---

### Star schema diagram

Two independent stars sharing conformed dimensions (`dim_teams`, `dim_seasons`).

**Star 1 — player_stats**
```
                        dim_players
                             │ player_name (1)
                             │
            year (1)         ▼
dim_seasons ────────────► player_stats ◄──────────── dim_teams
                         (132,112 rows)              team [ACTIVE]
                                                     opponent [INACTIVE]
```

**Star 2 — match_results**
```
                           dim_date
                               │ date (1)
                               │
             year (1)          ▼
dim_seasons ──────────► match_results ◄──────────── dim_teams
                          (3,095 rows)              hteam [ACTIVE]
                               ▲                    ateam [INACTIVE]
                               │ venue (1)          winner [INACTIVE]
                           dim_venues
```

**Star 3 — squiggle_standings**
```
                         dim_teams
                              │ name (1)
                              │
              year (1)        ▼
dim_seasons ──────────► squiggle_standings
                           (270 rows)
```

---

## Step 5 — Mark the Date Table

Select `dim_date` → Table tools → **Mark as date table** → date column = `full_date`.

This unlocks all time intelligence DAX (SAMEPERIODLASTYEAR, DATESYTD, rolling averages).

---

## Step 6 — DAX Measures

Create a dedicated measures table: Home → **Enter Data** → blank table, name it `_Measures` → Load.

### Core stats

```dax
Total Disposals = SUM(player_stats[disposals])

Avg Disposals Per Game = AVERAGE(player_stats[disposals])

Total Goals = SUM(player_stats[goals])

Avg Goals Per Game = AVERAGE(player_stats[goals])

Total Clearances = SUM(player_stats[clearances])

Total Contested Possessions = SUM(player_stats[contested_possessions])

Total Inside 50s = SUM(player_stats[inside_50s])

Total Tackles = SUM(player_stats[tackles])

Games Played = COUNTROWS(player_stats)
```

### Player rankings

```dax
Disposal Rank =
RANKX(
    ALLSELECTED(dim_players[player_name]),
    [Avg Disposals Per Game],
    ,
    DESC,
    DENSE
)

Goal Rank =
RANKX(
    ALLSELECTED(dim_players[player_name]),
    [Avg Goals Per Game],
    ,
    DESC,
    DENSE
)

Clearance Rank =
RANKX(
    ALLSELECTED(dim_players[player_name]),
    [Total Clearances],
    ,
    DESC,
    DENSE
)
```

### Match results

```dax
Total Matches = COUNTROWS(match_results)

Home Wins =
CALCULATE(
    COUNTROWS(match_results),
    match_results[winner] = match_results[hteam]
)

Away Wins =
CALCULATE(
    COUNTROWS(match_results),
    match_results[winner] = match_results[ateam]
)

Home Win % =
DIVIDE([Home Wins], [Total Matches], 0) * 100

Avg Winning Margin = AVERAGE(match_results[margin])

Avg Total Score =
AVERAGEX(
    match_results,
    match_results[hscore] + match_results[ascore]
)
```

### Ladder / standings

```dax
Season Wins = SUM(squiggle_standings[wins])

Win % =
DIVIDE(
    SUM(squiggle_standings[wins]),
    SUM(squiggle_standings[played]),
    0
) * 100

Ladder Position = MIN(squiggle_standings[rank])
```

### Inactive relationship measures

```dax
-- Disposals AGAINST a team (uses inactive opponent relationship)
Disposals vs Opponent =
CALCULATE(
    [Total Disposals],
    USERELATIONSHIP(player_stats[opponent], dim_teams[team_name])
)

-- Away team wins (uses inactive ateam relationship)
Away Team Wins =
CALCULATE(
    [Total Matches],
    USERELATIONSHIP(match_results[ateam], dim_teams[team_name]),
    match_results[winner] = match_results[ateam]
)
```

### Time intelligence

```dax
YoY Avg Disposals Change % =
VAR CurrentYear = [Avg Disposals Per Game]
VAR PriorYear =
    CALCULATE(
        [Avg Disposals Per Game],
        SAMEPERIODLASTYEAR(dim_date[full_date])
    )
RETURN
    DIVIDE(CurrentYear - PriorYear, PriorYear, BLANK()) * 100

Rolling 3-Season Avg Disposals =
CALCULATE(
    [Avg Disposals Per Game],
    DATESINPERIOD(dim_date[full_date], LASTDATE(dim_date[full_date]), -3, YEAR)
)
```

### What-if parameter

Modeling → New Parameter → name: `Contested Poss Uplift %` → range 0 to 30, increment 1.

```dax
Adjusted Inside 50s =
[Total Inside 50s] * (1 + 'Contested Poss Uplift %'[Contested Poss Uplift % Value] / 100)
```

---

## Step 7 — Report Pages

### Page 1: Season Overview
- Cards: Total matches, Avg total score, Avg margin
- Line chart: Avg total score by year (scoring trend 2012–2026)
- Bar chart: Wins by team — slicer on `dim_seasons[year]`
- Table: Ladder — team, wins, losses, percentage, rank from `squiggle_standings`

### Page 2: Head-to-Head
- Two slicers: Home Team (`dim_teams`), Away Team (inactive rel)
- Cards: H2H record, avg home score, avg away score
- Bar chart: Home win % by venue
- Line chart: Team form by round (wins_last_5 from SQL query)

### Page 3: Player Deep Dive
- Slicers: Team → Player (hierarchy drill-through)
- Line chart: Avg disposals by season (career trajectory)
- Bar chart: Stat breakdown — kicks, marks, handballs, clearances
- Table: Season-by-season with Disposal Rank and Goal Rank

### Page 4: Venue & Scoring Analysis
- Bar chart: Home win % by venue
- Bar chart: Avg total score by venue
- Line chart: League scoring trend by season
- Slicer: Finals vs Home-and-Away (`dim_date[is_finals]`)

---

## Notes

- Save the `.pbix` to `powerbi/AFL_Analytics.pbix` and commit it to GitHub
- `data/` is in `.gitignore` so CSVs are not committed — only the `.pbix` file goes to GitHub
- To refresh data after re-running the ETL pipeline: Home → **Refresh**
