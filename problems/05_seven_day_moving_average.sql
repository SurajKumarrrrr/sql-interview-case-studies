-- Problem: 7-day moving average including days without sales
-- Concepts: date spine with generate_series, LEFT JOIN, moving-window AVG
-- Task: For every day of October 2026 (also days with zero revenue), return
--       paid revenue and the trailing 7-day moving average.
WITH calendar AS (
    SELECT CAST(d AS DATE) AS day
    FROM generate_series(TIMESTAMP '2026-10-01', TIMESTAMP '2026-10-31', INTERVAL '1 day') AS t (d)
),
daily AS (
    SELECT o.order_date AS day, SUM(oi.quantity * oi.unit_price) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status = 'paid'
    GROUP BY o.order_date
)
SELECT c.day,
       COALESCE(d.revenue, 0) AS revenue,
       ROUND(AVG(COALESCE(d.revenue, 0)) OVER (ORDER BY c.day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2)
           AS moving_avg_7d
FROM calendar c
LEFT JOIN daily d ON d.day = c.day
ORDER BY c.day;
