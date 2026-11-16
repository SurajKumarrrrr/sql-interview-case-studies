"""CLI: list problems, run one (or all) against DuckDB or PostgreSQL, regenerate data."""

from __future__ import annotations

import argparse
import os
import time

import pandas as pd

from .db import DATA, duckdb_connection, find_problem, postgres_connection, problem_files, problem_title, run_sql
from .generate import write


def _connect(engine: str):
    if engine == "postgres":
        dsn = os.environ.get("PG_DSN", "postgresql://postgres:postgres@localhost:5432/postgres")
        return postgres_connection(dsn)
    return duckdb_connection()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="sqlcases")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list all problems")
    r = sub.add_parser("run", help="run one problem, or 'all'")
    r.add_argument("problem", help="number, name fragment or 'all'")
    r.add_argument("--engine", choices=["duckdb", "postgres"], default="duckdb")
    r.add_argument("--rows", type=int, default=15)
    g = sub.add_parser("generate", help="regenerate data/*.csv")
    g.add_argument("--seed", type=int, default=7)
    args = parser.parse_args(argv)

    if args.cmd == "list":
        for p in problem_files():
            print(f"{p.stem[:2]}  {problem_title(p)}")
    elif args.cmd == "generate":
        for table, n in write(DATA, args.seed).items():
            print(f"{table:12s} {n:>6d} rows")
    elif args.cmd == "run":
        con = _connect(args.engine)
        paths = problem_files() if args.problem == "all" else [find_problem(args.problem)]
        pd.set_option("display.width", 140)
        for p in paths:
            t0 = time.perf_counter()
            df = run_sql(con, p.read_text(encoding="utf-8"))
            ms = (time.perf_counter() - t0) * 1000
            print(f"\n## {p.stem}: {problem_title(p)}  ({len(df)} rows, {ms:.0f} ms on {args.engine})\n")
            print(df.head(args.rows).to_string(index=False))


if __name__ == "__main__":
    main()
