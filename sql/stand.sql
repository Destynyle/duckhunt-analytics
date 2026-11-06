-- Public demo at the student fair: runs per game, completion and scores.
SELECT
    game,
    COUNT(*)                                    AS runs,
    COUNT(finished_at)                          AS finished_runs,
    ROUND(AVG(score), 1)                        AS avg_score,
    MAX(score)                                  AS best_score
FROM stand_runs
GROUP BY game
ORDER BY game;
