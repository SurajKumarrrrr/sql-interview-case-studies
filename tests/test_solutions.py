"""Every SQL solution must match the independent pandas reference.

Runs on DuckDB always, and on PostgreSQL too when PG_DSN is set (as in CI).
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pytest
from reference import REFERENCES, load

from sqlcases.db import DATA, duckdb_connection, postgres_connection, problem_files, run_sql

ENGINES = ["duckdb"] + (["postgres"] if os.environ.get("PG_DSN") else [])


@pytest.fixture(scope="session")
def ref_data():
    return load(DATA)


@pytest.fixture(scope="session", params=ENGINES)
def con(request):
    if request.param == "postgres":
        c = postgres_connection(os.environ["PG_DSN"])
    else:
        c = duckdb_connection()
    yield c
    c.close()


def _normalise(df: pd.DataFrame) -> pd.DataFrame:
    """Make results from DuckDB, PostgreSQL and pandas comparable."""
    out = df.reset_index(drop=True).copy()
    for col in out.columns:
        s = out[col]
        if pd.api.types.is_datetime64_any_dtype(s):
            out[col] = s.dt.strftime("%Y-%m-%d")
        elif s.dtype == object and len(s.dropna()) and hasattr(s.dropna().iloc[0], "isoformat"):
            out[col] = pd.to_datetime(s).dt.strftime("%Y-%m-%d")
        else:
            try:
                out[col] = pd.to_numeric(s).astype(float)
            except (ValueError, TypeError):
                out[col] = s.astype(str)
    return out


def assert_same(actual: pd.DataFrame, expected: pd.DataFrame) -> None:
    a, e = _normalise(actual), _normalise(expected)
    assert list(a.columns) == list(e.columns)
    assert len(a) == len(e), f"row count {len(a)} != {len(e)}"
    for col in a.columns:
        if a[col].dtype == float:
            # references are unrounded; SQL rounds to <= 1 decimal, so allow 0.05 (+ float noise)
            np.testing.assert_allclose(a[col], e[col], atol=0.051, rtol=1e-9, err_msg=col, equal_nan=True)
        else:
            assert a[col].tolist() == e[col].tolist(), col


@pytest.mark.parametrize("path", problem_files(), ids=lambda p: p.stem)
def test_solution_matches_reference(path, con, ref_data):
    actual = run_sql(con, path.read_text(encoding="utf-8"))
    expected = REFERENCES[path.stem[:2]](ref_data)
    assert len(actual) > 0
    assert_same(actual, expected)


def test_every_problem_has_a_reference():
    assert {p.stem[:2] for p in problem_files()} == set(REFERENCES)


def test_every_problem_documents_itself():
    for p in problem_files():
        head = p.read_text(encoding="utf-8").splitlines()[:5]
        assert any(line.startswith("-- Problem:") for line in head), p.name
        assert any(line.startswith("-- Task:") for line in head), p.name
