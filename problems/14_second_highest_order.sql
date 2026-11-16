-- Problem: Second-highest order per customer
-- Concepts: ROW_NUMBER vs DENSE_RANK, deterministic tie-breaking
-- Task: For every customer with at least two paid orders, return the value of
--       their second-largest paid order (ties broken by lower order_id first).
WITH order_totals AS (
    SELECT o.customer_id, o.order_id, SUM(oi.quantity * oi.unit_price) AS total
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status = 'paid'
    GROUP BY o.customer_id, o.order_id
),
ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY total DESC, order_id) AS rn
    FROM order_totals
)
SELECT customer_id, order_id, total AS second_highest_order
FROM ranked
WHERE rn = 2
ORDER BY customer_id;
