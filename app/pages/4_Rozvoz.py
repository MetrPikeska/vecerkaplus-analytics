import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.etl.load import load_orders
from src.etl.clean import clean_orders
from src.etl.distance import get_distance_km, delivery_cost
from src.config import (
    DEFAULT_FUEL_L_PER_100KM,
    DEFAULT_FUEL_PRICE_CZK,
    GOOGLE_MAPS_API_KEY,
)

st.set_page_config(
    page_title="Rozvoz – VečerkaPlus",
    page_icon=":car:",
    layout="wide",
)
st.title("Rozvoz — vzdálenosti a náklady")

if not GOOGLE_MAPS_API_KEY:
    st.error("Chybí GOOGLE_MAPS_API_KEY v .env")
    st.stop()

# ── Nastavení ─────────────────────────────────────────────────────────────────
with st.expander("Nastavení vozidla a paliva", expanded=True):
    c1, c2, c3 = st.columns(3)
    fuel_consumption = c1.number_input(
        "Spotřeba (l / 100 km)", min_value=3.0, max_value=20.0,
        value=DEFAULT_FUEL_L_PER_100KM, step=0.5, format="%.1f"
    )
    fuel_price = c2.number_input(
        "Cena paliva (Kč / l)", min_value=20.0, max_value=80.0,
        value=DEFAULT_FUEL_PRICE_CZK, step=0.5, format="%.1f"
    )
    round_trip = c3.toggle("Počítat zpáteční cestu (2×)", value=True)

trip_mult = 2 if round_trip else 1

# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def _get_orders() -> pd.DataFrame:
    return clean_orders(load_orders())


try:
    orders_df = _get_orders()
except Exception as e:
    st.error(f"Chyba při načítání objednávek: {e}")
    st.stop()

if orders_df.empty:
    st.warning("Žádné objednávky v databázi.")
    st.stop()

# Filtr — jen doručené nebo všechny
status_filter = st.multiselect(
    "Stav objednávek",
    options=["nová", "přijatá", "doručená", "zrušená"],
    default=["doručená"],
)
filtered_df = orders_df[orders_df["status"].isin(status_filter)].copy() if status_filter else orders_df.copy()

if filtered_df.empty:
    st.info("Žádné objednávky pro vybraný filtr.")
    st.stop()

# ── Výpočet vzdáleností ───────────────────────────────────────────────────────
st.subheader("Výpočet vzdáleností")

addresses = filtered_df["address"].dropna().unique().tolist()
total_unique = len(addresses)

progress_bar = st.progress(0, text="Načítám vzdálenosti...")
distance_map: dict[str, float | None] = {}

for i, addr in enumerate(addresses):
    distance_map[addr] = get_distance_km(addr)
    progress_bar.progress((i + 1) / total_unique, text=f"Vzdálenosti: {i+1}/{total_unique}")

progress_bar.empty()

# Přiřadit vzdálenosti objednávkám
filtered_df["km_one_way"] = filtered_df["address"].map(distance_map)
filtered_df["km_total"] = filtered_df["km_one_way"] * trip_mult
filtered_df["naklady_rozvoz"] = filtered_df["km_total"].apply(
    lambda km: delivery_cost(km, fuel_consumption, fuel_price) if pd.notna(km) else None
)
filtered_df["zisk_po_rozvozu"] = filtered_df["total"] - filtered_df["naklady_rozvoz"].fillna(0)

# Počet neúspěšných lookupů
failed = filtered_df["km_one_way"].isna().sum()
if failed > 0:
    st.warning(f"{failed} adres se nepodařilo dohledat přes Google Maps.")

valid_df = filtered_df.dropna(subset=["km_one_way"])

# ── KPI ───────────────────────────────────────────────────────────────────────
if not valid_df.empty:
    total_km = round(valid_df["km_total"].sum(), 1)
    avg_km = round(valid_df["km_one_way"].mean(), 1)
    total_fuel_cost = round(valid_df["naklady_rozvoz"].sum(), 0)
    avg_fuel_cost = round(valid_df["naklady_rozvoz"].mean(), 1)
    total_revenue = int(valid_df["total"].sum())
    total_profit = round(valid_df["zisk_po_rozvozu"].sum(), 0)

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Objednávek", len(valid_df))
    k2.metric("Celkem km", f"{total_km} km")
    k3.metric("Prům. vzdálenost", f"{avg_km} km")
    k4.metric("Náklady na rozvoz", f"{int(total_fuel_cost):,} Kč".replace(",", " "))
    k5.metric("Zisk po rozvozu", f"{int(total_profit):,} Kč".replace(",", " "))

    st.divider()

    # ── Grafy ─────────────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Tržby vs. náklady na rozvoz")
        chart_df = valid_df.sort_values("created_at").copy()
        chart_df["label"] = chart_df["created_at"].dt.strftime("%d.%m %H:%M") + " — " + chart_df["name"]
        fig = go.Figure()
        fig.add_bar(
            x=chart_df["label"], y=chart_df["total"],
            name="Tržby", marker_color="#29B6F6"
        )
        fig.add_bar(
            x=chart_df["label"], y=chart_df["naklady_rozvoz"],
            name="Náklady rozvoz", marker_color="#FF3D9A"
        )
        fig.update_layout(
            barmode="overlay",
            xaxis_tickangle=-45,
            legend=dict(orientation="h"),
            margin=dict(t=20, b=120),
            height=380,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.subheader("Zisk po odečtení rozvozu")
        profit_df = valid_df.copy()
        profit_df["label"] = profit_df["created_at"].dt.strftime("%d.%m %H:%M") + " — " + profit_df["name"]
        profit_df = profit_df.sort_values("zisk_po_rozvozu")
        colors = ["#e05555" if v < 0 else "#5bc4a0" for v in profit_df["zisk_po_rozvozu"]]
        fig2 = px.bar(
            profit_df, x="zisk_po_rozvozu", y="label",
            orientation="h",
            labels={"zisk_po_rozvozu": "Zisk (Kč)", "label": ""},
            color_discrete_sequence=["#5bc4a0"],
        )
        fig2.update_traces(marker_color=colors)
        fig2.add_vline(x=0, line_color="white", line_dash="dash", line_width=1)
        fig2.update_layout(margin=dict(t=20), height=380)
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ── Tabulka ───────────────────────────────────────────────────────────────
    st.subheader("Detail objednávek")

    table = valid_df[[
        "created_at", "name", "address", "total",
        "km_one_way", "km_total", "naklady_rozvoz", "zisk_po_rozvozu", "status"
    ]].copy()
    table["created_at"] = table["created_at"].dt.strftime("%d.%m.%Y %H:%M")
    table = table.rename(columns={
        "created_at": "Čas",
        "name": "Zákazník",
        "address": "Adresa",
        "total": "Tržba (Kč)",
        "km_one_way": "Vzdál. (km)",
        "km_total": f"Km celkem ({'2×' if round_trip else '1×'})",
        "naklady_rozvoz": "Náklady rozvoz (Kč)",
        "zisk_po_rozvozu": "Zisk po rozvozu (Kč)",
        "status": "Stav",
    })

    def _color_profit(val):
        try:
            return "color: #e05555" if float(val) < 0 else "color: #5bc4a0"
        except Exception:
            return ""

    styled = table.style.map(_color_profit, subset=["Zisk po rozvozu (Kč)"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    cost_per_km = round(fuel_consumption / 100 * fuel_price, 2)
    st.caption(
        f"Náklady: {fuel_consumption} l/100km × {fuel_price} Kč/l = **{cost_per_km} Kč/km** | "
        f"{'Zpáteční cesta (2×)' if round_trip else 'Pouze cesta tam (1×)'}"
    )
