#!/usr/bin/env python3
"""
完全独立的股票数据下载脚本（无需 FinRL 导入）

使用：
- 直接使用 yfinance 下载数据
- 使用 TA-Lib 或 pandas_ta 计算技术指标（无需 stockstats）
- 不依赖任何 FinRL 模块

特点：
- 日期格式：YYYY-MM-DD
- 价格精度：2 位小数
- 完全独立，无复杂依赖
"""

import os
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import numpy as np


def get_date_range(years=3):
    """获取日期范围（默认过去3年）"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * years)
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')


def download_data(ticker_list, start_date, end_date):
    """
    下载股票数据（基于 FinRL 的 YahooDownloader）

    返回标准化的 DataFrame
    """
    print(f"\n{'='*60}")
    print(f"下载股票数据")
    print(f"{'='*60}")
    print(f"股票代码: {', '.join(ticker_list)}")
    print(f"时间范围: {start_date} 至 {end_date}")
    print(f"{'='*60}\n")

    data_df = pd.DataFrame()
    num_failures = 0

    for tic in ticker_list:
        print(f"正在下载 {tic} 的数据...")
        try:
            temp_df = yf.download(
                tic,
                start=start_date,
                end=end_date,
                auto_adjust=False,  # 保留 Adj Close
                progress=False
            )

            # 处理多级列名
            if temp_df.columns.nlevels != 1:
                temp_df.columns = temp_df.columns.droplevel(1)

            temp_df["tic"] = tic

            if len(temp_df) > 0:
                data_df = pd.concat([data_df, temp_df], axis=0)
                print(f"  ✓ {tic} 下载完成！获得 {len(temp_df)} 行数据")
            else:
                num_failures += 1
                print(f"  ⚠ {tic} 无数据")
        except Exception as e:
            print(f"  ❌ {tic} 下载失败: {e}")
            num_failures += 1

    if num_failures == len(ticker_list):
        raise ValueError("没有成功下载任何数据")

    # 重置索引
    data_df = data_df.reset_index()

    # 标准化列名
    data_df.rename(
        columns={
            "Date": "date",
            "tic": "tic",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Adj Close": "adjcp",
            "Close": "close",
            "Volume": "volume",
        },
        inplace=True,
    )

    # 调整价格（使用复权价格）
    data_df["adj"] = data_df["adjcp"] / data_df["close"]
    for col in ["open", "high", "low", "close"]:
        data_df[col] *= data_df["adj"]
    data_df = data_df.drop(["adjcp", "adj"], axis=1)

    # 添加星期几
    data_df["day"] = data_df["date"].dt.dayofweek

    # 日期格式化为 YYYY-MM-DD
    data_df["date"] = data_df.date.apply(lambda x: x.strftime("%Y-%m-%d"))

    # 删除缺失数据
    data_df = data_df.dropna()
    data_df = data_df.reset_index(drop=True)

    # 排序
    data_df = data_df.sort_values(by=["date", "tic"]).reset_index(drop=True)

    # 四舍五入价格到 2 位小数
    price_cols = ['open', 'high', 'low', 'close']
    for col in price_cols:
        if col in data_df.columns:
            data_df[col] = data_df[col].round(2)

    print(f"\n✓ 下载完成！")
    print(f"  总行数: {len(data_df)}")
    print(f"  数据形状: {data_df.shape}")

    return data_df


def calculate_indicators_pandas(df):
    """
    使用纯 pandas 计算技术指标（无需 stockstats）

    计算常用的技术指标
    """
    print(f"\n{'='*60}")
    print(f"计算技术指标（使用 pandas）")
    print(f"{'='*60}\n")

    result_dfs = []

    for ticker in df['tic'].unique():
        print(f"  计算 {ticker} 的技术指标...")
        ticker_df = df[df['tic'] == ticker].copy().sort_values('date').reset_index(drop=True)

        close = ticker_df['close']
        high = ticker_df['high']
        low = ticker_df['low']
        volume = ticker_df['volume']

        # ==================== MACD ====================
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        ticker_df['macd'] = exp1 - exp2
        ticker_df['macds'] = ticker_df['macd'].ewm(span=9, adjust=False).mean()
        ticker_df['macdh'] = ticker_df['macd'] - ticker_df['macds']

        # ==================== EMA ====================
        for period in [3, 5, 10, 20, 30, 60]:
            ticker_df[f'ema_{period}'] = close.ewm(span=period, adjust=False).mean()

        # ==================== SMA ====================
        for period in [5, 10, 20, 30, 60]:
            ticker_df[f'sma_{period}'] = close.rolling(window=period).mean()

        # ==================== RSI ====================
        for period in [6, 12, 24]:
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            ticker_df[f'rsi_{period}'] = 100 - (100 / (1 + rs))

        # ==================== CCI ====================
        for period in [14, 20]:
            tp = (high + low + close) / 3
            sma_tp = tp.rolling(window=period).mean()
            mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
            ticker_df[f'cci_{period}'] = (tp - sma_tp) / (0.015 * mad)

        # ==================== Bollinger Bands ====================
        period = 20
        sma = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        ticker_df['boll'] = sma
        ticker_df['boll_ub'] = sma + (std * 2)
        ticker_df['boll_lb'] = sma - (std * 2)

        # ==================== ATR ====================
        for period in [14, 21]:
            high_low = high - low
            high_close = np.abs(high - close.shift())
            low_close = np.abs(low - close.shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            ticker_df[f'atr_{period}'] = tr.rolling(window=period).mean()

        # ==================== OBV ====================
        obv = [0]
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.append(obv[-1] + volume.iloc[i])
            elif close.iloc[i] < close.iloc[i-1]:
                obv.append(obv[-1] - volume.iloc[i])
            else:
                obv.append(obv[-1])
        ticker_df['obv'] = obv

        # ==================== Williams %R ====================
        period = 14
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        ticker_df['wr'] = -100 * ((highest_high - close) / (highest_high - lowest_low))

        # 四舍五入所有指标到 2 位小数
        for col in ticker_df.columns:
            if col not in ['date', 'tic', 'day', 'volume'] and ticker_df[col].dtype in ['float64', 'float32']:
                ticker_df[col] = ticker_df[col].round(2)

        result_dfs.append(ticker_df)

    result = pd.concat(result_dfs, ignore_index=True)
    result = result.sort_values(['date', 'tic']).reset_index(drop=True)

    print(f"\n✓ 技术指标计算完成！")
    print(f"  总列数: {len(result.columns)}")
    print(f"  数据形状: {result.shape}")

    return result


def save_data(df, ticker_list, start_date, end_date):
    """保存数据到 CSV"""
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'prices')
    os.makedirs(output_dir, exist_ok=True)

    ticker_str = '_'.join(ticker_list) if len(ticker_list) <= 3 else f"{len(ticker_list)}stocks"
    filename = f"{ticker_str}_{start_date}_{end_date}.csv"
    filepath = os.path.join(output_dir, filename)

    df.to_csv(filepath, index=False)

    file_size = os.path.getsize(filepath) / 1024

    print(f"\n{'='*60}")
    print(f"数据已保存")
    print(f"{'='*60}")
    print(f"文件路径: {filepath}")
    print(f"文件大小: {file_size:.2f} KB")
    print(f"{'='*60}\n")

    # 显示预览
    print("数据预览（前 10 行，部分列）:")
    preview_cols = ['date', 'tic', 'open', 'high', 'low', 'close', 'volume', 'macd', 'rsi_12', 'cci_14', 'boll']
    available_cols = [col for col in preview_cols if col in df.columns]
    print(df[available_cols].head(10).to_string())

    print(f"\n所有列 ({len(df.columns)} 个):")
    print(', '.join(df.columns.tolist()))

    return filepath


def main():
    """主函数"""

    # ==================== 配置参数 ====================

    TICKER_LIST = ['AAPL']  # 股票代码列表
    START_DATE, END_DATE = get_date_range(years=3)  # 时间范围

    # ==================================================

    try:
        # 步骤 1: 下载数据
        df = download_data(TICKER_LIST, START_DATE, END_DATE)

        # 步骤 2: 计算技术指标
        df_with_indicators = calculate_indicators_pandas(df)

        # 步骤 3: 保存数据
        filepath = save_data(df_with_indicators, TICKER_LIST, START_DATE, END_DATE)

        print(f"\n{'='*60}")
        print(f"✅ 所有操作完成！")
        print(f"数据文件: {filepath}")
        print(f"{'='*60}\n")

        return df_with_indicators

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    df = main()
