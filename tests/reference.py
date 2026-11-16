"""Independent pandas implementations of every problem.

Values are left unrounded; the test tolerance covers SQL ROUND().

Each SQL solution is checked against these, so a query that "runs" but
answers the wrong question fails the test suite.
"""

from __future__ import annotations

import pandas as pd

REF_DATE = pd.Timestamp("2026-10-31")


class Data:
    def __init__(self, tables: dict[str, pd.DataFrame]):
        self.t = tables
        o, oi = tables["orders"], tables["order_items"]
        oi = oi.assign(line_total=oi["quantity"] * oi["unit_price"])
        totals = oi.groupby("order_id", as_index=False)["line_total"].sum().rename(columns={"line_total": "total"})
        self.items = oi
        self.order_totals = o.merge(totals, on="order_id")
        self.paid = self.order_totals[self.order_totals["status"] == "paid"].copy()


def load(data_dir) -> Data:
    dates = {"customers": ["signup_date"], "orders": ["order_date"], "payments": ["paid_at"], "events": ["event_date"]}
    tables = {
        name: pd.read_csv(data_dir / f"{name}.csv", parse_dates=dates.get(name, False))
        for name in ["customers", "products", "orders", "order_items", "payments", "events"]
    }
    return Data(tables)


def _month(s: pd.Series) -> pd.Series:
    return s.dt.to_period("M").dt.to_timestamp()


def p01(d: Data) -> pd.DataFrame:
    p = d.paid.assign(month=_month(d.paid["order_date"]))
    m = p.groupby("month").agg(revenue=("total", "sum"), orders=("order_id", "count")).reset_index()
    prev = m["revenue"].shift()
    m["mom_growth_pct"] = (100 * (m["revenue"] - prev) / prev)
    return m


def p02(d: Data) -> pd.DataFrame:
    g = d.paid.groupby("customer_id").agg(paid_orders=("order_id", "nunique"), lifetime_revenue=("total", "sum"))
    g = g.reset_index().merge(d.t["customers"], on="customer_id")
    g["rnk"] = g["lifetime_revenue"].rank(method="min", ascending=False).astype(int)
    g = g[g["rnk"] <= 10].sort_values(["rnk", "customer_id"])
    return g[["rnk", "customer_id", "name", "country", "paid_orders", "lifetime_revenue"]]


def _paid_items(d: Data) -> pd.DataFrame:
    paid_ids = set(d.paid["order_id"])
    return d.items[d.items["order_id"].isin(paid_ids)].merge(
        d.t["products"][["product_id", "name", "category"]], on="product_id"
    )


def p03(d: Data) -> pd.DataFrame:
    g = (
        _paid_items(d)
        .groupby(["category", "product_id", "name"])
        .agg(units_sold=("quantity", "sum"), revenue=("line_total", "sum"))
        .reset_index()
    )
    g["rnk"] = g.groupby("category")["revenue"].rank(method="dense", ascending=False).astype(int)
    g = g[g["rnk"] <= 3].sort_values(["category", "rnk", "product_id"])
    return g[["category", "rnk", "product_id", "name", "units_sold", "revenue"]]


def _daily(d: Data) -> pd.Series:
    return d.paid.groupby("order_date")["total"].sum()


def p04(d: Data) -> pd.DataFrame:
    s = _daily(d)
    s = s[(s.index >= "2026-10-01") & (s.index <= "2026-10-31")]
    return pd.DataFrame({"day": s.index, "revenue": s.values, "running_total": s.cumsum().values})


def p05(d: Data) -> pd.DataFrame:
    days = pd.date_range("2026-10-01", "2026-10-31", freq="D")
    s = _daily(d).reindex(days, fill_value=0)
    return pd.DataFrame(
        {"day": days, "revenue": s.values, "moving_avg_7d": s.rolling(7, min_periods=1).mean().values}
    )


def p06(d: Data) -> pd.DataFrame:
    n = d.t["orders"].query("status == 'paid'").groupby("customer_id").size()
    rep = int((n >= 2).sum())
    return pd.DataFrame({"buyers": [len(n)], "repeat_buyers": [rep], "repeat_rate_pct": [100 * rep / len(n)]})


def p07(d: Data) -> pd.DataFrame:
    p = d.t["orders"].query("status == 'paid'")
    p = p.assign(month=_month(p["order_date"]))[["customer_id", "month"]].drop_duplicates()
    cohort = p.groupby("customer_id")["month"].min().rename("cohort_month")
    p = p.join(cohort, on="customer_id")
    years = p["month"].dt.year - p["cohort_month"].dt.year
    p["offset"] = years * 12 + p["month"].dt.month - p["cohort_month"].dt.month
    rows = []
    for cm, g in p.groupby("cohort_month"):
        if cm > pd.Timestamp("2026-07-01"):
            continue
        size = g["customer_id"].nunique()
        row = {"cohort_month": cm, "cohort_size": size}
        for k in (1, 2, 3):
            row[f"m{k}_pct"] = 100 * g.loc[g["offset"] == k, "customer_id"].nunique() / size
        rows.append(row)
    return pd.DataFrame(rows)


def p08(d: Data) -> pd.DataFrame:
    p = d.t["orders"].query("status == 'paid'").merge(d.t["customers"][["customer_id", "country"]], on="customer_id")
    p = p.sort_values(["customer_id", "order_date", "order_id"])
    p["gap"] = p.groupby("customer_id")["order_date"].diff().dt.days
    g = p.dropna(subset=["gap"]).groupby("country")
    out = pd.DataFrame(
        {
            "repeat_buyers": g["customer_id"].nunique(),
            "avg_gap_days": g["gap"].mean(),
            "median_gap_days": g["gap"].median(),
        }
    )
    return out.reset_index()


def p09(d: Data) -> pd.DataFrame:
    g = d.paid.groupby("customer_id").agg(
        paid_orders=("order_id", "nunique"), last_order_date=("order_date", "max"), lifetime_revenue=("total", "sum")
    )
    g = g[(g["paid_orders"] >= 2) & (g["last_order_date"] < REF_DATE - pd.Timedelta(days=90))].reset_index()
    g["days_since_last_order"] = (REF_DATE - g["last_order_date"]).dt.days
    g = g.sort_values(["lifetime_revenue", "customer_id"], ascending=[False, True]).head(20)
    return g[["customer_id", "paid_orders", "last_order_date", "days_since_last_order", "lifetime_revenue"]]


def p10(d: Data) -> pd.DataFrame:
    rows = []
    days = d.t["events"][["customer_id", "event_date"]].drop_duplicates().sort_values(["customer_id", "event_date"])
    for cid, g in days.groupby("customer_id"):
        dates = list(g["event_date"])
        best = cur_start = dates[0]
        best_len = cur_len = 1
        for prev, day in zip(dates, dates[1:], strict=False):
            if (day - prev).days == 1:
                cur_len += 1
            else:
                cur_start, cur_len = day, 1
            if cur_len > best_len:
                best, best_len = cur_start, cur_len
        rows.append((cid, best, best + pd.Timedelta(days=best_len - 1), best_len))
    df = pd.DataFrame(rows, columns=["customer_id", "streak_start", "streak_end", "streak_days"])
    return df.sort_values(["streak_days", "customer_id"], ascending=[False, True]).head(10)


def p11(d: Data) -> pd.DataFrame:
    paid_amt = d.t["payments"].groupby("order_id")["amount"].sum()
    p = d.paid[["order_id", "total"]].rename(columns={"total": "order_total"})
    p["paid_amount"] = p["order_id"].map(paid_amt).fillna(0)
    p["difference"] = (p["order_total"] - p["paid_amount"]).round(2)
    p = p[p["difference"].abs() > 0.005]  # ignore float noise; amounts are in cents
    p = p.assign(_abs=p["difference"].abs()).sort_values(["_abs", "order_id"], ascending=[False, True])
    return p[["order_id", "order_total", "paid_amount", "difference"]]


def p12(d: Data) -> pd.DataFrame:
    p = d.paid.merge(d.t["customers"][["customer_id", "country"]], on="customer_id")
    g = p.groupby("country")["total"]
    out = pd.DataFrame(
        {"paid_orders": g.size(), "avg_order_value": g.mean(), "median_order_value": g.median()}
    ).reset_index()
    return out.sort_values(["paid_orders", "country"], ascending=[False, True])


def p13(d: Data) -> pd.DataFrame:
    g = _paid_items(d).groupby("category")["line_total"].sum().rename("revenue").reset_index()
    g["share_pct"] = (100 * g["revenue"] / g["revenue"].sum())
    return g.sort_values(["revenue", "category"], ascending=[False, True])


def p14(d: Data) -> pd.DataFrame:
    p = d.paid.sort_values(["customer_id", "total", "order_id"], ascending=[True, False, True])
    p["rn"] = p.groupby("customer_id").cumcount() + 1
    p = p[p["rn"] == 2].rename(columns={"total": "second_highest_order"})
    return p[["customer_id", "order_id", "second_highest_order"]]


def p15(d: Data) -> pd.DataFrame:
    e = d.t["events"]
    s = e.groupby("session_id").agg(
        month=("event_date", "min"),
        has_cart=("event_type", lambda x: int((x == "add_to_cart").any())),
        has_purchase=("event_type", lambda x: int((x == "purchase").any())),
    )
    s["month"] = _month(s["month"])
    g = s.groupby("month").agg(
        sessions=("has_cart", "size"), cart_sessions=("has_cart", "sum"), purchase_sessions=("has_purchase", "sum")
    )
    g["view_to_cart_pct"] = (100 * g["cart_sessions"] / g["sessions"])
    g["cart_to_purchase_pct"] = (100 * g["purchase_sessions"] / g["cart_sessions"])
    return g.reset_index()


REFERENCES = {f"{i:02d}": globals()[f"p{i:02d}"] for i in range(1, 16)}
