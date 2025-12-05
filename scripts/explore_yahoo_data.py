#!/usr/bin/env python3
"""
Yahoo Finance 全面数据获取示例

展示如何获取股票的所有可用数据类型
"""

import yfinance as yf
import pandas as pd
from datetime import datetime

def explore_stock_data(ticker_symbol):
    """
    全面探索一只股票的所有可用数据

    参数：
        ticker_symbol: 股票代码，如 'AAPL'
    """
    print(f"\n{'='*60}")
    print(f"股票代码: {ticker_symbol}")
    print(f"{'='*60}\n")

    ticker = yf.Ticker(ticker_symbol)

    # ==================== 1. 基本信息 ====================
    print("1️⃣  基本信息")
    print("-" * 60)
    try:
        info = ticker.info
        print(f"公司名称: {info.get('longName', 'N/A')}")
        print(f"所属行业: {info.get('sector', 'N/A')}")
        print(f"细分行业: {info.get('industry', 'N/A')}")
        print(f"国家: {info.get('country', 'N/A')}")
        print(f"员工数: {info.get('fullTimeEmployees', 'N/A'):,}")
        print(f"官网: {info.get('website', 'N/A')}")
        print(f"\n简介: {info.get('longBusinessSummary', 'N/A')[:200]}...")
    except Exception as e:
        print(f"❌ 获取失败: {e}")

    # ==================== 2. 市场数据 ====================
    print(f"\n\n2️⃣  市场数据")
    print("-" * 60)
    try:
        info = ticker.info
        print(f"当前价格: ${info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))}")
        print(f"市值: ${info.get('marketCap', 'N/A'):,}")
        print(f"市盈率 P/E: {info.get('trailingPE', 'N/A')}")
        print(f"市净率 P/B: {info.get('priceToBook', 'N/A')}")
        print(f"股息率: {info.get('dividendYield', 0) * 100:.2f}%")
        print(f"Beta 系数: {info.get('beta', 'N/A')}")
        print(f"52周最高: ${info.get('fiftyTwoWeekHigh', 'N/A')}")
        print(f"52周最低: ${info.get('fiftyTwoWeekLow', 'N/A')}")
        print(f"平均成交量: {info.get('averageVolume', 'N/A'):,}")
        print(f"流通股数: {info.get('sharesOutstanding', 'N/A'):,}")
    except Exception as e:
        print(f"❌ 获取失败: {e}")

    # ==================== 3. 财务数据 ====================
    print(f"\n\n3️⃣  财务数据")
    print("-" * 60)

    # 损益表
    print("\n📊 损益表 (最近4个季度):")
    try:
        income = ticker.quarterly_income_stmt
        if not income.empty:
            print(income.head())
            print(f"\n关键指标:")
            if 'Total Revenue' in income.index:
                print(f"  收入: {income.loc['Total Revenue'].iloc[0]:,.0f}")
            if 'Net Income' in income.index:
                print(f"  净利润: {income.loc['Net Income'].iloc[0]:,.0f}")
        else:
            print("  无数据")
    except Exception as e:
        print(f"  ❌ 获取失败: {e}")

    # 资产负债表
    print("\n💰 资产负债表 (最近4个季度):")
    try:
        balance = ticker.quarterly_balance_sheet
        if not balance.empty:
            print(balance.head())
            print(f"\n关键指标:")
            if 'Total Assets' in balance.index:
                print(f"  总资产: {balance.loc['Total Assets'].iloc[0]:,.0f}")
            if 'Total Liabilities Net Minority Interest' in balance.index:
                print(f"  总负债: {balance.loc['Total Liabilities Net Minority Interest'].iloc[0]:,.0f}")
        else:
            print("  无数据")
    except Exception as e:
        print(f"  ❌ 获取失败: {e}")

    # 现金流量表
    print("\n💵 现金流量表 (最近4个季度):")
    try:
        cashflow = ticker.quarterly_cashflow
        if not cashflow.empty:
            print(cashflow.head())
        else:
            print("  无数据")
    except Exception as e:
        print(f"  ❌ 获取失败: {e}")

    # ==================== 4. 分红历史 ====================
    print(f"\n\n4️⃣  分红历史")
    print("-" * 60)
    try:
        dividends = ticker.dividends
        if not dividends.empty:
            print(f"最近10次分红:")
            print(dividends.tail(10))
            print(f"\n总分红次数: {len(dividends)}")
            print(f"最近一次分红: ${dividends.iloc[-1]:.2f}")
            print(f"分红总额: ${dividends.sum():.2f}")
        else:
            print("  该股票不分红")
    except Exception as e:
        print(f"  ❌ 获取失败: {e}")

    # ==================== 5. 股票拆分 ====================
    print(f"\n\n5️⃣  股票拆分历史")
    print("-" * 60)
    try:
        splits = ticker.splits
        if not splits.empty:
            print(splits)
            print(f"\n总拆分次数: {len(splits)}")
        else:
            print("  无股票拆分记录")
    except Exception as e:
        print(f"  ❌ 获取失败: {e}")

    # ==================== 6. 机构持股 ====================
    print(f"\n\n6️⃣  机构持股")
    print("-" * 60)
    try:
        institutional = ticker.institutional_holders
        if institutional is not None and not institutional.empty:
            print("前10大机构持股者:")
            print(institutional.head(10))
        else:
            print("  无数据")
    except Exception as e:
        print(f"  ❌ 获取失败: {e}")

    # ==================== 7. 主要持股者 ====================
    print(f"\n\n7️⃣  主要持股者")
    print("-" * 60)
    try:
        major = ticker.major_holders
        if major is not None and not major.empty:
            print(major)
        else:
            print("  无数据")
    except Exception as e:
        print(f"  ❌ 获取失败: {e}")

    # ==================== 8. 分析师建议 ====================
    print(f"\n\n8️⃣  分析师建议")
    print("-" * 60)
    try:
        recommendations = ticker.recommendations
        if recommendations is not None and not recommendations.empty:
            print("最近10条建议:")
            print(recommendations.tail(10))
        else:
            print("  无数据")
    except Exception as e:
        print(f"  ❌ 获取失败: {e}")

    # ==================== 9. 期权数据 ====================
    print(f"\n\n9️⃣  期权数据")
    print("-" * 60)
    try:
        options_dates = ticker.options
        if options_dates:
            print(f"可用的期权到期日 ({len(options_dates)} 个):")
            print(options_dates[:5], "...")

            # 获取最近一期的期权数据
            opt = ticker.option_chain(options_dates[0])
            print(f"\n到期日 {options_dates[0]} 的期权:")
            print(f"  看涨期权数量: {len(opt.calls)}")
            print(f"  看跌期权数量: {len(opt.puts)}")
            print(f"\n看涨期权示例 (前5个):")
            print(opt.calls[['strike', 'lastPrice', 'volume', 'impliedVolatility']].head())
        else:
            print("  无期权数据")
    except Exception as e:
        print(f"  ❌ 获取失败: {e}")

    # ==================== 10. 财报日历 ====================
    print(f"\n\n🔟 财报日历")
    print("-" * 60)
    try:
        calendar = ticker.calendar
        if calendar is not None and not calendar.empty:
            print(calendar)
        else:
            print("  无数据")
    except Exception as e:
        print(f"  ❌ 获取失败: {e}")

    # ==================== 11. ESG 评分 ====================
    print(f"\n\n1️⃣1️⃣  ESG 可持续性评分")
    print("-" * 60)
    try:
        sustainability = ticker.sustainability
        if sustainability is not None and not sustainability.empty:
            print(sustainability)
        else:
            print("  无数据")
    except Exception as e:
        print(f"  ❌ 获取失败: {e}")

    # ==================== 12. 内部交易 ====================
    print(f"\n\n1️⃣2️⃣  内部人士持股")
    print("-" * 60)
    try:
        insider = ticker.insider_holders
        if insider is not None and not insider.empty:
            print(insider)
        else:
            print("  无数据")
    except Exception as e:
        print(f"  ❌ 获取失败: {e}")

    print(f"\n\n内部交易记录")
    print("-" * 60)
    try:
        insider_trades = ticker.insider_transactions
        if insider_trades is not None and not insider_trades.empty:
            print("最近10条交易:")
            print(insider_trades.head(10))
        else:
            print("  无数据")
    except Exception as e:
        print(f"  ❌ 获取失败: {e}")

    print(f"\n{'='*60}")
    print(f"数据探索完成！")
    print(f"{'='*60}\n")


def main():
    """主函数"""
    # 示例：探索苹果公司的所有数据
    ticker_symbol = 'AAPL'

    print("\n" + "="*60)
    print("Yahoo Finance 全面数据获取示例")
    print("="*60)
    print(f"目标股票: {ticker_symbol}")
    print("="*60)

    explore_stock_data(ticker_symbol)

    print("\n💡 提示：")
    print("1. 修改 ticker_symbol 变量可以查看其他股票")
    print("2. 并非所有股票都有完整数据")
    print("3. 某些数据可能需要付费订阅")
    print("4. 数据更新频率：实时数据延迟15-20分钟")


if __name__ == '__main__':
    main()
