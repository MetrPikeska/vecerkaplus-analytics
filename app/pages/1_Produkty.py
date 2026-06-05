import sys
import os
from html import escape

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
import plotly.express as px
import pandas as pd

from src.etl.load import load_products
from src.etl.clean import clean_products

st.set_page_config(page_title="Produkty – VečerkaPlus", page_icon=":package:", layout="wide")
st.title("Produkty")


st.markdown(
    """
    <style>
      .product-card {
        min-height: 276px;
        padding: 12px;
        border: 1px solid rgba(212, 175, 106, 0.18);
        border-radius: 12px;
        background: #14141c;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.04) inset;
      }

      .product-image-frame {
        height: 148px;
        margin-bottom: 12px;
        border-radius: 9px;
        background: #ededeb;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .product-image-frame img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        display: block;
      }

      .product-image-placeholder {
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #77726b;
        font-size: 0.82rem;
        letter-spacing: 0.01em;
      }

      .product-name {
        min-height: 2.45rem;
        color: #f1eee7;
        font-weight: 700;
        line-height: 1.2;
      }

      .product-category {
        margin-top: 6px;
        color: #b8b1a5;
        font-size: 0.86rem;
        font-style: italic;
      }

      .product-meta {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        margin-top: 12px;
      }

      .product-price {
        color: #f2d48a;
        font-weight: 800;
      }

      .stock-pill {
        white-space: nowrap;
        border-radius: 999px;
        padding: 3px 8px;
        font-size: 0.78rem;
        font-weight: 700;
        background: rgba(255, 255, 255, 0.07);
        color: #d8d4cc;
      }

      .stock-pill.low {
        background: rgba(212, 175, 106, 0.16);
        color: #f2d48a;
      }

      .stock-pill.out {
        background: rgba(239, 68, 68, 0.16);
        color: #fca5a5;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

PLACEHOLDER_IMAGE_HTML = (
    '<div class="product-image-frame"><div class="product-image-placeholder">bez foto</div></div>'
)


@st.cache_data(ttl=300)
def get_products() -> pd.DataFrame:
    return clean_products(load_products())


def render_product_image(img_url: object) -> str:
    """render a product image with a client-side fallback for broken URLs."""
    normalized_img_url = "" if pd.isna(img_url) else str(img_url).strip()

    if not normalized_img_url:
        return PLACEHOLDER_IMAGE_HTML

    safe_url = escape(normalized_img_url, quote=True)
    return f"""
        <div class="product-image-frame">
          <img
            src="{safe_url}"
            alt=""
            loading="lazy"
            referrerpolicy="no-referrer"
            onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"
          />
          <div class="product-image-placeholder" style="display:none">bez foto</div>
        </div>
    """


def render_product_card(product: pd.Series) -> None:
    """render a compact product card for the products grid."""
    stock = int(product.get("stock", 0))
    stock_label = "OK" if stock > 5 else ("nízký" if stock > 0 else "OUT")
    stock_class = "out" if stock <= 0 else ("low" if stock <= 5 else "")
    name = escape(str(product.get("name", "")))
    category = escape(str(product.get("category", "")))
    price = escape(str(product.get("price", "")))
    image_html = render_product_image(product.get("img", ""))

    st.markdown(
        f"""
        <div class="product-card">
          {image_html}
          <div class="product-name">{name}</div>
          <div class="product-category">{category}</div>
          <div class="product-meta">
            <div class="product-price">{price} Kč</div>
            <div class="stock-pill {stock_class}">{stock_label} {stock} ks</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
    COLS = 5
    rows = [filtered.iloc[i : i + COLS] for i in range(0, len(filtered), COLS)]
    for row_df in rows:
        cols = st.columns(COLS)
        for col, (_, product) in zip(cols, row_df.iterrows()):
            with col:
                render_product_card(product)

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
