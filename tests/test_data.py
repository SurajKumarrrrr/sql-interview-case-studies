"""Integrity checks on the bundled dataset and the generator."""

import pandas as pd

from sqlcases.db import DATA, duckdb_connection, find_problem, run_sql
from sqlcases.generate import build


def test_bundled_csvs_match_generator():
    """data/*.csv must be exactly what `sqlcases generate` produces."""
    for name, df in build(seed=7).items():
        bundled = pd.read_csv(DATA / f"{name}.csv")
        fresh = pd.read_csv(pd.io.common.StringIO(df.to_csv(index=False, float_format="%.2f")))
        pd.testing.assert_frame_equal(bundled, fresh, check_dtype=False)


def test_foreign_keys_hold():
    con = duckdb_connection()  # loading enforces PK/FK/CHECK constraints
    orphans = run_sql(
        con,
        "SELECT count(*) AS n FROM order_items oi LEFT JOIN orders o USING (order_id) WHERE o.order_id IS NULL",
    )
    assert orphans["n"].iloc[0] == 0


def test_dataset_contains_the_data_quality_issues_problem_11_needs():
    con = duckdb_connection()
    df = run_sql(con, find_problem("11").read_text(encoding="utf-8"))
    assert (df["paid_amount"] == 0).any(), "expected paid orders without payments"
    assert (df["paid_amount"] > 0).any(), "expected underpaid orders"


def test_find_problem_by_number_and_name():
    assert find_problem("3").name.startswith("03_")
    assert find_problem("cohort").name.startswith("07_")
