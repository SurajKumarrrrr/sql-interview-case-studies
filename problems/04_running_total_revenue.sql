-- Problem: Running total of daily revenue in October 2026
-- Concepts: cumulative SUM window, explicit frame
-- Task: Daily paid revenue for October 2026 and the month-to-date running total.
WITH daily AS (
    SELECT o.order_date AS day, SUM(oi.quantity * oi.unit_price) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status = 'paid'
      AND o.order_date BETWEEN DATE '2026-10-01' AND DATE '2026-10-31'
    GROUP BY o.order_date
)
SELECT day,
       revenue,
       SUM(revenue) OVER (ORDER BY day ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
FROM daily
ORDER BY day;
