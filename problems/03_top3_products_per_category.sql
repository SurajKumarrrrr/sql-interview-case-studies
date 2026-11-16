-- Problem: Top 3 products per category
-- Concepts: PARTITION BY, DENSE_RANK, "top N per group"
-- Task: For each category, return the 3 best-selling products by paid revenue.
WITH product_revenue AS (
    SELECT p.category,
           p.product_id,
           p.name,
           SUM(oi.quantity)                 AS units_sold,
           SUM(oi.quantity * oi.unit_price) AS revenue
    FROM order_items oi
    JOIN orders o   ON o.order_id = oi.order_id AND o.status = 'paid'
    JOIN products p ON p.product_id = oi.product_id
    GROUP BY p.category, p.product_id, p.name
),
ranked AS (
    SELECT *, DENSE_RANK() OVER (PARTITION BY category ORDER BY revenue DESC) AS rnk
    FROM product_revenue
)
SELECT category, rnk, product_id, name, units_sold, revenue
FROM ranked
WHERE rnk <= 3
ORDER BY category, rnk, product_id;
