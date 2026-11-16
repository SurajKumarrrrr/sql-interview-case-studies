-- Bulk-load the bundled CSVs (runs once, on first container start).
\copy customers   FROM '/data/customers.csv'   WITH (FORMAT csv, HEADER true)
\copy products    FROM '/data/products.csv'    WITH (FORMAT csv, HEADER true)
\copy orders      FROM '/data/orders.csv'      WITH (FORMAT csv, HEADER true)
\copy order_items FROM '/data/order_items.csv' WITH (FORMAT csv, HEADER true)
\copy payments    FROM '/data/payments.csv'    WITH (FORMAT csv, HEADER true)
\copy events      FROM '/data/events.csv'      WITH (FORMAT csv, HEADER true)
ANALYZE;
