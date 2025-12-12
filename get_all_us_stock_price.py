#!/usr/bin/env python3
"""
批量下载美股所有股票数据

功能：
- 自动获取美股所有股票代码（排除 ETF 和基金）
- 批量下载过去5年的历史数据
- 分批处理，避免内存溢出
- 支持断点续传
- 每只股票单独保存 CSV 文件

使用方法：
    python scripts/download_all_us_stocks.py
"""

import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
from stockstats import StockDataFrame
import time
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def get_all_us_stocks():
    """
    获取美股所有股票代码（排除 ETF 和基金）

    使用多个来源确保列表完整：
    1. S&P 500
    2. NASDAQ 100
    3. NYSE 和 NASDAQ 所有股票
    """
    print("正在获取美股股票列表...")

    all_tickers = set()

    # 方法 1: 使用 pandas 读取 Wikipedia 的 S&P 500 列表
    try:
        sp500_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        sp500_table = pd.read_html(sp500_url)[0]
        sp500_tickers = sp500_table['Symbol'].tolist()
        all_tickers.update(sp500_tickers)
        print(f"  ✓ S&P 500: {len(sp500_tickers)} 只股票")
    except Exception as e:
        print(f"  ⚠ 无法获取 S&P 500 列表: {e}")

    # 方法 2: 使用 FTP 获取 NASDAQ 所有股票
    try:
        nasdaq_url = 'ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt'
        nasdaq_df = pd.read_csv(nasdaq_url, sep='|')
        # 过滤掉 ETF (ETF='Y') 和测试股票
        nasdaq_df = nasdaq_df[
            (nasdaq_df['Test Issue'] == 'N') &
            (nasdaq_df['ETF'] == 'N')
        ]
        nasdaq_tickers = nasdaq_df['Symbol'].tolist()
        # 移除最后一行（通常是文件元数据）
        nasdaq_tickers = [t for t in nasdaq_tickers if '|' not in str(t)]
        all_tickers.update(nasdaq_tickers)
        print(f"  ✓ NASDAQ: {len(nasdaq_tickers)} 只股票")
    except Exception as e:
        print(f"  ⚠ 无法获取 NASDAQ 列表: {e}")

    # 方法 3: 获取 NYSE 股票
    try:
        nyse_url = 'ftp://ftp.nasdaqtrader.com/SymbolDirectory/otherlisted.txt'
        nyse_df = pd.read_csv(nyse_url, sep='|')
        # 只要 NYSE 的股票 (Exchange='A')
        nyse_df = nyse_df[
            (nyse_df['Exchange'] == 'A') &
            (nyse_df['Test Issue'] == 'N') &
            (nyse_df['ETF'] == 'N')
        ]
        nyse_tickers = nyse_df['ACT Symbol'].tolist()
        nyse_tickers = [t for t in nyse_tickers if '|' not in str(t)]
        all_tickers.update(nyse_tickers)
        print(f"  ✓ NYSE: {len(nyse_tickers)} 只股票")
    except Exception as e:
        print(f"  ⚠ 无法获取 NYSE 列表: {e}")

    # 清理股票代码
    all_tickers = sorted([t.strip() for t in all_tickers if t and isinstance(t, str)])

    # 过滤掉明显的 ETF 和基金（通常包含特殊字符）
    all_tickers = [t for t in all_tickers if not any(c in t for c in ['^', '/', '.', '-'])]

    print(f"\n✓ 总共获取到 {len(all_tickers)} 只美股股票")

    return all_tickers


def load_progress():
    """加载下载进度"""
    progress_file = os.path.join(project_root, 'data', 'download_progress.json')
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {'completed': [], 'failed': []}


def save_progress(progress):
    """保存下载进度"""
    progress_file = os.path.join(project_root, 'data', 'download_progress.json')
    os.makedirs(os.path.dirname(progress_file), exist_ok=True)
    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)


def download_single_stock(ticker, start_date, end_date, output_dir):
    """
    下载单个股票的数据并计算技术指标

    返回: (成功标志, 错误信息)
    """
    try:
        # 下载数据
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(
            start=start_date,
            end=end_date,
            interval='1d',
            auto_adjust=False
        )

        if df.empty:
            return False, "无数据"

        # 数据量太少的跳过（可能是新上市或退市股票）
        if len(df) < 100:
            return False, f"数据不足 ({len(df)} 行)"

        # 重置索引
        df = df.reset_index()

        # 标准化列名
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]

        # 处理日期
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.date

        # 四舍五入价格
        price_cols = ['open', 'high', 'low', 'close', 'adj_close']
        for col in price_cols:
            if col in df.columns:
                df[col] = df[col].round(2)

        # 添加股票代码
        df['tic'] = ticker

        # 准备计算技术指标
        working_df = df[['open', 'high', 'low', 'close', 'volume']].copy()
        working_df = working_df.reset_index(drop=True)

        # 使用 StockDataFrame 计算指标
        stock = StockDataFrame.retype(working_df)

        # 计算常用技术指标
        try:
            # MACD
            stock['macd']
            stock['macds']
            stock['macdh']

            # EMA
            for period in [5, 10, 20, 30, 60]:
                stock[f'ema_{period}']

            # SMA
            for period in [5, 10, 20, 30, 60]:
                stock[f'sma_{period}']

            # RSI
            for period in [6, 12, 24]:
                stock[f'rsi_{period}']

            # Bollinger Bands
            stock['boll']
            stock['boll_ub']
            stock['boll_lb']

        except Exception as e:
            # 如果技术指标计算失败，只保存原始数据
            print(f"    ⚠ {ticker} 技术指标计算失败: {e}")
            pass

        # 合并数据
        result_df = pd.DataFrame(stock)
        result_df.insert(0, 'date', df['date'].values)
        result_df.insert(1, 'tic', ticker)

        # 四舍五入所有数值到2位小数
        for col in result_df.columns:
            if col not in ['date', 'tic', 'volume'] and result_df[col].dtype in ['float64', 'float32']:
                result_df[col] = result_df[col].round(2)

        # 保存到单独的 CSV 文件
        filename = f"{ticker}.csv"
        filepath = os.path.join(output_dir, filename)
        result_df.to_csv(filepath, index=False)

        return True, None

    except Exception as e:
        return False, str(e)


def download_all_stocks(tickers, start_date, end_date, batch_size=10):
    """
    批量下载所有股票数据

    参数：
        tickers: 股票代码列表
        start_date: 开始日期
        end_date: 结束日期
        batch_size: 每批处理的股票数量
    """
    output_dir = os.path.join(project_root, 'data', 'prices')
    os.makedirs(output_dir, exist_ok=True)

    # 加载进度
    progress = load_progress()
    completed = set(progress['completed'])
    failed = progress['failed']

    # 过滤掉已完成的
    remaining_tickers = [t for t in tickers if t not in completed]

    print(f"\n{'='*60}")
    print(f"开始批量下载")
    print(f"{'='*60}")
    print(f"总股票数: {len(tickers)}")
    print(f"已完成: {len(completed)}")
    print(f"待下载: {len(remaining_tickers)}")
    print(f"批次大小: {batch_size}")
    print(f"{'='*60}\n")

    total = len(remaining_tickers)
    success_count = 0
    fail_count = 0

    for i, ticker in enumerate(remaining_tickers, 1):
        print(f"[{i}/{total}] 下载 {ticker}...", end=' ')

        success, error = download_single_stock(ticker, start_date, end_date, output_dir)

        if success:
            print(f"✓ 成功")
            success_count += 1
            completed.add(ticker)
        else:
            print(f"✗ 失败: {error}")
            fail_count += 1
            if ticker not in [f['ticker'] for f in failed]:
                failed.append({'ticker': ticker, 'error': error})

        # 每10个股票保存一次进度
        if i % 10 == 0:
            progress = {
                'completed': list(completed),
                'failed': failed
            }
            save_progress(progress)
            print(f"  进度已保存 ({len(completed)}/{len(tickers)})")

        # 每批之间稍微暂停，避免请求过快
        if i % batch_size == 0:
            time.sleep(1)

    # 最终保存进度
    progress = {
        'completed': list(completed),
        'failed': failed
    }
    save_progress(progress)

    print(f"\n{'='*60}")
    print(f"批量下载完成！")
    print(f"{'='*60}")
    print(f"成功: {success_count + len(progress['completed']) - len(remaining_tickers) + success_count}")
    print(f"失败: {len(failed)}")
    print(f"总计: {len(tickers)}")
    print(f"数据保存在: {output_dir}")
    print(f"{'='*60}\n")

    # 显示失败列表
    if failed:
        print("失败的股票:")
        for item in failed[:20]:  # 只显示前20个
            print(f"  {item['ticker']}: {item['error']}")
        if len(failed) > 20:
            print(f"  ... 还有 {len(failed) - 20} 个失败")


def main():
    """主函数"""

    print("\n" + "="*60)
    print("美股所有股票数据批量下载工具")
    print("="*60)

    # 获取日期范围（过去5年）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 5)
    START_DATE = start_date.strftime('%Y-%m-%d')
    END_DATE = end_date.strftime('%Y-%m-%d')

    print(f"时间范围: {START_DATE} 至 {END_DATE}")
    print("="*60 + "\n")

    # 步骤 1: 获取股票列表
    tickers = get_all_us_stocks()

    if not tickers:
        print("❌ 未能获取股票列表，请检查网络连接")
        return

    # 确认是否继续
    print(f"\n准备下载 {len(tickers)} 只股票的数据")
    print("每只股票将保存为单独的 CSV 文件")
    print(f"预计需要时间: {len(tickers) * 2 / 60:.1f} 分钟 (假设每只2秒)")

    response = input("\n是否继续? (y/n): ")
    if response.lower() != 'y':
        print("已取消")
        return

    # 步骤 2: 批量下载
    download_all_stocks(tickers, START_DATE, END_DATE, batch_size=10)

    print("\n✅ 全部完成！")


if __name__ == '__main__':
    main()