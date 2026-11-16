-- Problem: Monthly revenue and month-over-month growth
-- Concepts: CTEs, date_trunc, LAG window function
-- Task: For paid orders, return revenue and order count per month, plus the
--       month-over-month revenue growth in percent (NULL for the first month).
WITH order_totals AS (
    SELECT o.order_id,
           CAST(date_trunc('month', o.order_date) AS DATE) AS month,
           SUM(oi.quantity * oi.unit_price)                AS total
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status = 'paid'
    GROUP BY o.order_id, CAST(date_trunc('month', o.order_date) AS DATE)
),
monthly AS (
    SELECT month, SUM(total) AS revenue, COUNT(*) AS orders
    FROM order_totals
    GROUP BY month
)
SELECT month,
       revenue,
       orders,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
             / LAG(revenue) OVER (ORDER BY month), 1) AS mom_growth_pct
FROM monthly
ORDER BY month;
