-- Home vs away performance splits per team per season
-- Shows whether teams genuinely perform better at home

WITH team_games AS (
    SELECT
        t.team_name,
        s.year,
        'Home' AS venue_type,
        mr.home_total_score                        AS score,
        mr.away_total_score                        AS opp_score,
        CASE WHEN mr.winning_team_key = mr.home_team_key THEN 1 ELSE 0 END AS win
    FROM fact_match_results mr
    JOIN dim_teams   t ON mr.home_team_key = t.team_key
    JOIN dim_seasons s ON mr.season_key    = s.season_key
    WHERE mr.home_total_score IS NOT NULL

    UNION ALL

    SELECT
        t.team_name,
        s.year,
        'Away' AS venue_type,
        mr.away_total_score                        AS score,
        mr.home_total_score                        AS opp_score,
        CASE WHEN mr.winning_team_key = mr.away_team_key THEN 1 ELSE 0 END AS win
    FROM fact_match_results mr
    JOIN dim_teams   t ON mr.away_team_key = t.team_key
    JOIN dim_seasons s ON mr.season_key    = s.season_key
    WHERE mr.away_total_score IS NOT NULL
)
SELECT
    team_name,
    year,
    venue_type,
    COUNT(*)                          AS games,
    SUM(win)                          AS wins,
    ROUND(100.0 * SUM(win) / COUNT(*), 1) AS win_pct,
    ROUND(AVG(score), 1)              AS avg_score,
    ROUND(AVG(opp_score), 1)          AS avg_opp_score,
    ROUND(AVG(score - opp_score), 1)  AS avg_margin
FROM team_games
GROUP BY team_name, year, venue_type
ORDER BY team_name, year, venue_type;
