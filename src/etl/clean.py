import pandas as pd
from src.config import TIMEZONE


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0).astype(int)
    df["stock"] = pd.to_numeric(df["stock"], errors="coerce").fillna(0).astype(int)
    return df


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()

    # Drop test/zero-value orders
    df = df[pd.to_numeric(df["total"], errors="coerce").fillna(0) > 0]

    # Parse and localise timestamps
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce")
    df["created_at"] = df["created_at"].dt.tz_convert(TIMEZONE)
    df = df.dropna(subset=["created_at"])

    df["total"] = pd.to_numeric(df["total"], errors="coerce").fillna(0).astype(int)
    return df.reset_index(drop=True)
