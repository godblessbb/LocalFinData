#!/usr/bin/env python3
"""
批量计算技术指标并清理过期数据

功能：
1. 遍历 data/prices/ 下所有 CSV 文件
2. 计算 80+ 个技术指标
3. 删除最近6个月无交易数据的文件
4. 统计删除的文件数量和列表

使用方法：
    python scripts/calculate_indicators_batch.py
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import glob


def calculate_all_indicators(df):
    """
    计算所有技术指标（使用纯 pandas/numpy）

    优化版本：使用字典存储所有指标，最后一次性合并，避免 DataFrame 碎片化

    返回包含所有指标的 DataFrame
    """
    # 确保有必要的列
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"缺少必要的列: {col}")

    df = df.copy()
    close = df['close']
    high = df['high']
    low = df['low']
    open_price = df['open']
    volume = df['volume']

    # 使用字典存储所有新指标，避免 DataFrame 碎片化
    indicators = {}

    # ==================== 趋势指标 ====================

    # 1. MACD (Moving Average Convergence Divergence)
    exp1 = close.ewm(span=12, adjust=False).mean()
    exp2 = close.ewm(span=26, adjust=False).mean()
    indicators['macd'] = exp1 - exp2
    indicators['macd_signal'] = indicators['macd'].ewm(span=9, adjust=False).mean()
    indicators['macd_hist'] = indicators['macd'] - indicators['macd_signal']

    # 2. EMA (Exponential Moving Average) - 多周期
    for period in [3, 5, 8, 10, 12, 15, 20, 26, 30, 35, 40, 45, 50, 60, 100, 200]:
        indicators[f'ema_{period}'] = close.ewm(span=period, adjust=False).mean()

    # 3. SMA (Simple Moving Average) - 多周期
    for period in [5, 10, 15, 20, 30, 50, 60, 100, 200]:
        indicators[f'sma_{period}'] = close.rolling(window=period).mean()

    # 4. WMA (Weighted Moving Average)
    def wma(series, period):
        weights = np.arange(1, period + 1)
        return series.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

    for period in [10, 20, 30]:
        indicators[f'wma_{period}'] = wma(close, period)

    # 5. DEMA (Double Exponential Moving Average)
    for period in [10, 20, 30]:
        ema = close.ewm(span=period, adjust=False).mean()
        ema_ema = ema.ewm(span=period, adjust=False).mean()
        indicators[f'dema_{period}'] = 2 * ema - ema_ema

    # 6. TEMA (Triple Exponential Moving Average)
    for period in [10, 20, 30]:
        ema1 = close.ewm(span=period, adjust=False).mean()
        ema2 = ema1.ewm(span=period, adjust=False).mean()
        ema3 = ema2.ewm(span=period, adjust=False).mean()
        indicators[f'tema_{period}'] = 3 * ema1 - 3 * ema2 + ema3

    # 7. TRIX (Triple Exponential Average)
    ema1 = close.ewm(span=15, adjust=False).mean()
    ema2 = ema1.ewm(span=15, adjust=False).mean()
    ema3 = ema2.ewm(span=15, adjust=False).mean()
    indicators['trix'] = ema3.pct_change() * 100
    indicators['trix_signal'] = indicators['trix'].ewm(span=9, adjust=False).mean()

    # ==================== 动量指标 ====================

    # 8. RSI (Relative Strength Index) - 多周期
    for period in [6, 9, 12, 14, 21, 24]:
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        indicators[f'rsi_{period}'] = 100 - (100 / (1 + rs))

    # 9. CCI (Commodity Channel Index) - 多周期
    for period in [14, 20]:
        tp = (high + low + close) / 3
        sma_tp = tp.rolling(window=period).mean()
        mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
        indicators[f'cci_{period}'] = (tp - sma_tp) / (0.015 * mad)

    # 10. ROC (Rate of Change) - 多周期
    for period in [12, 25]:
        indicators[f'roc_{period}'] = ((close - close.shift(period)) / close.shift(period)) * 100

    # 11. Momentum
    for period in [10, 14, 20]:
        indicators[f'mom_{period}'] = close - close.shift(period)

    # 12. Williams %R
    for period in [14, 21]:
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        indicators[f'willr_{period}'] = -100 * ((highest_high - close) / (highest_high - lowest_low))

    # 13. Stochastic Oscillator (KDJ)
    for period in [9, 14]:
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        indicators[f'stoch_k_{period}'] = k
        indicators[f'stoch_d_{period}'] = k.rolling(window=3).mean()
        indicators[f'stoch_j_{period}'] = 3 * indicators[f'stoch_k_{period}'] - 2 * indicators[f'stoch_d_{period}']

    # 14. Ultimate Oscillator
    bp = close - pd.concat([low, close.shift()], axis=1).min(axis=1)
    tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
    avg7 = bp.rolling(7).sum() / tr.rolling(7).sum()
    avg14 = bp.rolling(14).sum() / tr.rolling(14).sum()
    avg28 = bp.rolling(28).sum() / tr.rolling(28).sum()
    indicators['uo'] = 100 * ((4 * avg7 + 2 * avg14 + avg28) / 7)

    # ==================== 波动率指标 ====================

    # 15. Bollinger Bands - 多周期
    for period in [20, 50]:
        sma = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        indicators[f'bb_middle_{period}'] = sma
        indicators[f'bb_upper_{period}'] = sma + (std * 2)
        indicators[f'bb_lower_{period}'] = sma - (std * 2)
        indicators[f'bb_width_{period}'] = ((indicators[f'bb_upper_{period}'] - indicators[f'bb_lower_{period}']) / indicators[f'bb_middle_{period}']) * 100
        indicators[f'bb_pct_{period}'] = (close - indicators[f'bb_lower_{period}']) / (indicators[f'bb_upper_{period}'] - indicators[f'bb_lower_{period}'])

    # 16. ATR (Average True Range) - 多周期
    for period in [7, 14, 21]:
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        indicators[f'atr_{period}'] = tr.rolling(window=period).mean()

    # 17. Standard Deviation - 多周期
    for period in [10, 20, 30]:
        indicators[f'std_{period}'] = close.rolling(window=period).std()

    # 18. Keltner Channels
    period = 20
    ema = close.ewm(span=period, adjust=False).mean()
    atr = indicators['atr_14']
    indicators['kc_middle'] = ema
    indicators['kc_upper'] = ema + (2 * atr)
    indicators['kc_lower'] = ema - (2 * atr)

    # 19. Donchian Channels
    period = 20
    indicators['dc_upper'] = high.rolling(window=period).max()
    indicators['dc_lower'] = low.rolling(window=period).min()
    indicators['dc_middle'] = (indicators['dc_upper'] + indicators['dc_lower']) / 2

    # ==================== 成交量指标 ====================

    # 20. OBV (On-Balance Volume)
    obv = [0]
    for i in range(1, len(close)):
        if close.iloc[i] > close.iloc[i-1]:
            obv.append(obv[-1] + volume.iloc[i])
        elif close.iloc[i] < close.iloc[i-1]:
            obv.append(obv[-1] - volume.iloc[i])
        else:
            obv.append(obv[-1])
    indicators['obv'] = obv

    # 21. Volume MA
    for period in [5, 10, 20]:
        indicators[f'vol_ma_{period}'] = volume.rolling(window=period).mean()

    # 22. Volume Ratio
    indicators['vol_ratio'] = volume / volume.rolling(window=20).mean()

    # 23. MFI (Money Flow Index)
    period = 14
    tp = (high + low + close) / 3
    mf = tp * volume
    positive_mf = mf.where(tp > tp.shift(), 0).rolling(period).sum()
    negative_mf = mf.where(tp < tp.shift(), 0).rolling(period).sum()
    mfi = 100 - (100 / (1 + positive_mf / negative_mf))
    indicators['mfi'] = mfi

    # 24. A/D Line (Accumulation/Distribution Line)
    mfm = ((close - low) - (high - close)) / (high - low)
    mfv = mfm * volume
    indicators['ad_line'] = mfv.cumsum()

    # 25. VWAP (Volume Weighted Average Price)
    indicators['vwap'] = (tp * volume).cumsum() / volume.cumsum()

    # 26. CMF (Chaikin Money Flow)
    period = 20
    mfv = ((close - low) - (high - close)) / (high - low) * volume
    indicators['cmf'] = mfv.rolling(period).sum() / volume.rolling(period).sum()

    # ==================== 趋势强度指标 ====================

    # 27. ADX (Average Directional Index)
    period = 14
    high_diff = high.diff()
    low_diff = -low.diff()
    pos_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
    neg_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
    tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    pos_di = 100 * (pos_dm.rolling(period).mean() / atr)
    neg_di = 100 * (neg_dm.rolling(period).mean() / atr)
    dx = 100 * abs(pos_di - neg_di) / (pos_di + neg_di)
    indicators['adx'] = dx.rolling(period).mean()
    indicators['pos_di'] = pos_di
    indicators['neg_di'] = neg_di

    # 28. Aroon
    period = 25
    aroon_up = high.rolling(period + 1).apply(lambda x: x.argmax(), raw=True) / period * 100
    aroon_down = low.rolling(period + 1).apply(lambda x: x.argmin(), raw=True) / period * 100
    indicators['aroon_up'] = aroon_up
    indicators['aroon_down'] = aroon_down
    indicators['aroon_osc'] = aroon_up - aroon_down

    # ==================== 支撑阻力指标 ====================

    # 29. Pivot Points
    indicators['pivot'] = (high.shift() + low.shift() + close.shift()) / 3
    indicators['r1'] = 2 * indicators['pivot'] - low.shift()
    indicators['r2'] = indicators['pivot'] + (high.shift() - low.shift())
    indicators['s1'] = 2 * indicators['pivot'] - high.shift()
    indicators['s2'] = indicators['pivot'] - (high.shift() - low.shift())

    # ==================== 价格模式指标 ====================

    # 30. Parabolic SAR
    af = 0.02
    max_af = 0.2
    uptrend = True
    sar = [low.iloc[0]]
    ep = high.iloc[0]
    af_current = af

    for i in range(1, len(df)):
        if uptrend:
            sar_value = sar[-1] + af_current * (ep - sar[-1])
            sar_value = min(sar_value, low.iloc[i-1], low.iloc[i-2] if i > 1 else low.iloc[i-1])

            if high.iloc[i] > ep:
                ep = high.iloc[i]
                af_current = min(af_current + af, max_af)

            if low.iloc[i] < sar_value:
                uptrend = False
                sar_value = ep
                ep = low.iloc[i]
                af_current = af
        else:
            sar_value = sar[-1] - af_current * (sar[-1] - ep)
            sar_value = max(sar_value, high.iloc[i-1], high.iloc[i-2] if i > 1 else high.iloc[i-1])

            if low.iloc[i] < ep:
                ep = low.iloc[i]
                af_current = min(af_current + af, max_af)

            if high.iloc[i] > sar_value:
                uptrend = True
                sar_value = ep
                ep = high.iloc[i]
                af_current = af

        sar.append(sar_value)

    indicators['sar'] = sar

    # ==================== 其他有用指标 ====================

    # 31. Price Change
    indicators['price_change'] = close.diff()
    indicators['price_change_pct'] = close.pct_change() * 100

    # 32. True Range
    high_low = high - low
    high_close = abs(high - close.shift())
    low_close = abs(low - close.shift())
    indicators['true_range'] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

    # 33. Typical Price
    indicators['typical_price'] = (high + low + close) / 3

    # 34. Median Price
    indicators['median_price'] = (high + low) / 2

    # 35. Weighted Close
    indicators['weighted_close'] = (high + low + 2 * close) / 4

    # 36. Intraday Intensity
    indicators['intraday_intensity'] = ((2 * close - high - low) / (high - low)) * volume

    # 将所有指标转换为 DataFrame 并一次性合并（避免碎片化）
    indicators_df = pd.DataFrame(indicators, index=df.index)

    # 四舍五入所有指标到2位小数
    for col in indicators_df.columns:
        if col not in ['volume'] and indicators_df[col].dtype in ['float64', 'float32']:
            indicators_df[col] = indicators_df[col].round(2)

    # 合并原始数据和指标
    result_df = pd.concat([df, indicators_df], axis=1)

    return result_df


def process_single_file(filepath, cutoff_date):
    """
    处理单个 CSV 文件

    返回: (status, message)
        status: 'deleted' | 'updated' | 'error'
    """
    try:
        # 读取文件
        df = pd.read_csv(filepath)

        # 检查是否有必要的列
        if 'date' not in df.columns:
            return 'error', "缺少 date 列"

        # 转换日期
        df['date'] = pd.to_datetime(df['date'])

        # 检查最新日期
        latest_date = df['date'].max()

        # 如果最新日期超过6个月，删除文件
        if latest_date < cutoff_date:
            os.remove(filepath)
            return 'deleted', f"最新数据: {latest_date.date()}"

        # 检查是否有必要的价格列
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return 'error', f"缺少列: {missing_cols}"

        # 计算技术指标
        df_with_indicators = calculate_all_indicators(df)

        # 将日期转回字符串格式 (YYYY-MM-DD)
        df_with_indicators['date'] = df_with_indicators['date'].dt.strftime('%Y-%m-%d')

        # 保存文件
        df_with_indicators.to_csv(filepath, index=False)

        return 'updated', f"添加了 {len(df_with_indicators.columns)} 列"

    except Exception as e:
        return 'error', str(e)


def main():
    """主函数"""
    print("\n" + "="*60)
    print("批量计算技术指标并清理过期数据")
    print("="*60)

    # 设置路径
    prices_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'prices')

    if not os.path.exists(prices_dir):
        print(f"❌ 目录不存在: {prices_dir}")
        return

    # 获取所有 CSV 文件
    csv_files = glob.glob(os.path.join(prices_dir, '*.csv'))
    total_files = len(csv_files)

    if total_files == 0:
        print(f"❌ 在 {prices_dir} 中未找到 CSV 文件")
        return

    print(f"找到 {total_files} 个 CSV 文件")
    print("="*60 + "\n")

    # 计算截止日期（6个月前）
    cutoff_date = datetime.now() - timedelta(days=180)
    print(f"截止日期: {cutoff_date.date()}")
    print(f"将删除最新数据早于此日期的文件\n")

    # 统计信息
    deleted_files = []
    updated_files = []
    error_files = []

    # 处理每个文件
    for i, filepath in enumerate(csv_files, 1):
        filename = os.path.basename(filepath)
        print(f"[{i}/{total_files}] 处理 {filename}...", end=' ')

        status, message = process_single_file(filepath, cutoff_date)

        if status == 'deleted':
            print(f"🗑️  已删除 ({message})")
            deleted_files.append(filename)
        elif status == 'updated':
            print(f"✅ 已更新 ({message})")
            updated_files.append(filename)
        else:  # error
            print(f"❌ 错误: {message}")
            error_files.append((filename, message))

        # 每100个文件显示一次进度
        if i % 100 == 0:
            print(f"\n进度: {i}/{total_files} ({i/total_files*100:.1f}%)\n")

    # 显示最终统计
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)
    print(f"总文件数: {total_files}")
    print(f"✅ 已更新: {len(updated_files)}")
    print(f"🗑️  已删除: {len(deleted_files)}")
    print(f"❌ 错误: {len(error_files)}")
    print("="*60)

    # 显示删除的文件列表
    if deleted_files:
        print(f"\n已删除的文件 ({len(deleted_files)} 个):")
        print("-" * 60)
        for i, filename in enumerate(deleted_files, 1):
            print(f"  {i}. {filename}")
            if i >= 50:
                print(f"  ... 还有 {len(deleted_files) - 50} 个")
                break

    # 显示错误文件
    if error_files:
        print(f"\n错误文件 ({len(error_files)} 个):")
        print("-" * 60)
        for i, (filename, error) in enumerate(error_files, 1):
            print(f"  {i}. {filename}: {error}")
            if i >= 20:
                print(f"  ... 还有 {len(error_files) - 20} 个")
                break

    # 保存删除列表到文件
    if deleted_files:
        deleted_list_path = os.path.join(prices_dir, 'deleted_files.txt')
        with open(deleted_list_path, 'w') as f:
            f.write(f"删除时间: {datetime.now()}\n")
            f.write(f"截止日期: {cutoff_date.date()}\n")
            f.write(f"删除数量: {len(deleted_files)}\n")
            f.write("\n删除的文件:\n")
            for filename in deleted_files:
                f.write(f"{filename}\n")
        print(f"\n删除列表已保存到: {deleted_list_path}")

    print("\n✅ 全部完成！\n")


if __name__ == '__main__':
    main()
