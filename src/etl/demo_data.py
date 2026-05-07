"""Generate synthetic orders for demo/testing purposes."""
import random
import uuid
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytz

_TZ = pytz.timezone("Europe/Prague")

_FALLBACK_PRODUCTS = [
    {"id": str(uuid.uuid4()), "name": "Pilsner Urquell 0,5l", "category": "Pivo", "price": 59, "stock": 100},
    {"id": str(uuid.uuid4()), "name": "Kozel 11° 0,5l", "category": "Pivo", "price": 49, "stock": 100},
    {"id": str(uuid.uuid4()), "name": "Budvar 0,5l", "category": "Pivo", "price": 55, "stock": 100},
    {"id": str(uuid.uuid4()), "name": "Radegast 10° 0,5l", "category": "Pivo", "price": 45, "stock": 100},
    {"id": str(uuid.uuid4()), "name": "Gambrinus 10° 0,5l", "category": "Pivo", "price": 42, "stock": 100},
    {"id": str(uuid.uuid4()), "name": "Heineken 0,5l", "category": "Pivo", "price": 65, "stock": 50},
    {"id": str(uuid.uuid4()), "name": "Staropramen 0,5l", "category": "Pivo", "price": 52, "stock": 80},
    {"id": str(uuid.uuid4()), "name": "Becherovka 0,5l", "category": "Lihoviny", "price": 299, "stock": 30},
    {"id": str(uuid.uuid4()), "name": "Fernet Stock 0,5l", "category": "Lihoviny", "price": 249, "stock": 30},
    {"id": str(uuid.uuid4()), "name": "Slivovice 0,5l", "category": "Lihoviny", "price": 229, "stock": 20},
    {"id": str(uuid.uuid4()), "name": "Vodka Absolut 0,7l", "category": "Lihoviny", "price": 399, "stock": 20},
    {"id": str(uuid.uuid4()), "name": "Rum Božkov 0,5l", "category": "Lihoviny", "price": 189, "stock": 25},
    {"id": str(uuid.uuid4()), "name": "Coca-Cola 0,5l", "category": "Nealko", "price": 39, "stock": 200},
    {"id": str(uuid.uuid4()), "name": "Sprite 0,5l", "category": "Nealko", "price": 35, "stock": 150},
    {"id": str(uuid.uuid4()), "name": "Red Bull 0,25l", "category": "Nealko", "price": 69, "stock": 80},
    {"id": str(uuid.uuid4()), "name": "Mattoni 0,5l", "category": "Nealko", "price": 25, "stock": 200},
    {"id": str(uuid.uuid4()), "name": "Chips Lay's 100g", "category": "Svačiny", "price": 49, "stock": 60},
    {"id": str(uuid.uuid4()), "name": "Chips Pringles 165g", "category": "Svačiny", "price": 89, "stock": 40},
    {"id": str(uuid.uuid4()), "name": "Arašídy solené 200g", "category": "Svačiny", "price": 59, "stock": 50},
    {"id": str(uuid.uuid4()), "name": "Krekry 150g", "category": "Svačiny", "price": 45, "stock": 60},
    {"id": str(uuid.uuid4()), "name": "Čokoláda Milka 100g", "category": "Svačiny", "price": 39, "stock": 70},
    {"id": str(uuid.uuid4()), "name": "Tyčinka Snickers", "category": "Svačiny", "price": 25, "stock": 100},
]

_NAMES = [
    "Jan Novák", "Petra Svobodová", "Martin Dvořák", "Lucie Horáková",
    "Tomáš Procházka", "Eva Marková", "Jakub Krejčí", "Tereza Malá",
    "Ondřej Blažek", "Markéta Šimánková", "Radek Vlček", "Simona Kopecká",
    "Michal Beneš", "Veronika Růžičková", "Petr Hájek",
]

_ADDRESSES = [
    "Frýdlantská 15, Frýdek-Místek",
    "Hlavní tř. 42, Frýdek-Místek",
    "Nádražní 8, Frýdek",
    "Palackého 23, Místek",
    "Příční 7, Frýdek-Místek",
    "Ostravská 31, Frýdek-Místek",
    "Těšínská 55, Frýdek-Místek",
    "Novodvorská 12, Frýdek-Místek",
]

_PAYMENTS = ["hotovost", "karta", "online"]
_PAYMENT_W = [0.50, 0.30, 0.20]
_STATUSES = ["doručená"] * 85 + ["zrušená"] * 15


def _service_hours() -> list[int]:
    return list(range(22, 24)) + list(range(0, 7))


def _random_dt(base_date: datetime.date) -> datetime:
    hour = random.choice(_service_hours())
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    dt = _TZ.localize(
        datetime(base_date.year, base_date.month, base_date.day, hour, minute, second)
    )
    return dt


def _collect_valid_dates(n: int) -> list:
    dates = []
    d = datetime.now(_TZ).date()
    cutoff = d - timedelta(weeks=13)  # max 13 weeks back
    while len(dates) < n and d >= cutoff:
        if d.weekday() in (4, 5, 6):  # Fri/Sat/Sun
            dates.append(d)
        d -= timedelta(days=1)
    return dates


def generate_demo_orders(products_df: pd.DataFrame, n: int = 150) -> pd.DataFrame:
    """Create n synthetic orders distributed over Fri+Sat nights (22:00–06:00).
    Orders in hours 0–6 are timestamped on the calendar day that follows (Sat/Sun).
    """
    if products_df.empty:
        products = _FALLBACK_PRODUCTS
    else:
        products = products_df.to_dict("records")

    valid_dates = _collect_valid_dates(n * 2)

    # Weight recent dates more heavily
    weights = np.linspace(1.5, 0.5, len(valid_dates))
    weights /= weights.sum()

    rows = []
    for _ in range(n):
        date = random.choices(valid_dates, weights=weights)[0]
        dt = _random_dt(date)

        n_items = random.choices([1, 2, 3, 4], weights=[0.30, 0.35, 0.25, 0.10])[0]
        selected = random.sample(products, min(n_items, len(products)))

        items = []
        total = 0
        for p in selected:
            qty = random.choices([1, 2, 3], weights=[0.60, 0.30, 0.10])[0]
            items.append(
                {
                    "id": str(p["id"]),
                    "name": p["name"],
                    "price": int(p["price"]),
                    "quantity": qty,
                }
            )
            total += int(p["price"]) * qty

        rows.append(
            {
                "id": str(uuid.uuid4()),
                "created_at": dt,
                "name": random.choice(_NAMES),
                "address": random.choice(_ADDRESSES),
                "phone": f"+420 {random.randint(601,799):03d} {random.randint(100,999):03d} {random.randint(100,999):03d}",
                "payment": random.choices(_PAYMENTS, weights=_PAYMENT_W)[0],
                "items": items,
                "total": total,
                "status": random.choice(_STATUSES),
                "note": "",
            }
        )

    df = pd.DataFrame(rows)
    # Ensure tz-aware UTC timestamps (consistent with clean_orders input)
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    return df
