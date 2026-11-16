-- Problem: Reconcile payments against order totals
-- Concepts: aggregating two child tables separately (avoiding fan-out), LEFT JOIN, data quality
-- Task: List paid orders where the sum of payments differs from the order total,
--       including paid orders with no payment at all. Largest differences first.
WITH totals AS (
    SELECT order_id, SUM(quantity * unit_price) AS order_total
    FROM order_items
    GROUP BY order_id
),
paid_amounts AS (
    SELECT order_id, SUM(amount) AS paid_amount
    FROM payments
    GROUP BY order_id
)
SELECT o.order_id,
       t.order_total,
       COALESCE(p.paid_amount, 0)                 AS paid_amount,
       t.order_total - COALESCE(p.paid_amount, 0) AS difference
FROM orders o
JOIN totals t            ON t.order_id = o.order_id
LEFT JOIN paid_amounts p ON p.order_id = o.order_id
WHERE o.status = 'paid'
  AND t.order_total <> COALESCE(p.paid_amount, 0)
ORDER BY ABS(t.order_total - COALESCE(p.paid_amount, 0)) DESC, o.order_id;
