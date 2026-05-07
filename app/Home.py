import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime, timedelta
import pytz

from src.etl.load import load_products, load_orders
from src.etl.clean import clean_products, clean_orders
from src.config import TIMEZONE

st.set_page_config(
    page_title="VečerkaPlus Analytics",
    page_icon="🍺",
    layout="wide",
    initial_sidebar_state="expanded",
)

_TZ = pytz.timezone(TIMEZONE)

# ── Web Audio sounds (generated via JS, no files needed) ──────────────────────
_SOUNDS = {
    # nová — urgent ascending beep (new order!)
    "nová": """
(function() {
  var ctx = new (window.AudioContext || window.webkitAudioContext)();
  function beep(freq, start, dur, vol) {
    var o = ctx.createOscillator();
    var g = ctx.createGain();
    o.connect(g); g.connect(ctx.destination);
    o.type = 'sine';
    o.frequency.value = freq;
    g.gain.setValueAtTime(0, ctx.currentTime + start);
    g.gain.linearRampToValueAtTime(vol, ctx.currentTime + start + 0.01);
    g.gain.linearRampToValueAtTime(0, ctx.currentTime + start + dur);
    o.start(ctx.currentTime + start);
    o.stop(ctx.currentTime + start + dur + 0.05);
  }
  beep(660, 0.0, 0.12, 0.4);
  beep(880, 0.15, 0.12, 0.4);
  beep(1100, 0.30, 0.18, 0.5);
})();
""",
    # přijatá — double confirm beep
    "přijatá": """
(function() {
  var ctx = new (window.AudioContext || window.webkitAudioContext)();
  function beep(freq, start, dur, vol) {
    var o = ctx.createOscillator();
    var g = ctx.createGain();
    o.connect(g); g.connect(ctx.destination);
    o.type = 'sine';
    o.frequency.value = freq;
    g.gain.setValueAtTime(0, ctx.currentTime + start);
    g.gain.linearRampToValueAtTime(vol, ctx.currentTime + start + 0.01);
    g.gain.linearRampToValueAtTime(0, ctx.currentTime + start + dur);
    o.start(ctx.currentTime + start);
    o.stop(ctx.currentTime + start + dur + 0.05);
  }
  beep(880, 0.0, 0.10, 0.35);
  beep(880, 0.15, 0.10, 0.35);
})();
""",
    # doručená — pleasant success chime
    "doručená": """
(function() {
  var ctx = new (window.AudioContext || window.webkitAudioContext)();
  function beep(freq, start, dur, vol) {
    var o = ctx.createOscillator();
    var g = ctx.createGain();
    o.connect(g); g.connect(ctx.destination);
    o.type = 'sine';
    o.frequency.value = freq;
    g.gain.setValueAtTime(0, ctx.currentTime + start);
    g.gain.linearRampToValueAtTime(vol, ctx.currentTime + start + 0.01);
    g.gain.linearRampToValueAtTime(0, ctx.currentTime + start + dur);
    o.start(ctx.currentTime + start);
    o.stop(ctx.currentTime + start + dur + 0.05);
  }
  beep(523, 0.0,  0.10, 0.3);
  beep(659, 0.12, 0.10, 0.3);
  beep(784, 0.24, 0.20, 0.35);
})();
""",
    # zrušená — low descending buzz
    "zrušená": """
(function() {
  var ctx = new (window.AudioContext || window.webkitAudioContext)();
  function beep(freq, start, dur, vol) {
    var o = ctx.createOscillator();
    var g = ctx.createGain();
    o.connect(g); g.connect(ctx.destination);
    o.type = 'sawtooth';
    o.frequency.value = freq;
    g.gain.setValueAtTime(0, ctx.currentTime + start);
    g.gain.linearRampToValueAtTime(vol, ctx.currentTime + start + 0.01);
    g.gain.linearRampToValueAtTime(0, ctx.currentTime + start + dur);
    o.start(ctx.currentTime + start);
    o.stop(ctx.currentTime + start + dur + 0.05);
  }
  beep(300, 0.0,  0.18, 0.3);
  beep(200, 0.22, 0.22, 0.25);
})();
""",
}


def _play_sound(status: str) -> None:
    js = _SOUNDS.get(status, "")
    if js:
        components.html(f"<script>{js}</script>", height=0)


def _shift_status() -> tuple[bool, str]:
    now = datetime.now(_TZ)
    wd = now.weekday()
    h = now.hour
    friday_night = (wd == 4 and h >= 22) or (wd == 5 and h < 6)
    saturday_night = (wd == 5 and h >= 22) or (wd == 6 and h < 6)
    if friday_night or saturday_night:
        return True, ""
    days_to_friday = (4 - wd) % 7
    if wd == 4 and h < 22:
        next_open = now.replace(hour=22, minute=0, second=0, microsecond=0)
    else:
        next_friday = now + timedelta(days=days_to_friday if days_to_friday > 0 else 7)
        next_open = next_friday.replace(hour=22, minute=0, second=0, microsecond=0)
    delta = next_open - now
    hours_left = int(delta.total_seconds() // 3600)
    label = f"Příští otevření: **pátek {next_open.strftime('%d.%m')} ve 22:00**"
    if hours_left < 48:
        label += f" (za {hours_left} h)"
    return False, label


def _load_orders_fresh() -> pd.DataFrame:
    """Load orders bypassing cache — used for live polling."""
    return clean_orders(load_orders())


@st.cache_data(ttl=300)
def _load_products_cached() -> pd.DataFrame:
    return clean_products(load_products())


# ── Session state init ─────────────────────────────────────────────────────────
if "order_statuses" not in st.session_state:
    st.session_state.order_statuses = {}   # {order_id: status}
if "sound_enabled" not in st.session_state:
    st.session_state.sound_enabled = True

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("### Live monitoring")
live_mode = st.sidebar.toggle("🔴 Live mode (auto-refresh 30s)", value=False)
st.session_state.sound_enabled = st.sidebar.toggle(
    "🔊 Zvukové notifikace", value=st.session_state.sound_enabled
)
if live_mode:
    refresh_interval = st.sidebar.selectbox("Interval", [15, 30, 60], index=1, format_func=lambda x: f"{x}s")

st.sidebar.divider()
st.sidebar.markdown(
    "**Zvuky dle stavu:**\n"
    "- 🔵 nová → 3× stoupající tón\n"
    "- 🟡 přijatá → 2× pípnutí\n"
    "- 🟢 doručená → fanfára\n"
    "- 🔴 zrušená → sestupný bzukot"
)
st.sidebar.success("Vyberte stránku výše.")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🍺 VečerkaPlus Analytics")

is_open, next_label = _shift_status()
if is_open:
    st.success("🟢 **OTEVŘENO** — směna právě probíhá")
else:
    st.error(f"🔴 **ZAVŘENO** — {next_label}")

st.divider()

# ── Load data ─────────────────────────────────────────────────────────────────
try:
    products_df = _load_products_cached()
except Exception:
    products_df = pd.DataFrame()

try:
    orders_df = _load_orders_fresh()
except Exception as e:
    st.warning(f"Nelze načíst objednávky: {e}")
    orders_df = pd.DataFrame()

# ── Detect status changes & play sounds ───────────────────────────────────────
changed_orders: list[tuple[str, str, str]] = []  # (name, old_status, new_status)

if not orders_df.empty:
    current_statuses = dict(zip(orders_df["id"], orders_df["status"]))
    prev = st.session_state.order_statuses

    for oid, new_status in current_statuses.items():
        old_status = prev.get(oid)
        if old_status is None:
            # Brand new order not seen before — only alert if session already had data
            if prev:
                row = orders_df[orders_df["id"] == oid].iloc[0]
                changed_orders.append((row["name"], "—", new_status))
        elif old_status != new_status:
            row = orders_df[orders_df["id"] == oid].iloc[0]
            changed_orders.append((row["name"], old_status, new_status))

    st.session_state.order_statuses = current_statuses

    if changed_orders and st.session_state.sound_enabled:
        # Play sound for the most "significant" change (priority: nová > zrušená > doručená > přijatá)
        priority = {"nová": 4, "zrušená": 3, "doručená": 2, "přijatá": 1}
        top_status = max(changed_orders, key=lambda x: priority.get(x[2], 0))[2]
        _play_sound(top_status)

    if changed_orders:
        for cname, old_s, new_s in changed_orders:
            if old_s == "—":
                st.toast(f"🔵 Nová objednávka: **{cname}**", icon="🛒")
            else:
                icons = {"přijatá": "🟡", "doručená": "🟢", "zrušená": "🔴"}
                icon = icons.get(new_s, "ℹ️")
                st.toast(f"{icon} {cname}: {old_s} → **{new_s}**")

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.subheader("Přehled")

now = datetime.now(_TZ)
week_ago = now - timedelta(days=7)

if not orders_df.empty:
    recent = orders_df[orders_df["created_at"] >= week_ago]
    delivered = recent[recent["status"] == "doručená"]
    revenue_week = int(delivered["total"].sum())
    avg_order = int(delivered["total"].mean()) if not delivered.empty else 0
    all_delivered = orders_df[orders_df["status"] == "doručená"]
    revenue_total = int(all_delivered["total"].sum())
else:
    recent = delivered = pd.DataFrame()
    revenue_week = avg_order = revenue_total = 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Produkty v DB", len(products_df))
c2.metric("Objednávky (7 dní)", len(recent))
c3.metric("Tržby (7 dní)", f"{revenue_week:,} Kč".replace(",", " "))
c4.metric("Průměrná objednávka", f"{avg_order} Kč")
c5.metric("Tržby celkem", f"{revenue_total:,} Kč".replace(",", " "))

st.divider()

# ── Recent orders ─────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("Poslední objednávky")
    if orders_df.empty:
        st.info("Žádné objednávky v databázi.")
    else:
        last10 = orders_df.sort_values("created_at", ascending=False).head(10)
        STATUS_ICON = {"nová": "🔵", "přijatá": "🟡", "doručená": "🟢", "zrušená": "🔴"}
        display = last10[["created_at", "name", "total", "status", "payment"]].copy()
        display["created_at"] = display["created_at"].dt.strftime("%d.%m %H:%M")
        display["status"] = display["status"].map(lambda s: f"{STATUS_ICON.get(s, '')} {s}")
        display = display.rename(columns={
            "created_at": "Čas", "name": "Zákazník",
            "total": "Kč", "status": "Stav", "payment": "Platba",
        })
        st.dataframe(display, use_container_width=True, hide_index=True)

with col_right:
    st.subheader("Status (7 dní)")
    if orders_df.empty:
        st.info("Bez dat.")
    else:
        status_counts = recent["status"].value_counts() if not recent.empty else pd.Series(dtype=int)
        for status, icon in [("nová", "🔵"), ("přijatá", "🟡"), ("doručená", "🟢"), ("zrušená", "🔴")]:
            st.metric(f"{icon} {status.capitalize()}", int(status_counts.get(status, 0)))

# ── Auto-refresh ──────────────────────────────────────────────────────────────
if live_mode:
    time.sleep(refresh_interval)
    st.rerun()
