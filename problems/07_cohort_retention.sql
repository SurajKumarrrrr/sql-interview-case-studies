-- Problem: Monthly cohort retention
-- Concepts: cohort analysis, month arithmetic, conditional aggregation
-- Task: Group customers by the month of their first paid order. For each cohort
--       up to July 2026, return cohort size and the % of the cohort that placed a
--       paid order 1, 2 and 3 months later.
WITH paid AS (
    SELECT DISTINCT customer_id, CAST(date_trunc('month', order_date) AS DATE) AS month
    FROM orders
    WHERE status = 'paid'
),
cohorts AS (
    SELECT customer_id, MIN(month) AS cohort_month
    FROM paid
    GROUP BY customer_id
),
activity AS (
    SELECT c.cohort_month,
           p.customer_id,
           CAST((EXTRACT(YEAR FROM p.month) - EXTRACT(YEAR FROM c.cohort_month)) * 12
                + EXTRACT(MONTH FROM p.month) - EXTRACT(MONTH FROM c.cohort_month) AS INTEGER) AS month_offset
    FROM paid p
    JOIN cohorts c ON c.customer_id = p.customer_id
)
SELECT cohort_month,
       COUNT(DISTINCT customer_id) AS cohort_size,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN month_offset = 1 THEN customer_id END)
             / COUNT(DISTINCT customer_id), 1) AS m1_pct,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN month_offset = 2 THEN customer_id END)
             / COUNT(DISTINCT customer_id), 1) AS m2_pct,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN month_offset = 3 THEN customer_id END)
             / COUNT(DISTINCT customer_id), 1) AS m3_pct
FROM activity
WHERE cohort_month <= DATE '2026-07-01'
GROUP BY cohort_month
ORDER BY cohort_month;
