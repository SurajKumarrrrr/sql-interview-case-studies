-- Problem: Average vs median order value by country
-- Concepts: ordered-set aggregate percentile_cont, why the median matters with skewed data
-- Task: Per country, number of paid orders, average and median order value.
WITH order_totals AS (
    SELECT o.order_id, c.country, SUM(oi.quantity * oi.unit_price) AS total
    FROM orders o
    JOIN customers c    ON c.customer_id = o.customer_id
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status = 'paid'
    GROUP BY o.order_id, c.country
)
SELECT country,
       COUNT(*)                AS paid_orders,
       ROUND(AVG(total), 2)    AS avg_order_value,
       ROUND(CAST(percentile_cont(0.5) WITHIN GROUP (ORDER BY CAST(total AS DOUBLE PRECISION)) AS NUMERIC), 2)
                               AS median_order_value
FROM order_totals
GROUP BY country
ORDER BY paid_orders DESC, country;
