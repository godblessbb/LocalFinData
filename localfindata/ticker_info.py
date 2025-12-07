"""Utilities for downloading daily-refresh Yahoo Finance datasets per ticker."""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Iterable, List

import pandas as pd
import yfinance as yf
from yfinance.exceptions import YFRateLimitError

from .config import DATA_DIR


def _retry_yf_call(func, *args, max_attempts: int = 5, backoff: int = 10, **kwargs):
    """Retry a yfinance call on rate limit errors with exponential backoff."""

    attempt = 1
    while True:
        try:
            return func(*args, **kwargs)
        except YFRateLimitError as exc:  # pragma: no cover - network dependent
            if attempt >= max_attempts:
                raise exc
            # Exponential backoff: 10s, 20s, 40s, 80s, 160s
            wait_seconds = backoff * (2 ** (attempt - 1))
            print(
                f"[yfinance] Rate limited calling {func.__name__}; "
                f"retrying in {wait_seconds}s (attempt {attempt + 1}/{max_attempts})"
            )
            import time

            time.sleep(wait_seconds)
            attempt += 1


def _default_dates(years: int = 5) -> tuple[str, str]:
    today = dt.date.today()
    start = today - dt.timedelta(days=365 * years)
    return start.isoformat(), today.isoformat()


def _reset_index(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    if df.index.name is not None:
        df = df.reset_index()
    elif isinstance(df.index, (pd.DatetimeIndex, pd.MultiIndex, pd.Index)):
        df = df.reset_index()
    if "index" in df.columns:
        df = df.rename(columns={"index": date_col})
    return df


def _frame_from_series(series: pd.Series, dataset: str, value_name: str, tic: str) -> pd.DataFrame | None:
    if series is None or series.empty:
        return None
    df = series.copy()
    df = df.to_frame(name=value_name)
    df = _reset_index(df)
    df.rename(columns={df.columns[0]: "date"}, inplace=True)
    df["dataset"] = dataset
    df["tic"] = tic
    return df


def _frame_from_df(data: pd.DataFrame | None, dataset: str, tic: str) -> pd.DataFrame | None:
    if data is None or data.empty:
        return None
    df = data.copy()
    df = _reset_index(df)
    df["dataset"] = dataset
    df["tic"] = tic
    return df


def fetch_history(tic: str, ticker: yf.Ticker, start: str, end: str) -> pd.DataFrame | None:
    history = _retry_yf_call(
        ticker.history,
        start=start,
        end=end,
        interval="1d",
        actions=True,
        auto_adjust=False,
    )
    if history.empty:
        return None

    history = _reset_index(history)
    history.rename(
        columns={
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Adj Close": "adj_close",
            "Volume": "volume",
            "Dividends": "dividends",
            "Stock Splits": "stock_splits",
        },
        inplace=True,
    )
    cols = [
        "date",
        "open",
        "high",
        "low",
        "close",
        "adj_close",
        "volume",
        "dividends",
        "stock_splits",
    ]
    for col in cols:
        if col not in history:
            history[col] = pd.NA

    history = history[cols]
    history["dataset"] = "history"
    history["interval"] = "1d"
    history["tic"] = tic
    return history


def fetch_calendar(tic: str, ticker: yf.Ticker) -> pd.DataFrame | None:
    calendar = ticker.calendar
    if calendar is None or calendar.empty:
        return None
    # calendar returned with events as index; transpose for tidy rows
    cal = calendar.transpose().reset_index().rename(columns={"index": "event"})
    cal["dataset"] = "calendar"
    cal["tic"] = tic
    return cal


def fetch_earnings_dates(tic: str, ticker: yf.Ticker, limit: int = 60) -> pd.DataFrame | None:
    try:
        earnings_dates = ticker.get_earnings_dates(limit=limit)
    except Exception:
        return None
    return _frame_from_df(earnings_dates, "earnings_dates", tic)


def fetch_recommendations(tic: str, ticker: yf.Ticker) -> List[pd.DataFrame]:
    frames: List[pd.DataFrame] = []

    rec = _frame_from_df(getattr(ticker, "recommendations", None), "recommendations", tic)
    if rec is not None:
        frames.append(rec)

    rec_summary = _frame_from_df(getattr(ticker, "recommendations_summary", None), "recommendations_summary", tic)
    if rec_summary is not None:
        frames.append(rec_summary)

    upgrades = _frame_from_df(getattr(ticker, "upgrades_downgrades", None), "upgrade_downgrade_history", tic)
    if upgrades is not None:
        frames.append(upgrades)

    price_targets = _frame_from_df(getattr(ticker, "analyst_price_targets", None), "analyst_price_targets", tic)
    if price_targets is not None:
        frames.append(price_targets)

    return frames


def fetch_earnings_and_forecasts(tic: str, ticker: yf.Ticker) -> List[pd.DataFrame]:
    frames: List[pd.DataFrame] = []

    annual = _frame_from_df(getattr(ticker, "earnings", None), "earnings", tic)
    if annual is not None:
        frames.append(annual)

    quarterly = _frame_from_df(getattr(ticker, "quarterly_earnings", None), "quarterly_earnings", tic)
    if quarterly is not None:
        frames.append(quarterly)

    trend = _frame_from_df(getattr(ticker, "earnings_trend", None), "earnings_trend", tic)
    if trend is not None:
        frames.append(trend)

    revenue = _frame_from_df(getattr(ticker, "revenue_forecasts", None), "revenue_forecasts", tic)
    if revenue is not None:
        frames.append(revenue)

    return frames


def fetch_shares(tic: str, ticker: yf.Ticker, start: str, end: str) -> pd.DataFrame | None:
    try:
        shares = _retry_yf_call(ticker.get_shares_full, start=start, end=end)
    except Exception:
        shares = getattr(ticker, "shares", None)
    if shares is None:
        return None
    if isinstance(shares, pd.DataFrame):
        df = _frame_from_df(shares, "shares", tic)
        if "Date" in df.columns:
            df.rename(columns={"Date": "date"}, inplace=True)
        return df
    return _frame_from_series(pd.Series(shares), "shares", "shares_outstanding", tic)


def fetch_daily_datasets(tic: str, start: str | None = None, end: str | None = None, api_delay: float = 0.5) -> pd.DataFrame:
    """Collect daily/ event-driven datasets from yfinance for a single ticker.

    Args:
        tic: Stock ticker symbol
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        api_delay: Seconds to wait between API calls (default: 0.5)
    """
    import time

    if start is None and end is None:
        start_date, end_date = _default_dates()
    elif start is None:
        start_date, _ = _default_dates()
        end_date = end
    elif end is None:
        start_date = start
        end_date = dt.date.today().isoformat()
    else:
        start_date, end_date = start, end

    ticker = yf.Ticker(tic)
    frames: List[pd.DataFrame] = []

    history = fetch_history(tic, ticker, start_date, end_date)
    if history is not None:
        frames.append(history)
    time.sleep(api_delay)

    dividends = _frame_from_series(getattr(ticker, "dividends", None), "dividends", "dividend", tic)
    if dividends is not None:
        frames.append(dividends)
    time.sleep(api_delay)

    splits = _frame_from_series(getattr(ticker, "splits", None), "splits", "split_ratio", tic)
    if splits is not None:
        frames.append(splits)
    time.sleep(api_delay)

    capital_gains = _frame_from_series(getattr(ticker, "capital_gains", None), "capital_gains", "capital_gains", tic)
    if capital_gains is not None:
        frames.append(capital_gains)
    time.sleep(api_delay)

    calendar = fetch_calendar(tic, ticker)
    if calendar is not None:
        frames.append(calendar)
    time.sleep(api_delay)

    earnings_dates = fetch_earnings_dates(tic, ticker)
    if earnings_dates is not None:
        frames.append(earnings_dates)
    time.sleep(api_delay)

    frames.extend(fetch_recommendations(tic, ticker))
    time.sleep(api_delay)

    frames.extend(fetch_earnings_and_forecasts(tic, ticker))
    time.sleep(api_delay)

    shares = fetch_shares(tic, ticker, start_date, end_date)
    if shares is not None:
        frames.append(shares)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True, sort=False)
    # Normalize date-like columns to strings to ease CSV union
    for col in combined.columns:
        if col.lower().endswith("date") or col in {"date", "period", "timestamp"}:
            combined[col] = combined[col].astype(str)

    return combined


def save_ticker_info(tic: str, data: pd.DataFrame) -> Path:
    output_dir = DATA_DIR / "ticker"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{tic}.csv"

    if path.exists():
        existing = pd.read_csv(path)
        all_columns = sorted(set(existing.columns).union(data.columns))
        existing = existing.reindex(columns=all_columns)
        data = data.reindex(columns=all_columns)
        merged = pd.concat([existing, data], ignore_index=True, sort=False)
        merged = merged.drop_duplicates()
    else:
        merged = data

    merged.to_csv(path, index=False)
    return path


def download_ticker_batch(
    tickers: Iterable[str],
    start: str | None = None,
    end: str | None = None,
    delay_between_tickers: int = 3,
    api_delay: float = 0.5,
) -> list[Path]:
    """Download data for multiple tickers with delay between each to avoid rate limits.

    Args:
        tickers: Stock ticker symbols to download
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        delay_between_tickers: Seconds to wait between processing each ticker (default: 3)
        api_delay: Seconds to wait between API calls within each ticker (default: 0.5)
    """
    import time

    paths: list[Path] = []
    ticker_list = list(tickers)

    for i, ticker in enumerate(ticker_list):
        print(f"Processing {ticker} ({i+1}/{len(ticker_list)})...")
        data = fetch_daily_datasets(ticker, start=start, end=end, api_delay=api_delay)
        if data.empty:
            print(f"No data found for {ticker}")
            continue
        paths.append(save_ticker_info(ticker, data))
        print(f"Saved data for {ticker}")

        # Add delay between tickers (except after the last one)
        if i < len(ticker_list) - 1:
            print(f"Waiting {delay_between_tickers}s before next ticker...")
            time.sleep(delay_between_tickers)

    return paths
