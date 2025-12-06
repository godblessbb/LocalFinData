#!/usr/bin/env python3
"""Download yfinance 日度更新的全量信息（行情、事件、观点等）。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from localfindata.ticker_info import download_ticker_batch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download daily-refresh ticker info from yfinance")
    parser.add_argument("tickers", nargs="+", help="Ticker symbols to download")
    parser.add_argument("--start", help="Start date YYYY-MM-DD (default: 最近5年)")
    parser.add_argument("--end", help="End date YYYY-MM-DD (default: 今天)")
    return parser.parse_args()


def run(tickers: Iterable[str], start: str | None, end: str | None) -> None:
    paths = download_ticker_batch(tickers, start=start, end=end)
    if not paths:
        print("未获取到数据，可能是代码或网络限制。")
        return
    for path in paths:
        print(f"已保存：{path}")


def main() -> None:
    args = parse_args()
    run(args.tickers, args.start, args.end)


if __name__ == "__main__":
    main()
