import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
import pandas as pd
import plotly.express as px
from rapidfuzz import fuzz, process

from src.etl.load import load_products
from src.etl.clean import clean_products
from src.config import TARGET_MARGIN, FUZZY_CUTOFF

st.set_page_config(page_title="Marže & Ceník – VečerkaPlus", page_icon="💰", layout="wide")
st.title("💰 Marže & Ceník")

TARGET_PCT = int(TARGET_MARGIN * 100)


@st.cache_data(ttl=300)
def get_products() -> pd.DataFrame:
    return clean_products(load_products())


try:
    products_df = get_products()
except Exception as e:
    st.error(f"Chyba při načítání produktů: {e}")
    st.stop()

# ── Upload Makro CSV ──────────────────────────────────────────────────────────
st.subheader("1. Nahrát ceník Makro")
st.caption("CSV musí obsahovat sloupce: `name`, `buy_price_per_unit`, `pack_size`, `pack_price`")

default_csv_path = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "makro_sample.csv"
)

uploaded = st.file_uploader("Nahrát CSV", type=["csv"])

if uploaded is not None:
    makro_df = pd.read_csv(uploaded)
elif os.path.exists(default_csv_path):
    makro_df = pd.read_csv(default_csv_path)
    st.info("Používám ukázkový soubor `data/makro_sample.csv`.")
else:
    st.warning("Nahrajte CSV s nákupními cenami z Makra.")
    st.stop()

required_cols = {"name", "buy_price_per_unit"}
missing = required_cols - set(makro_df.columns)
if missing:
    st.error(f"CSV postrádá sloupce: {missing}")
    st.stop()

makro_df["buy_price_per_unit"] = pd.to_numeric(
    makro_df["buy_price_per_unit"], errors="coerce"
)
makro_df = makro_df.dropna(subset=["buy_price_per_unit"])

if products_df.empty:
    st.warning("Žádné produkty v databázi.")
    st.stop()

# ── Fuzzy matching ────────────────────────────────────────────────────────────
st.subheader("2. Párování produktů (fuzzy)")

product_names = products_df["name"].tolist()


def match_product(makro_name: str) -> tuple[str | None, float]:
    result = process.extractOne(
        makro_name, product_names, scorer=fuzz.token_sort_ratio
    )
    if result and result[1] >= FUZZY_CUTOFF:
        return result[0], result[1]
    return None, 0.0


matched_rows = []
for _, row in makro_df.iterrows():
    matched_name, score = match_product(str(row["name"]))
    if matched_name:
        prod = products_df[products_df["name"] == matched_name].iloc[0]
        sell_price = int(prod["price"])
        buy_price = float(row["buy_price_per_unit"])
        margin = (sell_price - buy_price) / sell_price if sell_price > 0 else 0
        rec_price = int(buy_price / (1 - TARGET_MARGIN)) + 1 if buy_price > 0 else sell_price

        matched_rows.append(
            {
                "Produkt (DB)": matched_name,
                "Makro název": row["name"],
                "Shoda (%)": round(score, 1),
                "Nákupní cena (Kč)": round(buy_price, 2),
                "Prodejní cena (Kč)": sell_price,
                "Marže (%)": round(margin * 100, 1),
                "Doporučená cena (Kč)": rec_price,
                "Pod cílem": margin < TARGET_MARGIN,
            }
        )

if not matched_rows:
    st.warning(
        f"Žádné produkty nespárovány (cutoff={FUZZY_CUTOFF}). Zkontrolujte názvy v CSV."
    )
    st.stop()

result_df = pd.DataFrame(matched_rows)

matched_count = len(result_df)
below_target = result_df["Pod cílem"].sum()
avg_margin = result_df["Marže (%)"].mean()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Spárováno produktů", matched_count)
c2.metric("Pod cílovou marží", f"{below_target} ks")
c3.metric("Průměrná marže", f"{avg_margin:.1f} %")
c4.metric(f"Cílová marže", f"{TARGET_PCT} %")

st.divider()

# ── Margin chart ──────────────────────────────────────────────────────────────
st.subheader("3. Marže dle produktu")

chart_df = result_df.sort_values("Marže (%)")
fig = px.bar(
    chart_df,
    x="Marže (%)",
    y="Produkt (DB)",
    orientation="h",
    color="Pod cílem",
    color_discrete_map={True: "#EF5350", False: "#66BB6A"},
    labels={"Produkt (DB)": ""},
)
fig.add_vline(
    x=TARGET_PCT,
    line_dash="dash",
    line_color="orange",
    annotation_text=f"Cíl {TARGET_PCT}%",
    annotation_position="top right",
)
fig.update_layout(margin=dict(t=20), height=max(300, len(chart_df) * 28))
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Recommendations table ─────────────────────────────────────────────────────
st.subheader("4. Doporučení ceníku")

display_df = result_df.drop(columns=["Pod cílem"])


def highlight_below(row: pd.Series) -> list[str]:
    color = "background-color: #FFEBEE" if row["Marže (%)"] < TARGET_PCT else ""
    return [color] * len(row)


styled = display_df.style.apply(highlight_below, axis=1).format(
    {"Nákupní cena (Kč)": "{:.2f}", "Marže (%)": "{:.1f}"}
)

st.dataframe(styled, use_container_width=True, hide_index=True)
st.caption(f"Červené řádky = marže pod cílem {TARGET_PCT} %")
