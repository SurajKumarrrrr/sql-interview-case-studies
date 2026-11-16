"""Load the schema + CSVs into DuckDB or PostgreSQL and run problem files."""

from __future__ import annotations

import re
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "sql" / "schema.sql"
DATA = ROOT / "data"
PROBLEMS = ROOT / "problems"
# load order respects foreign keys
TABLES = ["customers", "products", "orders", "order_items", "payments", "events"]


def problem_files() -> list[Path]:
    return sorted(PROBLEMS.glob("[0-9][0-9]_*.sql"))


def find_problem(key: str) -> Path:
    """Find a problem by number ('3', '03') or name fragment ('cohort')."""
    for p in problem_files():
        if p.name.startswith(f"{int(key):02d}_") if key.isdigit() else key in p.stem:
            return p
    raise FileNotFoundError(f"No problem matches {key!r}")


def problem_title(path: Path) -> str:
    m = re.search(r"--\s*Problem:\s*(.+)", path.read_text(encoding="utf-8"))
    return m.group(1).strip() if m else path.stem


def duckdb_connection(data_dir: Path = DATA) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(SCHEMA.read_text(encoding="utf-8"))
    for t in TABLES:
        con.execute(f"COPY {t} FROM '{(data_dir / f'{t}.csv').as_posix()}' (HEADER)")
    return con


def postgres_connection(dsn: str, data_dir: Path = DATA):
    """Create a fresh schema in PostgreSQL and bulk-load the CSVs with COPY."""
    import psycopg2

    con = psycopg2.connect(dsn)
    con.autocommit = True
    with con.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS shop CASCADE; CREATE SCHEMA shop; SET search_path TO shop;")
        cur.execute(SCHEMA.read_text(encoding="utf-8"))
        for t in TABLES:
            with open(data_dir / f"{t}.csv", encoding="utf-8") as f:
                cur.copy_expert(f"COPY {t} FROM STDIN WITH (FORMAT csv, HEADER true)", f)
    return con


def run_sql(con, sql: str) -> pd.DataFrame:
    """Run a query on either engine and return a DataFrame."""
    if isinstance(con, duckdb.DuckDBPyConnection):
        return con.execute(sql).df()
    with con.cursor() as cur:
        cur.execute(sql)
        cols = [d[0] for d in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=cols)
