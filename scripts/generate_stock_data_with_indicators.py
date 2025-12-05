#!/usr/bin/env python3
"""
生成包含技术指标的股票数据
基于 yahoo_finance_test_data.csv 生成完整的技术指标数据
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def calculate_ema(prices, period):
    """计算指数移动平均"""
    return prices.ewm(span=period, adjust=False).mean()


def calculate_sma(prices, period):
    """计算简单移动平均"""
    return prices.rolling(window=period).mean()


def calculate_wma(prices, period):
    """计算加权移动平均"""
    weights = np.arange(1, period + 1)

    def weighted_mean(x):
        if len(x) < period:
            return np.nan
        return np.sum(weights * x[-period:]) / weights.sum()

    return prices.rolling(window=period).apply(weighted_mean, raw=True)


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """计算MACD指标"""
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    macd = ema_fast - ema_slow
    macd_signal = calculate_ema(macd, signal)
    macd_hist = macd - macd_signal
    return macd, macd_signal, macd_hist


def calculate_rsi(prices, period=14):
    """计算RSI指标"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """计算布林带"""
    sma = calculate_sma(prices, period)
    std = prices.rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    width = upper_band - lower_band
    pct_b = (prices - lower_band) / (upper_band - lower_band)
    return upper_band, lower_band, width, pct_b


def calculate_atr(high, low, close, period=14):
    """计算平均真实波幅"""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr


def calculate_cci(high, low, close, period=14):
    """计算商品通道指数"""
    tp = (high + low + close) / 3
    sma_tp = tp.rolling(window=period).mean()
    mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
    cci = (tp - sma_tp) / (0.015 * mad)
    return cci


def calculate_roc(prices, period=12):
    """计算变动率"""
    roc = ((prices - prices.shift(period)) / prices.shift(period)) * 100
    return roc


def calculate_momentum(prices, period=10):
    """计算动量"""
    return prices - prices.shift(period)


def calculate_williams_r(high, low, close, period=14):
    """计算威廉指标"""
    highest_high = high.rolling(window=period).max()
    lowest_low = low.rolling(window=period).min()
    williams_r = -100 * (highest_high - close) / (highest_high - lowest_low)
    return williams_r


def calculate_stochastic(high, low, close, k_period=14, d_period=3):
    """计算随机指标"""
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()

    stoch_k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    stoch_d = stoch_k.rolling(window=d_period).mean()
    stoch_j = 3 * stoch_k - 2 * stoch_d

    return stoch_k, stoch_d, stoch_j


def calculate_ultimate_oscillator(high, low, close, period1=7, period2=14, period3=28):
    """计算终极指标"""
    bp = close - pd.concat([low, close.shift()], axis=1).min(axis=1)
    tr = pd.concat([
        high - low,
        abs(high - close.shift()),
        abs(low - close.shift())
    ], axis=1).max(axis=1)

    avg1 = bp.rolling(window=period1).sum() / tr.rolling(window=period1).sum()
    avg2 = bp.rolling(window=period2).sum() / tr.rolling(window=period2).sum()
    avg3 = bp.rolling(window=period3).sum() / tr.rolling(window=period3).sum()

    uo = 100 * (4 * avg1 + 2 * avg2 + avg3) / 7
    return uo


def calculate_dema(prices, period):
    """计算双重指数移动平均"""
    ema1 = calculate_ema(prices, period)
    ema2 = calculate_ema(ema1, period)
    dema = 2 * ema1 - ema2
    return dema


def calculate_tema(prices, period):
    """计算三重指数移动平均"""
    ema1 = calculate_ema(prices, period)
    ema2 = calculate_ema(ema1, period)
    ema3 = calculate_ema(ema2, period)
    tema = 3 * ema1 - 3 * ema2 + ema3
    return tema


def calculate_trix(prices, period=14, signal_period=9):
    """计算TRIX指标"""
    ema1 = calculate_ema(prices, period)
    ema2 = calculate_ema(ema1, period)
    ema3 = calculate_ema(ema2, period)
    trix = 100 * (ema3.diff() / ema3.shift())
    trix_signal = calculate_ema(trix, signal_period)
    return trix, trix_signal


def calculate_mfi(high, low, close, volume, period=14):
    """计算资金流量指标"""
    tp = (high + low + close) / 3
    mf = tp * volume

    positive_mf = mf.where(tp > tp.shift(), 0).rolling(window=period).sum()
    negative_mf = mf.where(tp < tp.shift(), 0).rolling(window=period).sum()

    mfr = positive_mf / negative_mf
    mfi = 100 - (100 / (1 + mfr))
    return mfi


def calculate_adx(high, low, close, period=14):
    """计算平均趋向指标"""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

    atr = tr.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()

    return adx, plus_di, minus_di


def calculate_aroon(high, low, period=25):
    """计算阿隆指标"""
    aroon_up = 100 * high.rolling(window=period + 1).apply(
        lambda x: x.argmax() / period, raw=True
    )
    aroon_down = 100 * low.rolling(window=period + 1).apply(
        lambda x: x.argmin() / period, raw=True
    )
    aroon_osc = aroon_up - aroon_down
    return aroon_up, aroon_down, aroon_osc


def calculate_pivot_points(high, low, close):
    """计算枢轴点"""
    pivot = (high.shift() + low.shift() + close.shift()) / 3
    r1 = 2 * pivot - low.shift()
    r2 = pivot + (high.shift() - low.shift())
    s1 = 2 * pivot - high.shift()
    s2 = pivot - (high.shift() - low.shift())
    return pivot, r1, r2, s1, s2


def calculate_keltner_channels(high, low, close, period=20, atr_period=14, multiplier=2):
    """计算肯特纳通道"""
    typical_price = (high + low + close) / 3
    basis = calculate_ema(typical_price, period)
    atr = calculate_atr(high, low, close, atr_period)

    upper = basis + multiplier * atr
    lower = basis - multiplier * atr

    return upper, lower


def calculate_donchian_channels(high, low, period=20):
    """计算唐奇安通道"""
    upper = high.rolling(window=period).max()
    lower = low.rolling(window=period).min()
    middle = (upper + lower) / 2
    return upper, lower, middle


def generate_stock_data_with_indicators(input_file, output_file, ticker='AAPL'):
    """
    生成包含技术指标的股票数据

    Args:
        input_file: 输入CSV文件路径
        output_file: 输出CSV文件路径
        ticker: 股票代码
    """
    print(f"读取数据文件: {input_file}")

    # 读取原始数据（跳过前3行：列名、股票代码、空行）
    df = pd.read_csv(input_file, skiprows=3, header=None)

    # 手动设置列名（根据实际文件格式）
    df.columns = ['date', 'close', 'high', 'low', 'open', 'volume']

    # 去除任何空行
    df = df.dropna(subset=['date'])

    # 添加股票代码
    df['tic'] = ticker

    # 确保数据按日期排序
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)

    print(f"数据点数: {len(df)}")
    print(f"日期范围: {df['date'].min()} 到 {df['date'].max()}")

    # 提取价格和成交量数据
    close = df['close']
    high = df['high']
    low = df['low']
    open_p = df['open']
    volume = df['volume']

    print("计算技术指标...")

    # MACD
    df['macd'], df['macd_signal'], df['macd_hist'] = calculate_macd(close)
    df['macds'] = df['macd_signal']  # 别名
    df['macdh'] = df['macd_hist']    # 别名
    df['macd.1'] = df['macd']        # 别名

    # EMA系列
    for period in [3, 5, 8, 10, 12, 15, 20, 26, 30, 35, 40, 45, 50, 60, 100, 200]:
        df[f'ema_{period}'] = calculate_ema(close, period)

    # SMA系列
    for period in [5, 10, 15, 20, 30, 50, 60, 100, 200]:
        df[f'sma_{period}'] = calculate_sma(close, period)

    # WMA系列
    for period in [10, 20, 30]:
        df[f'wma_{period}'] = calculate_wma(close, period)

    # DEMA系列
    for period in [10, 20, 30]:
        df[f'dema_{period}'] = calculate_dema(close, period)

    # TEMA系列
    for period in [10, 20, 30]:
        df[f'tema_{period}'] = calculate_tema(close, period)

    # TRIX
    df['trix'], df['trix_signal'] = calculate_trix(close)

    # RSI系列
    for period in [6, 9, 12, 14, 21, 24]:
        df[f'rsi_{period}'] = calculate_rsi(close, period)

    # CCI
    df['cci_14'] = calculate_cci(high, low, close, 14)
    df['cci_20'] = calculate_cci(high, low, close, 20)

    # ROC
    df['roc_12'] = calculate_roc(close, 12)
    df['roc_25'] = calculate_roc(close, 25)

    # Momentum
    df['mom_10'] = calculate_momentum(close, 10)
    df['mom_14'] = calculate_momentum(close, 14)
    df['mom_20'] = calculate_momentum(close, 20)

    # Williams %R
    df['willr_14'] = calculate_williams_r(high, low, close, 14)
    df['willr_21'] = calculate_williams_r(high, low, close, 21)

    # Stochastic
    df['stoch_k_9'], df['stoch_d_9'], df['stoch_j_9'] = calculate_stochastic(high, low, close, 9, 3)
    df['stoch_k_14'], df['stoch_d_14'], df['stoch_j_14'] = calculate_stochastic(high, low, close, 14, 3)

    # Ultimate Oscillator
    df['uo'] = calculate_ultimate_oscillator(high, low, close)

    # Bollinger Bands (20)
    df['bb_upper_20'], df['bb_lower_20'], df['bb_width_20'], df['bb_pct_20'] = calculate_bollinger_bands(close, 20)

    # Bollinger Bands (50)
    df['bb_upper_50'], df['bb_lower_50'], df['bb_width_50'], df['bb_pct_50'] = calculate_bollinger_bands(close, 50)

    # ATR
    df['atr_7'] = calculate_atr(high, low, close, 7)
    df['atr_14'] = calculate_atr(high, low, close, 14)
    df['atr_21'] = calculate_atr(high, low, close, 21)

    # Standard Deviation
    df['std_10'] = close.rolling(window=10).std()
    df['std_20'] = close.rolling(window=20).std()
    df['std_30'] = close.rolling(window=30).std()

    # Keltner Channels
    df['kc_upper'], df['kc_lower'] = calculate_keltner_channels(high, low, close)

    # Donchian Channels
    df['dc_upper'], df['dc_lower'], df['dc_middle'] = calculate_donchian_channels(high, low)

    # OBV (On Balance Volume)
    df['obv'] = (np.sign(close.diff()) * volume).fillna(0).cumsum()

    # Volume MA
    df['vol_ma_5'] = volume.rolling(window=5).mean()
    df['vol_ma_10'] = volume.rolling(window=10).mean()
    df['vol_ma_20'] = volume.rolling(window=20).mean()

    # Volume Ratio
    df['vol_ratio'] = volume / df['vol_ma_20']

    # MFI (Money Flow Index)
    df['mfi'] = calculate_mfi(high, low, close, volume)

    # Accumulation/Distribution Line
    clv = ((close - low) - (high - close)) / (high - low)
    clv = clv.fillna(0)
    df['ad_line'] = (clv * volume).cumsum()

    # VWAP (简化版本，使用累计计算)
    df['vwap'] = (close * volume).cumsum() / volume.cumsum()

    # ADX and Directional Indicators
    df['adx'], df['pos_di'], df['neg_di'] = calculate_adx(high, low, close)

    # Aroon
    df['aroon_up'], df['aroon_down'], df['aroon_osc'] = calculate_aroon(high, low)

    # Pivot Points
    df['pivot'], df['r1'], df['r2'], df['s1'], df['s2'] = calculate_pivot_points(high, low, close)

    # SAR (简化版本，使用收盘价的滞后值)
    df['sar'] = close.shift()

    # Price Changes
    df['price_change'] = close.diff()
    df['price_change_pct'] = close.pct_change() * 100

    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    df['true_range'] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Typical, Median, Weighted Close
    df['typical_price'] = (high + low + close) / 3
    df['median_price'] = (high + low) / 2
    df['weighted_close'] = (high + low + 2 * close) / 4

    # Intraday Intensity
    df['intraday_intensity'] = (2 * close - high - low) / (high - low) * volume
    df['intraday_intensity'] = df['intraday_intensity'].fillna(0)

    # 调整列顺序，与用户提供的格式一致
    column_order = [
        'date', 'tic', 'open', 'high', 'low', 'close', 'volume',
        'macd', 'macds', 'macdh', 'macd.1', 'macd_signal', 'macd_hist',
        'ema_3', 'ema_5', 'ema_8', 'ema_10', 'ema_12', 'ema_15', 'ema_20', 'ema_26', 'ema_30',
        'ema_35', 'ema_40', 'ema_45', 'ema_50', 'ema_60', 'ema_100', 'ema_200',
        'sma_5', 'sma_10', 'sma_15', 'sma_20', 'sma_30', 'sma_50', 'sma_60', 'sma_100', 'sma_200',
        'wma_10', 'wma_20', 'wma_30',
        'dema_10', 'dema_20', 'dema_30',
        'tema_10', 'tema_20', 'tema_30',
        'trix', 'trix_signal',
        'rsi_6', 'rsi_9', 'rsi_12', 'rsi_14', 'rsi_21', 'rsi_24',
        'cci_14', 'cci_20',
        'roc_12', 'roc_25',
        'mom_10', 'mom_14', 'mom_20',
        'willr_14', 'willr_21',
        'stoch_k_9', 'stoch_d_9', 'stoch_j_9',
        'stoch_k_14', 'stoch_d_14', 'stoch_j_14',
        'uo',
        'bb_upper_20', 'bb_lower_20', 'bb_width_20', 'bb_pct_20',
        'bb_upper_50', 'bb_lower_50', 'bb_width_50', 'bb_pct_50',
        'atr_7', 'atr_14', 'atr_21',
        'std_10', 'std_20', 'std_30',
        'kc_upper', 'kc_lower',
        'dc_upper', 'dc_lower', 'dc_middle',
        'obv',
        'vol_ma_5', 'vol_ma_10', 'vol_ma_20', 'vol_ratio',
        'mfi',
        'ad_line', 'vwap',
        'adx', 'pos_di', 'neg_di',
        'aroon_up', 'aroon_down', 'aroon_osc',
        'pivot', 'r1', 'r2', 's1', 's2',
        'sar',
        'price_change', 'price_change_pct',
        'true_range', 'typical_price', 'median_price', 'weighted_close',
        'intraday_intensity'
    ]

    # 确保所有列都存在
    for col in column_order:
        if col not in df.columns:
            df[col] = np.nan

    df = df[column_order]

    # 保存到CSV
    print(f"保存数据到: {output_file}")
    df.to_csv(output_file, index=False)

    print(f"完成! 生成了 {len(df)} 行数据，包含 {len(df.columns)} 个字段")
    print(f"\n数据预览:")
    print(df.head())

    return df


if __name__ == '__main__':
    # 设置文件路径
    input_file = 'yahoo_finance_test_data.csv'
    output_file = 'data/prices/AAPL_with_indicators.csv'

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # 生成数据
    df = generate_stock_data_with_indicators(input_file, output_file, ticker='AAPL')

    print("\n数据已生成，可以使用以下MATLAB命令绘制K线图:")
    print(f"plot_candlestick_chart('{output_file}', 'AAPL')")
