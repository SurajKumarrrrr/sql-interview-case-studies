-- Problem: Top 10 customers by lifetime value
-- Concepts: joins, aggregation, RANK
-- Task: Rank customers by total revenue from paid orders. Return the top 10
--       ranks (ties share a rank) with name, country, number of paid orders and revenue.
WITH ltv AS (
    SELECT c.customer_id,
           c.name,
           c.country,
           COUNT(DISTINCT o.order_id)        AS paid_orders,
           SUM(oi.quantity * oi.unit_price)  AS lifetime_revenue
    FROM customers c
    JOIN orders o       ON o.customer_id = c.customer_id AND o.status = 'paid'
    JOIN order_items oi ON oi.order_id = o.order_id
    GROUP BY c.customer_id, c.name, c.country
),
ranked AS (
    SELECT *, RANK() OVER (ORDER BY lifetime_revenue DESC) AS rnk
    FROM ltv
)
SELECT rnk, customer_id, name, country, paid_orders, lifetime_revenue
FROM ranked
WHERE rnk <= 10
ORDER BY rnk, customer_id;
