import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.etl.load import load_products, load_orders
from src.etl.clean import clean_products, clean_orders
from src.etl.transform import explode_items, daily_revenue, hourly_heatmap, top_products, SERVICE_HOURS, DAY_ORDER
from src.etl.demo_data import generate_demo_orders

st.set_page_config(page_title="Objednávky – VečerkaPlus", page_icon=":shopping_trolley:", layout="wide")
st.title("Objednávky")

# ── Data source toggle ────────────────────────────────────────────────────────
use_demo = st.sidebar.toggle("Demo data (150 syntetických objednávek)", value=False)


@st.cache_data(ttl=300)
def get_products_cached() -> pd.DataFrame:
    return clean_products(load_products())


@st.cache_data(ttl=300)
def get_real_orders() -> pd.DataFrame:
    return clean_orders(load_orders())


@st.cache_data(ttl=3600)
def get_demo_orders(products_hash: str) -> pd.DataFrame:
    # products_hash is used as cache key so demo regenerates if products change
    try:
        products_df = get_products_cached()
    except Exception:
        products_df = pd.DataFrame()
    raw = generate_demo_orders(products_df)
    return clean_orders(raw)


try:
    products_df = get_products_cached()
    products_hash = str(len(products_df))
except Exception:
    products_df = pd.DataFrame()
    products_hash = "0"

if use_demo:
    orders_df = get_demo_orders(products_hash)
    st.sidebar.info("Zobrazuji 150 syntetických objednávek.")
else:
    try:
        orders_df = get_real_orders()
    except Exception as e:
        st.error(f"Chyba při načítání objednávek: {e}")
        st.stop()

if orders_df.empty:
    st.warning(
        "Žádné objednávky. Zapněte **Demo data** v postranním panelu nebo přidejte reálná data."
    )
    st.stop()

items_df = explode_items(orders_df)

# ── KPI cards ────────────────────────────────────────────────────────────────
total_orders = len(orders_df)
completed = orders_df[orders_df["status"] == "doručená"]
cancelled = orders_df[orders_df["status"] == "zrušená"]
total_revenue = int(completed["total"].sum())
avg_order = int(completed["total"].mean()) if not completed.empty else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Objednávky celkem", total_orders)
c2.metric("Doručené", len(completed))
c3.metric("Zrušené", len(cancelled))
c4.metric("Tržby celkem", f"{total_revenue:,} Kč".replace(",", " "))
c5.metric("Průměrná objednávka", f"{avg_order} Kč")

st.divider()

# ── Daily revenue line ────────────────────────────────────────────────────────
st.subheader("Denní tržby (doručené objednávky)")
daily_df = daily_revenue(orders_df)
if not daily_df.empty:
    fig_line = px.line(
        daily_df,
        x="date",
        y="revenue",
        labels={"date": "Datum", "revenue": "Tržby (Kč)"},
        markers=True,
        color_discrete_sequence=["#1976D2"],
    )
    fig_line.update_layout(margin=dict(t=20))
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("Nedostatek dat pro denní tržby.")

st.divider()

# ── Hourly heatmap ────────────────────────────────────────────────────────────
st.subheader("Heatmapa objednávek (den × hodina)")

pivot = hourly_heatmap(orders_df)
if not pivot.empty and pivot.values.sum() > 0:
    hour_labels = [f"{h:02d}:00" for h in SERVICE_HOURS]
    fig_heat = go.Figure(
        go.Heatmap(
            z=pivot.values.tolist(),
            x=hour_labels,
            y=pivot.index.tolist(),
            colorscale="Blues",
            text=pivot.values.tolist(),
            texttemplate="%{text:.0f}",
            showscale=True,
            hovertemplate="Den: %{y}<br>Hodina: %{x}<br>Objednávky: %{z}<extra></extra>",
        )
    )
    fig_heat.update_layout(
        xaxis_title="Hodina",
        yaxis_title="Den",
        yaxis=dict(categoryorder="array", categoryarray=list(reversed(DAY_ORDER))),
        margin=dict(t=20),
        height=250,
    )
    st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("Nedostatek dat pro heatmapu (potřebná data z Pá/So/Ne 22–6).")

st.divider()

# ── Payment donut ─────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Způsob platby")
    pay_counts = orders_df["payment"].value_counts().reset_index()
    pay_counts.columns = ["Platba", "Počet"]
    fig_pie = px.pie(
        pay_counts,
        names="Platba",
        values="Počet",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_pie.update_layout(margin=dict(t=20))
    st.plotly_chart(fig_pie, use_container_width=True)

# ── Top products bar ──────────────────────────────────────────────────────────
with col_right:
    st.subheader("Top 10 produktů (ks)")
    top_df = top_products(items_df)
    if not top_df.empty:
        fig_top = px.bar(
            top_df,
            x="quantity",
            y="product_name",
            orientation="h",
            labels={"quantity": "Prodáno (ks)", "product_name": ""},
            color_discrete_sequence=["#43A047"],
        )
        fig_top.update_layout(
            yaxis=dict(autorange="reversed"),
            margin=dict(t=20),
        )
        st.plotly_chart(fig_top, use_container_width=True)
    else:
        st.info("Žádná data o produktech.")

st.divider()

# ── Market basket analysis ────────────────────────────────────────────────────
st.subheader("Analýza košíku (Apriori)")
st.caption("min_support = 0.10, zobrazeny pravidla s lift > 1")

try:
    from mlxtend.frequent_patterns import apriori, association_rules
    from mlxtend.preprocessing import TransactionEncoder

    delivered_items = items_df[items_df["order_status"] == "doručená"]

    if delivered_items.empty:
        st.info("Nedostatek dat pro analýzu košíku.")
    else:
        transactions = (
            delivered_items.groupby("order_id")["product_name"].apply(list).tolist()
        )

        if len(transactions) < 10:
            st.info(f"Příliš málo transakcí ({len(transactions)}) pro apriori analýzu.")
        else:
            te = TransactionEncoder()
            te_array = te.fit_transform(transactions)
            basket_df = pd.DataFrame(te_array, columns=te.columns_)

            freq_itemsets = apriori(
                basket_df, min_support=0.10, use_colnames=True, max_len=3
            )

            if freq_itemsets.empty:
                st.info("Žádné časté položky při min_support=0.10. Zkuste více objednávek.")
            else:
                rules = association_rules(
                    freq_itemsets,
                    num_itemsets=len(basket_df),
                    metric="confidence",
                    min_threshold=0.25,
                )
                rules = rules[rules["lift"] > 1.0]
                rules = rules.sort_values("lift", ascending=False)

                rules["antecedents"] = rules["antecedents"].apply(
                    lambda x: ", ".join(list(x))
                )
                rules["consequents"] = rules["consequents"].apply(
                    lambda x: ", ".join(list(x))
                )

                display_rules = rules[
                    ["antecedents", "consequents", "support", "confidence", "lift"]
                ].rename(
                    columns={
                        "antecedents": "Pokud zákazník koupí",
                        "consequents": "Pak pravděpodobně koupí",
                        "support": "Support",
                        "confidence": "Confidence",
                        "lift": "Lift",
                    }
                )

                st.dataframe(
                    display_rules.style.format(
                        {
                            "Support": "{:.2%}",
                            "Confidence": "{:.2%}",
                            "Lift": "{:.2f}",
                        }
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

                st.caption(
                    f"Celkem {len(freq_itemsets)} častých kombinací, "
                    f"{len(rules)} asociačních pravidel."
                )

except ImportError:
    st.warning("mlxtend není nainstalován. Spusťte: `pip install mlxtend`")
except Exception as e:
    st.error(f"Chyba při analýze košíku: {e}")

st.divider()

# ── Raw orders table ──────────────────────────────────────────────────────────
with st.expander("Zobrazit všechny objednávky"):
    show_cols = [c for c in ["created_at", "name", "address", "payment", "total", "status"] if c in orders_df.columns]
    col_labels = {
        "created_at": "Čas",
        "name": "Zákazník",
        "address": "Adresa",
        "payment": "Platba",
        "total": "Celkem (Kč)",
        "status": "Stav",
    }
    st.dataframe(
        orders_df[show_cols].rename(columns=col_labels).reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )
