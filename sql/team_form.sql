-- Team form: rolling results using LAG/LEAD
-- Shows each team's last 5 game results and current form string

WITH match_outcomes AS (
    SELECT
        t.team_name,
        s.year,
        mr.round,
        d.full_date,
        CASE
            WHEN mr.home_team_key = t.team_key AND mr.winning_team_key = t.team_key THEN 'W'
            WHEN mr.away_team_key = t.team_key AND mr.winning_team_key = t.team_key THEN 'W'
            WHEN mr.winning_team_key IS NULL THEN 'D'
            ELSE 'L'
        END AS result,
        CASE
            WHEN mr.home_team_key = t.team_key THEN mr.home_total_score
            ELSE mr.away_total_score
        END AS team_score,
        CASE
            WHEN mr.home_team_key = t.team_key THEN mr.away_total_score
            ELSE mr.home_total_score
        END AS opp_score
    FROM fact_match_results mr
    JOIN dim_teams   t ON t.team_key IN (mr.home_team_key, mr.away_team_key)
    JOIN dim_seasons s ON mr.season_key = s.season_key
    JOIN dim_date    d ON mr.date_key   = d.date_key
),
with_lag AS (
    SELECT
        *,
        LAG(result, 1) OVER (PARTITION BY team_name, year ORDER BY round) AS prev_1,
        LAG(result, 2) OVER (PARTITION BY team_name, year ORDER BY round) AS prev_2,
        LAG(result, 3) OVER (PARTITION BY team_name, year ORDER BY round) AS prev_3,
        LAG(result, 4) OVER (PARTITION BY team_name, year ORDER BY round) AS prev_4,
        LAG(result, 5) OVER (PARTITION BY team_name, year ORDER BY round) AS prev_5,
        SUM(CASE WHEN result = 'W' THEN 1 ELSE 0 END)
            OVER (PARTITION BY team_name, year ORDER BY round
                  ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS wins_last_5,
        team_score - opp_score AS margin
    FROM match_outcomes
)
SELECT
    team_name,
    year,
    round,
    result,
    margin,
    wins_last_5,
    COALESCE(prev_5,'') || COALESCE(prev_4,'') || COALESCE(prev_3,'')
        || COALESCE(prev_2,'') || COALESCE(prev_1,'') || result AS form_string
FROM with_lag
ORDER BY team_name, year, round;
