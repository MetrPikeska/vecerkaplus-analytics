import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
import plotly.express as px
import pandas as pd

from src.etl.load import load_products
from src.etl.clean import clean_products

st.set_page_config(page_title="Produkty – VečerkaPlus", page_icon="📦", layout="wide")
st.title("📦 Produkty")


@st.cache_data(ttl=300)
def get_products() -> pd.DataFrame:
    return clean_products(load_products())


try:
    df = get_products()
except Exception as e:
    st.error(f"Chyba při načítání produktů: {e}")
    st.stop()

if df.empty:
    st.warning("Žádné produkty nenalezeny.")
    st.stop()

# ── KPI cards ────────────────────────────────────────────────────────────────
total_products = len(df)
total_categories = df["category"].nunique() if "category" in df.columns else 0
avg_price = int(df["price"].mean())
stock_value = int((df["price"] * df["stock"]).sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Počet produktů", total_products)
c2.metric("Kategorie", total_categories)
c3.metric("Průměrná cena", f"{avg_price} Kč")
c4.metric("Hodnota skladu", f"{stock_value:,} Kč".replace(",", " "))

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Produkty dle kategorie")
    cat_counts = df.groupby("category").size().reset_index(name="počet")
    fig_bar = px.bar(
        cat_counts,
        x="category",
        y="počet",
        color="category",
        labels={"category": "Kategorie", "počet": "Počet produktů"},
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_bar.update_layout(showlegend=False, margin=dict(t=20))
    st.plotly_chart(fig_bar, use_container_width=True)

with col_right:
    st.subheader("Distribuce cen")
    fig_hist = px.histogram(
        df,
        x="price",
        nbins=20,
        labels={"price": "Cena (Kč)"},
        color_discrete_sequence=["#2196F3"],
    )
    fig_hist.update_yaxes(title_text="Počet produktů")
    fig_hist.update_layout(margin=dict(t=20))
    st.plotly_chart(fig_hist, use_container_width=True)

st.divider()

# ── Filters ───────────────────────────────────────────────────────────────────
st.subheader("Přehled produktů")

fcol1, fcol2, fcol3 = st.columns([2, 2, 1])
with fcol1:
    categories = ["Vše"] + sorted(df["category"].dropna().unique().tolist())
    selected_cat = st.selectbox("Kategorie", categories)
with fcol2:
    min_price, max_price = int(df["price"].min()), int(df["price"].max())
    price_range = st.slider("Cena (Kč)", min_value=min_price, max_value=max_price, value=(min_price, max_price))
with fcol3:
    view = st.radio("Zobrazení", ["Karty", "Tabulka"], horizontal=True)

filtered = df if selected_cat == "Vše" else df[df["category"] == selected_cat]
filtered = filtered[
    (filtered["price"] >= price_range[0]) & (filtered["price"] <= price_range[1])
].reset_index(drop=True)

st.caption(f"{len(filtered)} produktů")

# ── Card view ─────────────────────────────────────────────────────────────────
if view == "Karty":
    COLS = 4
    rows = [filtered.iloc[i : i + COLS] for i in range(0, len(filtered), COLS)]
    for row_df in rows:
        cols = st.columns(COLS)
        for col, (_, product) in zip(cols, row_df.iterrows()):
            with col:
                img_url = product.get("img", "")
                if img_url:
                    st.image(img_url, use_container_width=True)
                else:
                    st.markdown(
                        "<div style='height:120px;background:#eee;border-radius:8px;display:flex;"
                        "align-items:center;justify-content:center;color:#aaa'>bez foto</div>",
                        unsafe_allow_html=True,
                    )
                stock = int(product.get("stock", 0))
                stock_color = "🟢" if stock > 5 else ("🟡" if stock > 0 else "🔴")
                st.markdown(
                    f"**{product['name']}**  \n"
                    f"*{product.get('category', '')}*  \n"
                    f"**{product['price']} Kč** &nbsp; {stock_color} {stock} ks",
                    unsafe_allow_html=False,
                )
                st.markdown("---")

# ── Table view ────────────────────────────────────────────────────────────────
else:
    display_cols = [c for c in ["name", "category", "price", "stock"] if c in filtered.columns]
    col_labels = {
        "name": "Název",
        "category": "Kategorie",
        "price": "Cena (Kč)",
        "stock": "Sklad (ks)",
    }
    st.dataframe(
        filtered[display_cols].rename(columns=col_labels),
        use_container_width=True,
        hide_index=True,
    )
