-- Problem: Time between consecutive orders per country
-- Concepts: LAG per customer, date subtraction, median with percentile_cont
-- Task: For repeat buyers, compute the gap in days between consecutive paid
--       orders. Return per country: repeat buyers, average and median gap.
WITH ordered AS (
    SELECT o.customer_id,
           c.country,
           o.order_date,
           LAG(o.order_date) OVER (PARTITION BY o.customer_id ORDER BY o.order_date, o.order_id) AS prev_date
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    WHERE o.status = 'paid'
),
gaps AS (
    SELECT customer_id, country, order_date - prev_date AS gap_days
    FROM ordered
    WHERE prev_date IS NOT NULL
)
SELECT country,
       COUNT(DISTINCT customer_id)                                                 AS repeat_buyers,
       ROUND(AVG(gap_days), 1)                                                    AS avg_gap_days,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY CAST(gap_days AS DOUBLE PRECISION)) AS median_gap_days
FROM gaps
GROUP BY country
ORDER BY country;
