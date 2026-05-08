import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")

TIMEZONE = "Europe/Prague"
TARGET_MARGIN = 0.35  # 35%
FUZZY_CUTOFF = 70     # rapidfuzz token_sort_ratio threshold

# Rozvoz
ORIGIN = "Frýdek-Místek, Czech Republic"
DEFAULT_FUEL_L_PER_100KM = 7.5
DEFAULT_FUEL_PRICE_CZK = 42.0
