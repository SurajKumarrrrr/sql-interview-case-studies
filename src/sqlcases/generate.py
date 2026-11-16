"""Deterministic generator for the e-commerce dataset in data/*.csv.

The data covers 2025-11-01 to 2026-10-31 and contains the patterns the
case studies need: heavy and one-off buyers, cancellations and refunds,
split payments, a few payment mismatches, and multi-day activity streaks.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

START = date(2025, 11, 1)
END = date(2026, 10, 31)
N_DAYS = (END - START).days + 1

COUNTRIES = ["DE", "AT", "CH", "NL", "FR", "PL"]
COUNTRY_P = [0.55, 0.12, 0.10, 0.10, 0.08, 0.05]
CATEGORIES = {
    "Electronics": (40, 400),
    "Books": (8, 40),
    "Home": (15, 150),
    "Sports": (20, 200),
    "Fashion": (15, 120),
    "Grocery": (2, 25),
}
FIRST = ["Anna", "Lukas", "Mia", "Leon", "Emma", "Paul", "Lena", "Jonas", "Sofia", "Felix", "Priya", "Arjun"]
LAST = ["Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Kumar", "Hoffmann"]


def _day(rng: np.random.Generator, lo: int = 0) -> date:
    return START + timedelta(days=int(rng.integers(lo, N_DAYS)))


def build(seed: int = 7, n_customers: int = 600, n_products: int = 60) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)

    customers = pd.DataFrame(
        {
            "customer_id": np.arange(1, n_customers + 1),
            "name": [f"{rng.choice(FIRST)} {rng.choice(LAST)}" for _ in range(n_customers)],
            "country": rng.choice(COUNTRIES, size=n_customers, p=COUNTRY_P),
            "signup_date": [_day(rng) - timedelta(days=int(rng.integers(0, 365))) for _ in range(n_customers)],
        }
    )
    customers["email"] = [f"customer{i}@example.com" for i in customers["customer_id"]]
    customers = customers[["customer_id", "name", "email", "country", "signup_date"]]

    cats = list(CATEGORIES)
    prod_cat = [cats[i % len(cats)] for i in range(n_products)]
    products = pd.DataFrame(
        {
            "product_id": np.arange(1, n_products + 1),
            "name": [f"{c} item {i + 1}" for i, c in enumerate(prod_cat)],
            "category": prod_cat,
            "unit_price": [round(float(rng.uniform(*CATEGORIES[c])), 2) for c in prod_cat],
        }
    )
    # popularity is skewed: a few products sell a lot
    popularity = rng.pareto(1.5, n_products) + 0.1
    popularity /= popularity.sum()

    # buyer intensity: most customers order once or twice, a few order often
    intensity = rng.choice([0, 1, 2, 4, 8, 15], size=n_customers, p=[0.10, 0.30, 0.25, 0.18, 0.12, 0.05])
    orders, items, payments = [], [], []
    order_id = payment_id = 0
    for cid, k in zip(customers["customer_id"], intensity, strict=True):
        n_orders = int(rng.poisson(k)) if k else 0
        first_day = int(rng.integers(0, N_DAYS))
        for _ in range(n_orders):
            order_id += 1
            d = START + timedelta(days=int(rng.integers(first_day, N_DAYS)))
            status = str(rng.choice(["paid", "cancelled", "refunded"], p=[0.90, 0.06, 0.04]))
            orders.append((order_id, int(cid), d, status))
            total = 0.0
            for line in range(1, int(rng.integers(1, 5)) + 1):
                pid = int(rng.choice(n_products, p=popularity)) + 1
                qty = int(rng.choice([1, 1, 1, 2, 3]))
                price = float(products.at[pid - 1, "unit_price"])
                items.append((order_id, line, pid, qty, price))
                total += qty * price
            total = round(total, 2)
            if status != "paid":
                continue
            method = str(rng.choice(["card", "paypal", "klarna", "sepa"]))
            r = rng.random()
            if r < 0.02:  # data-quality issue: payment does not match the order
                payment_id += 1
                payments.append((payment_id, order_id, round(total - float(rng.integers(1, 30)), 2), d, method))
            elif r < 0.03:  # data-quality issue: paid order without any payment
                pass
            elif r < 0.23:  # split payment (voucher + card)
                first = round(total * 0.3, 2)
                payment_id += 1
                payments.append((payment_id, order_id, first, d, "voucher"))
                payment_id += 1
                payments.append((payment_id, order_id, round(total - first, 2), d, method))
            else:
                payment_id += 1
                payments.append((payment_id, order_id, total, d, method))

    # web sessions: view -> add_to_cart -> purchase funnel, plus activity streaks
    events = []
    event_id = session_id = 0
    for cid in customers["customer_id"]:
        n_streaks = int(rng.integers(1, 6))
        for _ in range(n_streaks):
            start = int(rng.integers(0, N_DAYS - 20))
            length = int(rng.choice([1, 1, 2, 3, 4, 6, 9, 14]))
            for offset in range(length):
                session_id += 1
                d = START + timedelta(days=start + offset)
                funnel = ["view"]
                if rng.random() < 0.35:
                    funnel.append("add_to_cart")
                    if rng.random() < 0.45:
                        funnel.append("purchase")
                for ev in funnel:
                    event_id += 1
                    events.append((event_id, session_id, int(cid), d, ev))

    return {
        "customers": customers,
        "products": products,
        "orders": pd.DataFrame(orders, columns=["order_id", "customer_id", "order_date", "status"]),
        "order_items": pd.DataFrame(items, columns=["order_id", "line_no", "product_id", "quantity", "unit_price"]),
        "payments": pd.DataFrame(payments, columns=["payment_id", "order_id", "amount", "paid_at", "method"]),
        "events": pd.DataFrame(events, columns=["event_id", "session_id", "customer_id", "event_date", "event_type"]),
    }


def write(out_dir: Path, seed: int = 7) -> dict[str, int]:
    """Write every table as CSV and return row counts."""
    out_dir.mkdir(parents=True, exist_ok=True)
    counts = {}
    for name, df in build(seed).items():
        df.to_csv(out_dir / f"{name}.csv", index=False, float_format="%.2f")
        counts[name] = len(df)
    return counts
