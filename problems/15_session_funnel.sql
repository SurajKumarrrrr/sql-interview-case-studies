-- Problem: Monthly conversion funnel
-- Concepts: session-level flags with conditional MAX, funnel ratios
-- Task: Per month, count sessions, sessions with an add_to_cart, sessions with a
--       purchase, and the view->cart and cart->purchase conversion rates.
WITH sessions AS (
    SELECT session_id,
           CAST(date_trunc('month', MIN(event_date)) AS DATE)            AS month,
           MAX(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END)  AS has_cart,
           MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END)     AS has_purchase
    FROM events
    GROUP BY session_id
)
SELECT month,
       COUNT(*)                                          AS sessions,
       SUM(has_cart)                                     AS cart_sessions,
       SUM(has_purchase)                                 AS purchase_sessions,
       ROUND(100.0 * SUM(has_cart) / COUNT(*), 1)        AS view_to_cart_pct,
       ROUND(100.0 * SUM(has_purchase) / SUM(has_cart), 1) AS cart_to_purchase_pct
FROM sessions
GROUP BY month
ORDER BY month;
