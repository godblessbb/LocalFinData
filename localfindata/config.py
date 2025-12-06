"""Project-wide configuration for data downloads and storage."""
from __future__ import annotations

from pathlib import Path

# Root directory of the repository
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default location to store raw and enriched price data
DATA_DIR = PROJECT_ROOT / "data" / "prices"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Default indicator settings
DEFAULT_INTERVAL = "1d"
DEFAULT_INDICATOR_PERIODS = {
    "ema": [5, 20, 50, 100, 200],
    "bollinger": 20,
    "rsi": 14,
    "stochastic": 14,
    "atr": 14,
    "adx": 14,
}
