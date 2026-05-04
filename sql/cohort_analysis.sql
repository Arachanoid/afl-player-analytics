-- Player debut cohort analysis
-- Groups players by the year they first appeared in the data
-- and tracks aggregate career stats across subsequent seasons

WITH player_debut AS (
    SELECT
        player_key,
        MIN(s.year) AS debut_year
    FROM fact_player_match_stats f
    JOIN dim_seasons s ON f.season_key = s.season_key
    GROUP BY player_key
),
career_stats AS (
    SELECT
        f.player_key,
        p.player_name,
        s.year,
        COUNT(*)                             AS games,
        ROUND(AVG(f.disposals), 1)           AS avg_disposals,
        ROUND(AVG(f.goals), 2)               AS avg_goals,
        ROUND(AVG(f.brownlow_votes), 2)      AS avg_brownlow,
        SUM(f.brownlow_votes)                AS total_brownlow,
        s.year - d.debut_year                AS years_since_debut
    FROM fact_player_match_stats f
    JOIN dim_players  p ON f.player_key  = p.player_key
    JOIN dim_seasons  s ON f.season_key  = s.season_key
    JOIN player_debut d ON f.player_key  = d.player_key
    GROUP BY f.player_key, s.season_key
)
SELECT
    debut_year,
    years_since_debut,
    COUNT(DISTINCT player_key)    AS active_players,
    ROUND(AVG(games), 1)          AS avg_games_per_season,
    ROUND(AVG(avg_disposals), 1)  AS cohort_avg_disposals,
    ROUND(AVG(avg_goals), 2)      AS cohort_avg_goals,
    ROUND(AVG(avg_brownlow), 2)   AS cohort_avg_brownlow
FROM career_stats
GROUP BY debut_year, years_since_debut
ORDER BY debut_year, years_since_debut;
