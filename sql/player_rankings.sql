-- Player rankings using window functions
-- Shows season averages ranked within each season

WITH season_averages AS (
    SELECT
        p.player_name,
        t.team_name,
        s.year,
        COUNT(*)                        AS games_played,
        ROUND(AVG(f.disposals), 1)      AS avg_disposals,
        ROUND(AVG(f.kicks), 1)          AS avg_kicks,
        ROUND(AVG(f.marks), 1)          AS avg_marks,
        ROUND(AVG(f.goals), 2)          AS avg_goals,
        ROUND(AVG(f.tackles), 1)        AS avg_tackles,
        ROUND(AVG(f.clearances), 1)     AS avg_clearances,
        ROUND(AVG(f.inside_50s), 1)     AS avg_inside_50s,
        ROUND(AVG(f.contested_possessions), 1) AS avg_contested_pos
    FROM fact_player_match_stats f
    JOIN dim_players p ON f.player_key  = p.player_key
    JOIN dim_teams   t ON f.team_key    = t.team_key
    JOIN dim_seasons s ON f.season_key  = s.season_key
    WHERE f.pct_game_played >= 50      -- only count games where player was on field >50%
    GROUP BY p.player_key, t.team_key, s.season_key
    HAVING COUNT(*) >= 10              -- minimum 10 games
),
ranked AS (
    SELECT
        *,
        RANK() OVER (PARTITION BY year ORDER BY avg_disposals DESC)  AS disposal_rank,
        RANK() OVER (PARTITION BY year ORDER BY avg_goals DESC)      AS goal_rank,
        RANK() OVER (PARTITION BY year ORDER BY avg_clearances DESC) AS clearance_rank,
        RANK() OVER (PARTITION BY year ORDER BY avg_tackles DESC)    AS tackle_rank
    FROM season_averages
)
SELECT * FROM ranked
ORDER BY year DESC, disposal_rank
LIMIT 100;
