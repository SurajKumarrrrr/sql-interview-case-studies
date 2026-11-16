-- E-commerce schema used by all case studies.
-- Written in portable SQL: runs unchanged on PostgreSQL 16 and DuckDB.

CREATE TABLE customers (
    customer_id  INTEGER PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    email        VARCHAR(200) NOT NULL UNIQUE,
    country      CHAR(2)      NOT NULL,
    signup_date  DATE         NOT NULL
);

CREATE TABLE products (
    product_id  INTEGER PRIMARY KEY,
    name        VARCHAR(100)   NOT NULL,
    category    VARCHAR(50)    NOT NULL,
    unit_price  DECIMAL(10, 2) NOT NULL CHECK (unit_price > 0)
);

CREATE TABLE orders (
    order_id     INTEGER PRIMARY KEY,
    customer_id  INTEGER     NOT NULL REFERENCES customers (customer_id),
    order_date   DATE        NOT NULL,
    status       VARCHAR(20) NOT NULL CHECK (status IN ('paid', 'cancelled', 'refunded'))
);

CREATE TABLE order_items (
    order_id    INTEGER        NOT NULL REFERENCES orders (order_id),
    line_no     INTEGER        NOT NULL,
    product_id  INTEGER        NOT NULL REFERENCES products (product_id),
    quantity    INTEGER        NOT NULL CHECK (quantity > 0),
    unit_price  DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (order_id, line_no)
);

CREATE TABLE payments (
    payment_id  INTEGER PRIMARY KEY,
    order_id    INTEGER        NOT NULL REFERENCES orders (order_id),
    amount      DECIMAL(10, 2) NOT NULL,
    paid_at     DATE           NOT NULL,
    method      VARCHAR(20)    NOT NULL
);

CREATE TABLE events (
    event_id     INTEGER PRIMARY KEY,
    session_id   INTEGER     NOT NULL,
    customer_id  INTEGER     NOT NULL REFERENCES customers (customer_id),
    event_date   DATE        NOT NULL,
    event_type   VARCHAR(20) NOT NULL CHECK (event_type IN ('view', 'add_to_cart', 'purchase'))
);
