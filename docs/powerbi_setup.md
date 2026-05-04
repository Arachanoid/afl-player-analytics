# Power BI Setup Guide

## Step 1 — Download Power BI Desktop

Free download: https://powerbi.microsoft.com/desktop

---

## Step 2 — Load the Data

Home → Get Data → Text/CSV → load each file from `data/cleaned/`:

| File | What it is |
|---|---|
| `player_stats.csv` | Fact table — 132,112 player-game rows |
| `match_results_squiggle.csv` | Fact table — 3,095 match results |
| `dim_teams.csv` | Dimension — 18 teams |
| `dim_players.csv` | Dimension — 1,859 players |
| `dim_venues.csv` | Dimension — 28 venues |
| `dim_seasons.csv` | Dimension — 15 seasons (2012–2026) |
| `dim_date.csv` | Dimension — date spine with is_finals, is_weekend flags |
| `squiggle_standings.csv` | Reference — season ladder standings |

**When loading each CSV:** Power BI will auto-detect column types. Check that:
- Numeric stat columns (kicks, marks, etc.) are detected as numbers, not text
- `full_date` in `dim_date` is detected as a date
- Key columns (`team_key`, `season_key`, etc.) are whole numbers

---

## Step 3 — Build the Star Schema (Model View)

Go to the **Model view** (icon on the left sidebar). Drag and drop to create each relationship, then double-click it to set the exact properties below.

### Relationship settings explained
| Setting | What it means |
|---|---|
| **Cardinality: Many-to-one** | Many rows in the fact match one row in the dim — standard star schema |
| **Cross-filter: Single** | Dim filters fact, but NOT the other way. Use this on all fact→dim links |
| **Cross-filter: Both** | Filters flow in both directions — only use on dim→dim or reference tables |
| **Active** | The default relationship used in all DAX calculations |
| **Inactive** | Dormant — only activated when you explicitly call USERELATIONSHIP() in a measure |

---

### player_stats (fact table)

| From | To | Cardinality | Cross-filter | Active? |
|---|---|---|---|---|
| `player_stats[team]` | `dim_teams[team_name]` | Many-to-one (\*→1) | Single | Yes |
| `player_stats[year]` | `dim_seasons[year]` | Many-to-one (\*→1) | Single | Yes |
| `player_stats[player_name]` | `dim_players[player_name]` | Many-to-one (\*→1) | Single | Yes |
| `player_stats[opponent]` | `dim_teams[team_name]` | Many-to-one (\*→1) | Single | **No (Inactive)** |

> Power BI only allows **one active relationship between the same two tables**. Both `team` and `opponent` point to `dim_teams`, so `opponent` must be inactive. To use it in a measure: `CALCULATE([Total Disposals], USERELATIONSHIP(player_stats[opponent], dim_teams[team_name]))`

---

### match_results_squiggle (fact table)

| From | To | Cardinality | Cross-filter | Active? |
|---|---|---|---|---|
| `match_results_squiggle[hteam]` | `dim_teams[team_name]` | Many-to-one (\*→1) | Single | Yes |
| `match_results_squiggle[venue]` | `dim_venues[venue_name]` | Many-to-one (\*→1) | Single | Yes |
| `match_results_squiggle[year]` | `dim_seasons[year]` | Many-to-one (\*→1) | Single | Yes |
| `match_results_squiggle[date]` | `dim_date[full_date]` | Many-to-one (\*→1) | Single | Yes |
| `match_results_squiggle[ateam]` | `dim_teams[team_name]` | Many-to-one (\*→1) | Single | **No (Inactive)** |
| `match_results_squiggle[winner]` | `dim_teams[team_name]` | Many-to-one (\*→1) | Single | **No (Inactive)** |

> Same reason as above — three columns (`hteam`, `ateam`, `winner`) all point to `dim_teams`, only one can be active. `hteam` is active as the primary team context.

---

### squiggle_standings (reference table)

| From | To | Cardinality | Cross-filter | Active? |
|---|---|---|---|---|
| `squiggle_standings[name]` | `dim_teams[team_name]` | Many-to-one (\*→1) | Single | Yes |
| `squiggle_standings[year]` | `dim_seasons[year]` | Many-to-one (\*→1) | Single | Yes |

---

### How it looks in Model view

Two independent stars sharing conformed dimension tables. Each fact sits in the centre of its own star — dims only ever appear on the outside edge, never linking to each other.

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

**Why dim_teams and dim_seasons appear in all three stars:**
These are called **conformed dimensions** — the same lookup table used by multiple fact tables. This is correct and intentional. It means one `dim_teams` slicer in Power BI filters all three fact tables simultaneously.

**What a star is NOT:**
- Dims do not link to other dims
- Fact tables do not link to each other directly
- No dim sits between two facts

---

## Step 4 — Mark the Date Table

Select `dim_date` → Table tools → **Mark as date table** → date column = `full_date`.

This unlocks all time intelligence DAX functions (SAMEPERIODLASTYEAR, DATESYTD, etc.).

---

## Step 5 — DAX Measures

Create a dedicated **Measures table** (Enter Data → blank table named `_Measures`).

### Core measures

```dax
Total Disposals = SUM(player_stats[disposals])

Avg Disposals Per Game = AVERAGE(player_stats[disposals])

Total Goals = SUM(player_stats[goals])

Avg Goals Per Game = AVERAGE(player_stats[goals])

Total Clearances = SUM(player_stats[clearances])

Total Contested Possessions = SUM(player_stats[contested_possessions])

Total Inside 50s = SUM(player_stats[inside_50s])

Total Tackles = SUM(player_stats[tackles])
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
```

### Match results

```dax
Home Wins =
CALCULATE(
    COUNTROWS(match_results_squiggle),
    match_results_squiggle[winner] = match_results_squiggle[hteam]
)

Away Wins =
CALCULATE(
    COUNTROWS(match_results_squiggle),
    match_results_squiggle[winner] = match_results_squiggle[ateam]
)

Home Win % =
DIVIDE([Home Wins], COUNTROWS(match_results_squiggle), 0) * 100

Avg Winning Margin = AVERAGE(match_results_squiggle[margin])

Avg Total Score =
AVERAGEX(
    match_results_squiggle,
    match_results_squiggle[hscore] + match_results_squiggle[ascore]
)
```

### Season ladder

```dax
Team Wins (Season) = SUM(squiggle_standings[wins])

Team Win % (Season) =
DIVIDE(
    SUM(squiggle_standings[wins]),
    SUM(squiggle_standings[played]),
    0
) * 100

Ladder Position = MIN(squiggle_standings[rank])
```

### Time intelligence (requires marked date table)

```dax
YoY Disposal Change % =
VAR CurrentYear = [Avg Disposals Per Game]
VAR PriorYear =
    CALCULATE(
        [Avg Disposals Per Game],
        SAMEPERIODLASTYEAR(dim_date[full_date])
    )
RETURN DIVIDE(CurrentYear - PriorYear, PriorYear, BLANK()) * 100
```

### What-if parameter (contested possessions scenario)

Create via Modeling → New Parameter → name it "Contested Poss Uplift %" → range 0–30, increment 1.

```dax
Adjusted Inside 50s =
[Total Inside 50s] * (1 + 'Contested Poss Uplift %'[Contested Poss Uplift % Value] / 100)
```

---

## Step 6 — Report Pages

### Page 1: Season Overview
- Card visuals: Total matches, Avg total score, Avg margin
- Line chart: Avg total score by year (scoring trend)
- Bar chart: Team wins by season (slicer on year)
- Table: Ladder standings with rank, wins, percentage

### Page 2: Head-to-Head
- Two slicers: Home Team, Away Team
- Cards: H2H record, avg scores
- Bar chart: Win % home vs away by venue
- Line chart: Form over the season (rolling wins)

### Page 3: Player Deep Dive
- Slicer: Team → Position → Player (drill-through hierarchy)
- Line chart: Avg disposals by season (career trajectory)
- Bar chart: Stat breakdown (kicks, marks, handballs, clearances)
- Table: Season-by-season stats with RANKX disposal rank

### Page 4: Venue Analysis
- Map visual: Venues (requires lat/long — add manually to dim_venues)
- Bar chart: Home win % by venue
- Box-style bar chart: Avg total score by venue
- Slicer: Season filter

---

## Notes

- `data/cleaned/` files are the source — if you re-run the ETL, just refresh in Power BI
- The `data/` folder is in `.gitignore` so CSVs are not committed to GitHub
- Save the `.pbix` file to `powerbi/AFL_Analytics.pbix` and commit it to GitHub
