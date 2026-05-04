-- Scoring trends by season
-- Tracks whether league-wide scoring is going up or down over time,
-- and which teams are the highest/lowest scorers each year

-- League-wide average score per season
SELECT
    s.year,
    COUNT(*)                                      AS matches,
    ROUND(AVG(mr.home_total_score), 1)            AS avg_home_score,
    ROUND(AVG(mr.away_total_score), 1)            AS avg_away_score,
    ROUND(AVG(mr.home_total_score + mr.away_total_score), 1) AS avg_total_score,
    ROUND(AVG(mr.margin), 1)                      AS avg_margin,
    MIN(mr.home_total_score + mr.away_total_score) AS lowest_scoring_game,
    MAX(mr.home_total_score + mr.away_total_score) AS highest_scoring_game
FROM fact_match_results mr
JOIN dim_seasons s ON mr.season_key = s.season_key
WHERE mr.home_total_score IS NOT NULL
GROUP BY s.year
ORDER BY s.year;
