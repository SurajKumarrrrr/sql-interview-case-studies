-- Problem: High-value customers at churn risk
-- Concepts: HAVING, date arithmetic against a reference date
-- Task: Customers with 2+ paid orders whose last paid order is more than 90
--       days before 2026-10-31. Return the 20 most valuable of them.
WITH per_customer AS (
    SELECT o.customer_id,
           COUNT(DISTINCT o.order_id)       AS paid_orders,
           MAX(o.order_date)                AS last_order_date,
           SUM(oi.quantity * oi.unit_price) AS lifetime_revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status = 'paid'
    GROUP BY o.customer_id
    HAVING COUNT(DISTINCT o.order_id) >= 2
)
SELECT customer_id,
       paid_orders,
       last_order_date,
       DATE '2026-10-31' - last_order_date AS days_since_last_order,
       lifetime_revenue
FROM per_customer
WHERE last_order_date < DATE '2026-10-31' - 90
ORDER BY lifetime_revenue DESC, customer_id
LIMIT 20;
