"""Utility functions for adding common technical indicators to price data."""
from __future__ import annotations

import pandas as pd
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import ADXIndicator, EMAIndicator, MACD, PSARIndicator
from ta.volatility import AverageTrueRange, BollingerBands
from ta.volume import OnBalanceVolumeIndicator

from .config import DEFAULT_INDICATOR_PERIODS


def _ensure_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    if "date" in df.columns:
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
    elif not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame must have a datetime index or a 'date' column")
    return df


def add_indicators(df: pd.DataFrame, periods: dict | None = None) -> pd.DataFrame:
    """Return a copy of ``df`` with common indicators used by the charting script.

    The function expects standard OHLCV column names: ``open, high, low, close, volume``.
    Missing columns will raise a ``KeyError``.
    """

    periods = periods or DEFAULT_INDICATOR_PERIODS
    working = _ensure_datetime_index(df)
    data = working.copy()

    # Exponential moving averages
    for window in periods.get("ema", []):
        data[f"ema_{window}"] = EMAIndicator(close=data["close"], window=window).ema_indicator()

    # Bollinger Bands
    bb_window = periods.get("bollinger", 20)
    bb = BollingerBands(close=data["close"], window=bb_window)
    data[f"bb_upper_{bb_window}"] = bb.bollinger_hband()
    data[f"bb_lower_{bb_window}"] = bb.bollinger_lband()

    # MACD
    macd = MACD(close=data["close"])
    data["macd"] = macd.macd()
    data["macds"] = macd.macd_signal()
    data["macdh"] = macd.macd_diff()

    # RSI
    rsi_window = periods.get("rsi", 14)
    data[f"rsi_{rsi_window}"] = RSIIndicator(close=data["close"], window=rsi_window).rsi()

    # Stochastic (KDJ) values
    stoch_window = periods.get("stochastic", 14)
    stoch = StochasticOscillator(high=data["high"], low=data["low"], close=data["close"], window=stoch_window)
    data[f"stoch_k_{stoch_window}"] = stoch.stoch()
    data[f"stoch_d_{stoch_window}"] = stoch.stoch_signal()
    data[f"stoch_j_{stoch_window}"] = 3 * data[f"stoch_k_{stoch_window}"] - 2 * data[f"stoch_d_{stoch_window}"]

    # Average True Range
    atr_window = periods.get("atr", 14)
    data[f"atr_{atr_window}"] = AverageTrueRange(high=data["high"], low=data["low"], close=data["close"], window=atr_window).average_true_range()

    # ADX and directional indicators
    adx_window = periods.get("adx", 14)
    adx_indicator = ADXIndicator(high=data["high"], low=data["low"], close=data["close"], window=adx_window)
    data["adx"] = adx_indicator.adx()
    data["pos_di"] = adx_indicator.adx_pos()
    data["neg_di"] = adx_indicator.adx_neg()

    # On Balance Volume
    data["obv"] = OnBalanceVolumeIndicator(close=data["close"], volume=data["volume"]).on_balance_volume()

    # Parabolic SAR
    psar = PSARIndicator(high=data["high"], low=data["low"], close=data["close"])
    data["sar"] = psar.psar()

    data.reset_index(inplace=True)
    return data
