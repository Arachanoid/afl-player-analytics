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

Go to the **Model view** (icon on the left sidebar). Drag and drop to create these relationships:

### player_stats (fact)
| player_stats column | → | Dimension | column |
|---|---|---|---|
| `team` | → | `dim_teams` | `team_name` |
| `year` | → | `dim_seasons` | `year` |
| `player_name` | → | `dim_players` | `player_name` |

> Set `opponent → dim_teams.team_name` as an **inactive** relationship (Power BI only allows one active relationship per table pair). Use USERELATIONSHIP() in DAX when you need opponent context.

### match_results_squiggle (fact)
| match_results column | → | Dimension | column |
|---|---|---|---|
| `hteam` | → | `dim_teams` | `team_name` |
| `venue` | → | `dim_venues` | `venue_name` |
| `year` | → | `dim_seasons` | `year` |
| `date` (DATE() cast) | → | `dim_date` | `full_date` |

> `ateam` and `winner` → `dim_teams.team_name` should be set as **inactive** relationships.

### squiggle_standings (reference)
| squiggle_standings column | → | Dimension | column |
|---|---|---|---|
| `name` | → | `dim_teams` | `team_name` |
| `year` | → | `dim_seasons` | `year` |

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
