import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")

TIMEZONE = "Europe/Prague"
TARGET_MARGIN = 0.35  # 35%
FUZZY_CUTOFF = 70     # rapidfuzz token_sort_ratio threshold
