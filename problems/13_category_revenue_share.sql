-- Problem: Revenue share per category
-- Concepts: window over the whole result (SUM() OVER ()), percent of total
-- Task: Paid revenue per category and its share of total revenue.
WITH category_revenue AS (
    SELECT p.category, SUM(oi.quantity * oi.unit_price) AS revenue
    FROM order_items oi
    JOIN orders o   ON o.order_id = oi.order_id AND o.status = 'paid'
    JOIN products p ON p.product_id = oi.product_id
    GROUP BY p.category
)
SELECT category,
       revenue,
       ROUND(100.0 * revenue / SUM(revenue) OVER (), 1) AS share_pct
FROM category_revenue
ORDER BY revenue DESC, category;
