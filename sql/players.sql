-- One row per piscine player, no login: players are anonymised before leaving SQL.
-- Lifeguards (anyone who validated an oral) and older students who tested the game
-- are excluded: piscine accounts are the ones created by the intra for this piscine
-- (intra_id >= :min_intra_id).
WITH lifeguards AS (
    SELECT DISTINCT oral_lifeguard AS login
    FROM players
    WHERE oral_lifeguard IS NOT NULL
)
SELECT
    printf('P%02d', ROW_NUMBER() OVER (ORDER BY created_at))  AS player,
    stage,
    riddle_attempts,
    exam_attempts,
    created_at       / 1000.0 AS started,
    riddle_solved_at / 1000.0 AS riddle_done,
    game_done_at     / 1000.0 AS game_done,
    exam_solved_at   / 1000.0 AS exam_done,
    oral_done_at     / 1000.0 AS oral_done,
    memory_done_at   / 1000.0 AS memory_done,
    finished_at      / 1000.0 AS finished
FROM players
WHERE intra_id >= :min_intra_id
  AND login NOT IN (SELECT login FROM lifeguards)
ORDER BY created_at;
