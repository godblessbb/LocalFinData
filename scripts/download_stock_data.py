#!/usr/bin/env python3
"""
股票数据下载脚本

功能：
- 从 Yahoo Finance 下载股票历史价格数据
- 自动计算多种技术指标（包含不同时间周期）
- 添加 VIX 波动率指数
- 添加 Turbulence 湍流指数（风险指标）
- 数据保存为 CSV 格式到 data/prices/ 目录

使用方法：
    python scripts/download_stock_data.py

配置：
- 可以修改 TICKER_LIST 下载不同股票
- 可以修改 START_DATE 和 END_DATE 调整时间范围
- 可以修改 TECHNICAL_INDICATORS 列表调整指标
"""

import os
import sys
from datetime import datetime, timedelta
import pandas as pd

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from finrl.meta.data_processors.processor_yahoofinance import YahooFinanceProcessor


def get_date_range(years=3):
    """获取日期范围（默认过去3年）"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * years)
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')


def build_technical_indicators():
    """
    构建技术指标列表

    注意：stockstats 库使用特定的命名格式：
    - 带参数的指标：指标名_参数，如 'rsi_6', 'cci_14', 'ema_10'
    - 默认参数的指标：直接使用指标名，如 'macd', 'boll'
    """
    indicators = []

    # ==================== 趋势指标 ====================

    # MACD - 移动平均收敛散度（使用默认参数：12, 26, 9）
    indicators.extend([
        'macd',      # MACD线
        'macds',     # 信号线
        'macdh'      # MACD柱状图
    ])

    # EMA - 指数移动平均（多个时间周期）
    for period in [3, 5, 10, 20, 30, 60]:
        indicators.append(f'ema_{period}')

    # SMA - 简单移动平均（多个时间周期）
    for period in [5, 10, 20, 30, 60]:
        indicators.append(f'sma_{period}')

    # DMA - 双移动平均
    indicators.extend([
        'dma',       # DMA线
        'ama'        # AMA线（自适应移动平均）
    ])


    # ==================== 动量指标 ====================

    # RSI - 相对强弱指标（多个时间周期）
    for period in [6, 12, 24]:
        indicators.append(f'rsi_{period}')

    # CCI - 商品通道指数（多个时间周期）
    for period in [14, 20]:
        indicators.append(f'cci_{period}')

    # DX - 动向指数
    indicators.append('dx')

    # Williams %R - 威廉指标
    indicators.append('wr')

    # KDJ - 随机指标
    indicators.extend([
        'kdjk',      # K值
        'kdjd',      # D值
        'kdjj'       # J值
    ])


    # ==================== 波动率指标 ====================

    # BOLL - 布林带
    indicators.extend([
        'boll',      # 中轨
        'boll_ub',   # 上轨
        'boll_lb'    # 下轨
    ])

    # ATR - 真实波动幅度均值（多个时间周期）
    for period in [14, 21]:
        indicators.append(f'atr_{period}')


    # ==================== 成交量指标 ====================

    # Volume Delta - 成交量变化
    indicators.append('volume_delta')

    # VR - 成交量比率
    indicators.append('vr')

    # VROC - 成交量变化率
    indicators.append('vroc')

    # CR - 能量指标
    indicators.append('cr')


    # ==================== 其他有用指标 ====================

    # TRIX - 三重指数平滑平均线
    indicators.extend([
        'trix',      # TRIX线
        'trixs'      # TRIX信号线
    ])

    # Aroon - 阿隆指标
    indicators.extend([
        'aroon',     # 阿隆指标
        'aroondown', # 下降线
        'aroonup'    # 上升线
    ])

    # OBV - 能量潮
    indicators.append('obv')

    # MFI - 资金流量指标
    indicators.append('mfi')

    return indicators


def download_stock_data(ticker_list, start_date, end_date, time_interval='1d'):
    """
    下载股票数据并添加技术指标

    参数：
        ticker_list: 股票代码列表，如 ['AAPL', 'MSFT', 'GOOGL']
        start_date: 开始日期，格式 'YYYY-MM-DD'
        end_date: 结束日期，格式 'YYYY-MM-DD'
        time_interval: 时间间隔，'1d' = 日线，'1wk' = 周线，'1mo' = 月线

    返回：
        包含价格数据和技术指标的 DataFrame
    """
    print(f"\n{'='*60}")
    print(f"开始下载股票数据")
    print(f"{'='*60}")
    print(f"股票代码: {', '.join(ticker_list)}")
    print(f"时间范围: {start_date} 至 {end_date}")
    print(f"时间间隔: {time_interval}")
    print(f"{'='*60}\n")

    # 初始化处理器
    processor = YahooFinanceProcessor()

    # 步骤 1: 下载原始数据
    print("步骤 1/5: 下载原始价格数据...")
    df = processor.download_data(
        ticker_list=ticker_list,
        start_date=start_date,
        end_date=end_date,
        time_interval=time_interval
    )
    print(f"✓ 下载完成！获得 {len(df)} 行数据")
    print(f"  数据列: {list(df.columns)}")

    # 步骤 2: 清理数据
    print("\n步骤 2/5: 清理数据（处理缺失值和异常值）...")
    df = processor.clean_data(df)
    print(f"✓ 清理完成！剩余 {len(df)} 行数据")

    # 步骤 3: 添加技术指标
    print("\n步骤 3/5: 计算技术指标...")
    tech_indicators = build_technical_indicators()
    print(f"  将计算 {len(tech_indicators)} 个技术指标")
    print(f"  指标列表: {', '.join(tech_indicators[:10])}...")

    df = processor.add_technical_indicator(
        data=df,
        tech_indicator_list=tech_indicators
    )
    print(f"✓ 技术指标计算完成！")
    print(f"  当前数据列数: {len(df.columns)}")

    # 步骤 4: 添加 VIX（仅对多股票有效）
    if len(ticker_list) > 1:
        print("\n步骤 4/5: 添加 VIX 波动率指数...")
        try:
            df = processor.add_vix(df)
            print(f"✓ VIX 添加完成！")
        except Exception as e:
            print(f"⚠ VIX 添加失败: {e}")
    else:
        print("\n步骤 4/5: 跳过 VIX（单股票模式）")

    # 步骤 5: 添加 Turbulence（仅对多股票有效）
    if len(ticker_list) > 1:
        print("\n步骤 5/5: 计算 Turbulence 湍流指数...")
        try:
            df = processor.add_turbulence(df)
            print(f"✓ Turbulence 计算完成！")
        except Exception as e:
            print(f"⚠ Turbulence 计算失败: {e}")
    else:
        print("\n步骤 5/5: 跳过 Turbulence（单股票模式）")

    print(f"\n{'='*60}")
    print(f"数据下载和处理完成！")
    print(f"{'='*60}")
    print(f"最终数据形状: {df.shape}")
    print(f"日期范围: {df['date'].min()} 至 {df['date'].max()}")
    print(f"股票代码: {df['tic'].unique()}")
    print(f"{'='*60}\n")

    return df


def save_data(df, ticker_list, start_date, end_date):
    """
    保存数据到 CSV 文件

    文件命名格式：TICKER_START_END.csv
    例如：AAPL_2021-01-01_2024-01-01.csv
    """
    # 确保输出目录存在
    output_dir = os.path.join(project_root, 'data', 'prices')
    os.makedirs(output_dir, exist_ok=True)

    # 生成文件名
    ticker_str = '_'.join(ticker_list) if len(ticker_list) <= 3 else f"{len(ticker_list)}stocks"
    filename = f"{ticker_str}_{start_date}_{end_date}.csv"
    filepath = os.path.join(output_dir, filename)

    # 保存数据
    df.to_csv(filepath, index=False)

    # 计算文件大小
    file_size = os.path.getsize(filepath) / 1024  # KB

    print(f"✓ 数据已保存到: {filepath}")
    print(f"  文件大小: {file_size:.2f} KB")

    # 显示数据预览
    print(f"\n数据预览（前5行）:")
    print(df.head())

    print(f"\n数据统计信息:")
    print(df.describe())

    return filepath


def main():
    """主函数"""

    # ==================== 配置参数 ====================

    # 股票代码列表（当前仅下载苹果股票）
    TICKER_LIST = ['AAPL']

    # 时间范围（过去3年）
    START_DATE, END_DATE = get_date_range(years=3)

    # 时间间隔（日线数据）
    TIME_INTERVAL = '1d'

    # ==================================================

    try:
        # 下载数据
        df = download_stock_data(
            ticker_list=TICKER_LIST,
            start_date=START_DATE,
            end_date=END_DATE,
            time_interval=TIME_INTERVAL
        )

        # 保存数据
        filepath = save_data(df, TICKER_LIST, START_DATE, END_DATE)

        print(f"\n{'='*60}")
        print(f"所有操作完成！")
        print(f"数据文件位置: {filepath}")
        print(f"{'='*60}\n")

        return df

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    df = main()
