import pandas as pd
from src.supabase_client import get_client


def load_products() -> pd.DataFrame:
    client = get_client()
    resp = client.table("products").select("*").execute()
    return pd.DataFrame(resp.data) if resp.data else pd.DataFrame()


def load_orders() -> pd.DataFrame:
    client = get_client()
    resp = client.table("orders").select("*").execute()
    return pd.DataFrame(resp.data) if resp.data else pd.DataFrame()
