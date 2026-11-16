-- Problem: Longest streak of consecutive active days (gaps and islands)
-- Concepts: date minus ROW_NUMBER trick, picking one row per group
-- Task: A customer is active on a day if they have any event. For each customer
--       find their longest run of consecutive active days, then return the 10
--       customers with the longest streaks (earliest streak wins ties).
WITH active_days AS (
    SELECT DISTINCT customer_id, event_date
    FROM events
),
islands AS (
    SELECT customer_id,
           event_date,
           event_date - CAST(ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY event_date) AS INTEGER) AS grp
    FROM active_days
),
streaks AS (
    SELECT customer_id, MIN(event_date) AS streak_start, MAX(event_date) AS streak_end, COUNT(*) AS streak_days
    FROM islands
    GROUP BY customer_id, grp
),
best AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY streak_days DESC, streak_start) AS rn
    FROM streaks
)
SELECT customer_id, streak_start, streak_end, streak_days
FROM best
WHERE rn = 1
ORDER BY streak_days DESC, customer_id
LIMIT 10;
