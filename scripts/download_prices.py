#!/usr/bin/env python3
"""Command line helper to download stock data and enrich it with indicators."""
from __future__ import annotations

import argparse

from localfindata.pipeline import download_and_cache


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download OHLCV data with indicators.")
    parser.add_argument("tickers", nargs="+", help="Ticker symbols to download")
    parser.add_argument("--start", help="Start date YYYY-MM-DD (default: 3 years ago)")
    parser.add_argument("--end", help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--interval", default="1d", help="Data interval (e.g., 1d, 1wk, 1mo)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path = download_and_cache(args.tickers, start=args.start, end=args.end, interval=args.interval)
    print(f"Saved data to {path}")


if __name__ == "__main__":
    main()
