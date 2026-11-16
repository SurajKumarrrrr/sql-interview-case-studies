-- Problem: Repeat purchase rate
-- Concepts: aggregation of aggregates, conditional counting
-- Task: Of all customers with at least one paid order, how many placed two or
--       more paid orders, and what percentage is that?
WITH per_customer AS (
    SELECT customer_id, COUNT(*) AS paid_orders
    FROM orders
    WHERE status = 'paid'
    GROUP BY customer_id
)
SELECT COUNT(*)                                                       AS buyers,
       SUM(CASE WHEN paid_orders >= 2 THEN 1 ELSE 0 END)              AS repeat_buyers,
       ROUND(100.0 * SUM(CASE WHEN paid_orders >= 2 THEN 1 ELSE 0 END) / COUNT(*), 1) AS repeat_rate_pct
FROM per_customer;
