import json
import pandas as pd

# Service hours displayed in chronological night order
SERVICE_HOURS = list(range(22, 24)) + list(range(0, 7))
DAY_ORDER = ["Pátek", "Sobota", "Neděle"]
_DAY_MAP = {4: "Pátek", 5: "Sobota", 6: "Neděle"}


def explode_items(orders_df: pd.DataFrame) -> pd.DataFrame:
    """Expand JSONB items into one row per ordered product."""
    rows = []
    for _, order in orders_df.iterrows():
        items = order["items"]
        if isinstance(items, str):
            try:
                items = json.loads(items)
            except Exception:
                continue
        if not items:
            continue
        for item in items:
            rows.append(
                {
                    "order_id": order["id"],
                    "created_at": order["created_at"],
                    "order_status": order["status"],
                    "product_id": item.get("id"),
                    "product_name": item.get("name", ""),
                    "price": int(item.get("price", 0)),
                    "quantity": int(item.get("quantity", 1)),
                }
            )
    if not rows:
        return pd.DataFrame(
            columns=[
                "order_id",
                "created_at",
                "order_status",
                "product_id",
                "product_name",
                "price",
                "quantity",
            ]
        )
    df = pd.DataFrame(rows)
    df["revenue"] = df["price"] * df["quantity"]
    return df


def daily_revenue(orders_df: pd.DataFrame) -> pd.DataFrame:
    done = orders_df[orders_df["status"] == "doručená"].copy()
    if done.empty:
        return pd.DataFrame(columns=["date", "revenue"])
    done["date"] = done["created_at"].dt.date
    return done.groupby("date")["total"].sum().reset_index(name="revenue")


def hourly_heatmap(orders_df: pd.DataFrame) -> pd.DataFrame:
    """Return pivot: rows = day name, columns = hour (22→23→0→6)."""
    df = orders_df.copy()
    df["hour"] = df["created_at"].dt.hour
    df["dow"] = df["created_at"].dt.dayofweek
    df["day_name"] = df["dow"].map(_DAY_MAP)
    df = df.dropna(subset=["day_name"])
    df = df[df["hour"].isin(SERVICE_HOURS)]

    counts = df.groupby(["day_name", "hour"]).size().reset_index(name="count")
    pivot = counts.pivot(index="day_name", columns="hour", values="count").fillna(0)

    # Reindex to ensure all service hours and day order present
    pivot = pivot.reindex(index=DAY_ORDER, columns=SERVICE_HOURS, fill_value=0)
    return pivot


def top_products(items_df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N products by quantity sold (delivered orders only)."""
    done = items_df[items_df["order_status"] == "doručená"]
    if done.empty:
        return pd.DataFrame(columns=["product_name", "quantity", "revenue"])
    return (
        done.groupby("product_name")
        .agg(quantity=("quantity", "sum"), revenue=("revenue", "sum"))
        .sort_values("quantity", ascending=False)
        .head(n)
        .reset_index()
    )
