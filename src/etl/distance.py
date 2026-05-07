"""Google Distance Matrix lookups with JSON file cache to minimise API calls."""
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

from src.config import GOOGLE_MAPS_API_KEY, ORIGIN

_CACHE_FILE = Path(__file__).parent.parent.parent / "data" / "distance_cache.json"


def _load_cache() -> dict:
    if _CACHE_FILE.exists():
        try:
            return json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def get_distance_km(destination: str) -> float | None:
    """Return one-way road distance in km from ORIGIN to destination.
    Returns None if API call fails or key is missing.
    Results are cached in data/distance_cache.json.
    """
    if not GOOGLE_MAPS_API_KEY or not destination:
        return None

    cache = _load_cache()
    if destination in cache:
        return cache[destination]

    url = (
        "https://maps.googleapis.com/maps/api/distancematrix/json?"
        + urllib.parse.urlencode({
            "origins": ORIGIN,
            "destinations": destination,
            "mode": "driving",
            "language": "cs",
            "key": GOOGLE_MAPS_API_KEY,
        })
    )

    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        element = data["rows"][0]["elements"][0]
        if element["status"] != "OK":
            return None
        km = round(element["distance"]["value"] / 1000, 1)
        cache[destination] = km
        _save_cache(cache)
        return km
    except Exception:
        return None


def delivery_cost(km: float, fuel_l_per_100km: float, fuel_price_czk: float) -> float:
    """One-way fuel cost in CZK. Multiply by 2 for round trip."""
    return round(km * (fuel_l_per_100km / 100) * fuel_price_czk, 1)
