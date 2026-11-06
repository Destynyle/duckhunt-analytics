-- How many piscine players got past each trial.
-- A player counts for a trial if this trial or any later one has a timestamp:
-- one finisher has empty exam/oral columns (probably moved forward from /admin),
-- and should still count as having passed those trials.
WITH piscine AS (
    SELECT * FROM players
    WHERE intra_id >= :min_intra_id
      AND login NOT IN (SELECT oral_lifeguard FROM players WHERE oral_lifeguard IS NOT NULL)
)
SELECT 1 AS step, 'Started' AS trial, COUNT(*) AS players FROM piscine
UNION ALL SELECT 2, 'Riddle',      COUNT(COALESCE(riddle_solved_at, game_done_at, exam_solved_at, oral_done_at, memory_done_at, finished_at)) FROM piscine
UNION ALL SELECT 3, 'Logic game',  COUNT(COALESCE(game_done_at, exam_solved_at, oral_done_at, memory_done_at, finished_at)) FROM piscine
UNION ALL SELECT 4, 'C exam',      COUNT(COALESCE(exam_solved_at, oral_done_at, memory_done_at, finished_at)) FROM piscine
UNION ALL SELECT 5, 'Oral',        COUNT(COALESCE(oral_done_at, memory_done_at, finished_at)) FROM piscine
UNION ALL SELECT 6, 'Memory game', COUNT(COALESCE(memory_done_at, finished_at)) FROM piscine
UNION ALL SELECT 7, 'Finished',    COUNT(finished_at) FROM piscine
ORDER BY step;
