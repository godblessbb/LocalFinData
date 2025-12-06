"""Downloading and caching local financial datasets for training pipelines."""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Iterable

import pandas as pd
import yfinance as yf

from . import indicators
from .config import DATA_DIR, DEFAULT_INTERVAL, DEFAULT_INDICATOR_PERIODS


def _normalize_dates(start: str | dt.date | dt.datetime | None, end: str | dt.date | dt.datetime | None) -> tuple[str, str]:
    today = dt.date.today()
    if end is None:
        end = today
    if start is None:
        start = end - dt.timedelta(days=365 * 3)

    def to_str(value: str | dt.date | dt.datetime) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, dt.datetime):
            return value.date().isoformat()
        return value.isoformat()

    return to_str(start), to_str(end)


def download_prices(
    tickers: Iterable[str],
    start: str | dt.date | dt.datetime | None = None,
    end: str | dt.date | dt.datetime | None = None,
    interval: str = DEFAULT_INTERVAL,
) -> pd.DataFrame:
    """Download OHLCV data from Yahoo Finance and return a tidy DataFrame."""

    start_str, end_str = _normalize_dates(start, end)
    history = yf.download(tickers=list(tickers), start=start_str, end=end_str, interval=interval, group_by="ticker", auto_adjust=False, progress=False)

    # yfinance returns a MultiIndex when requesting multiple tickers
    if isinstance(history.columns, pd.MultiIndex):
        frames = []
        for ticker in history.columns.levels[0]:
            sub = history[ticker].copy()
            sub["tic"] = ticker
            frames.append(sub)
        data = pd.concat(frames)
    else:
        data = history.copy()
        data["tic"] = list(tickers)[0]

    data.reset_index(inplace=True)
    data.rename(columns={"Date": "date", "Open": "open", "High": "high", "Low": "low", "Close": "close", "Adj Close": "adj_close", "Volume": "volume"}, inplace=True)
    data = data[["date", "tic", "open", "high", "low", "close", "adj_close", "volume"]]
    return data


def enrich_with_indicators(data: pd.DataFrame, periods: dict | None = None) -> pd.DataFrame:
    """Append technical indicators used for training and visualization."""
    return indicators.add_indicators(data, periods=periods or DEFAULT_INDICATOR_PERIODS)


def save_prices(data: pd.DataFrame, name: str) -> Path:
    """Persist enriched data under ``data/prices`` and return the file path."""
    output = DATA_DIR / f"{name}.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(output, index=False)
    return output


def download_and_cache(
    tickers: Iterable[str],
    start: str | dt.date | dt.datetime | None = None,
    end: str | dt.date | dt.datetime | None = None,
    interval: str = DEFAULT_INTERVAL,
    periods: dict | None = None,
) -> Path:
    """High-level helper to download data, enrich indicators, and save locally."""
    prices = download_prices(tickers, start=start, end=end, interval=interval)
    enriched = enrich_with_indicators(prices, periods=periods)
    name = "_".join(sorted(tickers)) + f"_{start or 'auto'}_{end or 'auto'}".replace(" ", "")
    return save_prices(enriched, name)
