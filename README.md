# SQL Interview Case Studies: E-commerce on PostgreSQL

![CI](https://github.com/SurajKumarrrrr/sql-interview-case-studies/actions/workflows/ci.yml/badge.svg)

15 business questions answered in SQL on a realistic e-commerce schema. They cover window functions, CTEs, cohort retention, gaps and islands, funnels and data reconciliation. **Every solution is automatically checked against an independent pandas implementation, on both PostgreSQL 16 and DuckDB.**

## Problem

Interview SQL rounds and day-to-day analytics work ask the same kinds of questions: *"Top N per group"*, *"month-over-month growth"*, *"which customers are about to churn"*, *"do payments match orders?"*. A query that runs isn't necessarily correct. Fan-out joins, ties, missing days and rounding all produce answers that look plausible but are wrong. This repo answers each question in clean, portable SQL and **proves** the answer is right.

## Approach

```mermaid
flowchart LR
    G[generate.py<br/>seeded data] --> CSV[(data/*.csv)]
    CSV --> PG[(PostgreSQL 16)]
    CSV --> DD[(DuckDB)]
    SQL[problems/NN_*.sql] --> PG
    SQL --> DD
    CSV --> REF[pandas reference<br/>tests/reference.py]
    PG --> CMP{results equal?}
    DD --> CMP
    REF --> CMP
```

- **Schema:** `customers`, `products`, `orders`, `order_items`, `payments`, `events`, with primary keys, foreign keys and CHECK constraints. See [`sql/schema.sql`](sql/schema.sql).
- **Data:** a deterministic generator (seed 7) for one year, Nov 2025 to Oct 2026. It produces 600 customers, 2,007 orders, 5,074 order lines, 2,121 payments and 13,950 web events. Its realistic quirks are deliberate: one-off vs heavy buyers, cancellations and refunds, split payments, 61 paid orders whose payments don't add up, and multi-day activity streaks.
- **Portable SQL:** every file runs unchanged on PostgreSQL and DuckDB. Each starts with a header giving the problem, the concepts it uses and the task.
- **Verification:** `tests/reference.py` solves all 15 problems again in pandas, using different logic. CI runs the SQL on a real PostgreSQL 16 service container and on DuckDB, and compares the results row by row.

## The problems

| # | Problem | Key concepts |
|---|---|---|
| 01 | Monthly revenue + MoM growth | CTE, `date_trunc`, `LAG` |
| 02 | Top 10 customers by lifetime value | `RANK`, ties |
| 03 | Top 3 products per category | `DENSE_RANK() OVER (PARTITION BY …)` |
| 04 | Running total of daily revenue | cumulative `SUM` with explicit frame |
| 05 | 7-day moving average incl. zero days | date spine with `generate_series`, `LEFT JOIN` |
| 06 | Repeat purchase rate | aggregate of aggregates |
| 07 | Monthly cohort retention | cohort month, month offsets, conditional `COUNT DISTINCT` |
| 08 | Days between orders per country | `LAG` per customer, `percentile_cont` |
| 09 | High-value customers at churn risk | `HAVING`, reference-date arithmetic |
| 10 | Longest activity streak | gaps and islands (`date − ROW_NUMBER`) |
| 11 | Payment reconciliation | avoiding join fan-out, `LEFT JOIN`, data quality |
| 12 | Average vs median order value | `percentile_cont … WITHIN GROUP` |
| 13 | Revenue share per category | `SUM() OVER ()` |
| 14 | Second-highest order per customer | `ROW_NUMBER` vs `DENSE_RANK`, tie-breaking |
| 15 | Monthly conversion funnel | session flags with conditional `MAX` |

## Results

These are actual outputs (`make run`). The data is **synthetic**, so the numbers show what the queries do, not real business facts. For example, the strong revenue growth comes from how the generator spreads customers' first orders across the year.

- **Repeat purchase rate:** 335 of 452 buyers (**74.1 %**) placed two or more paid orders.
- **Revenue share:** Electronics 43.6 %, Sports 28.4 %, Home 15.8 %, Fashion 5.3 %, Grocery 4.6 %, Books 2.3 %.
- **Average vs median order value:** the mean is above the median in every country. In Germany it's €417.36 vs €351.56 across 1,060 orders, and in Poland €391.43 vs €261.47. Skewed baskets make the mean misleading.
- **Payment reconciliation:** finds **61** problem orders. 27 paid orders have no payment at all, and 34 are underpaid. Getting this right needs payments and order lines aggregated *separately*: joining both to `orders` first double-counts split payments.
- **Gaps and islands:** the longest activity streak is 25 consecutive days (customer 572, 6–30 Dec 2025).
- **Speed:** every query runs in under 20 ms on both engines.

## How to run

```bash
make install        # Python deps + the `sqlcases` CLI
make test           # 21 tests on DuckDB; set PG_DSN to also run them on Postgres (36 tests)
sqlcases list
sqlcases run 07     # run one problem (by number or name, e.g. `sqlcases run cohort`)
make run            # run all 15 on DuckDB, nothing to install
```

With PostgreSQL in Docker:

```bash
make db-up          # postgres:16 with schema + data preloaded
psql postgresql://postgres:postgres@localhost:5432/shop -f problems/10_longest_activity_streak.sql
make run-pg         # all problems on Postgres
```

## Project structure

```
sql/schema.sql            DDL with PK/FK/CHECK constraints
data/*.csv                bundled dataset (regenerate with `sqlcases generate`)
problems/NN_*.sql         15 documented solutions
src/sqlcases/             generator, DB loaders (DuckDB / Postgres COPY), CLI
tests/reference.py        independent pandas solutions
tests/test_solutions.py   SQL == reference, per engine
docker-compose.yml        Postgres 16 with init scripts
```

## What I'd do next

- Add `EXPLAIN ANALYZE` notes and indexes for the heavier queries on a scaled-up dataset (10M order lines).
- Add more problems: sessionisation from raw click timestamps, SCD2 lookups, recursive CTEs for category trees.
- Port the same questions to BigQuery and Snowflake dialects to show where SQL stops being portable.

## Interview notes

- **Fan-out:** in problem 11, joining `order_items` and `payments` to `orders` at the same time multiplies rows (2 lines × 2 payments = 4 rows), which inflates both sums. Aggregate each child table in its own CTE, then join.
- **`ROW_NUMBER` vs `RANK` vs `DENSE_RANK`:** pick based on how ties should behave. Problem 02 lets tied customers share a rank. Problem 14 needs exactly one row, so it uses `ROW_NUMBER` with an explicit tie-breaker.
- **Missing days:** a 7-day average over only the days that had sales is wrong. Problem 05 builds a calendar with `generate_series` and `LEFT JOIN`s onto it.
- **Gaps and islands:** consecutive dates minus their row number give the same value, so grouping by that difference finds each streak in one pass.
- **Testing SQL:** comparing against an independent implementation caught real bugs while building this, for example rounding (SQL rounds half-up, Python rounds half-to-even) and tie order in sorts.
