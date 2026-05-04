-- Venue win rates and scoring analysis

-- Home team win rate by venue
WITH venue_results AS (
    SELECT
        v.venue_name,
        COUNT(*)                                              AS total_matches,
        SUM(CASE WHEN mr.winning_team_key = mr.home_team_key THEN 1 ELSE 0 END) AS home_wins,
        SUM(CASE WHEN mr.winning_team_key = mr.away_team_key THEN 1 ELSE 0 END) AS away_wins,
        SUM(CASE WHEN mr.winning_team_key IS NULL THEN 1 ELSE 0 END)            AS draws,
        ROUND(AVG(mr.home_total_score), 1)                   AS avg_home_score,
        ROUND(AVG(mr.away_total_score), 1)                   AS avg_away_score,
        ROUND(AVG(mr.home_total_score + mr.away_total_score), 1) AS avg_total_score,
        ROUND(AVG(mr.margin), 1)                             AS avg_margin
    FROM fact_match_results mr
    JOIN dim_venues v ON mr.venue_key = v.venue_key
    GROUP BY v.venue_key
    HAVING COUNT(*) >= 10
)
SELECT
    venue_name,
    total_matches,
    home_wins,
    away_wins,
    draws,
    ROUND(100.0 * home_wins / total_matches, 1) AS home_win_pct,
    avg_home_score,
    avg_away_score,
    avg_total_score,
    avg_margin
FROM venue_results
ORDER BY total_matches DESC;


-- Scoring output at the three Melbourne venues (for ANOVA input)
SELECT
    v.venue_name,
    s.year,
    mr.round,
    mr.home_total_score + mr.away_total_score AS total_score
FROM fact_match_results mr
JOIN dim_venues  v ON mr.venue_key  = v.venue_key
JOIN dim_seasons s ON mr.season_key = s.season_key
WHERE v.venue_name IN ('MCG', 'Marvel Stadium', 'GMHBA Stadium')
ORDER BY v.venue_name, s.year, mr.round;
