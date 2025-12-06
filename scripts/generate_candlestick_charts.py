#!/usr/bin/env python3
"""
生成股票 K 线图
读取 data/prices 下的股票数据，生成专业的 K 线图并保存到 data/candles/<TICKER>/ 目录
文件名格式：<开始日期>_to_<结束日期>.png
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np
import os
import sys
import argparse
from pathlib import Path

# 项目根目录（用于定位 data 目录）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "prices"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "candles"

# 配置中文字体支持
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


class CandlestickChartGenerator:
    """K 线图生成器"""

    def __init__(self, data_file, ticker, output_dir=DEFAULT_OUTPUT_DIR, ma_periods=None):
        """
        初始化 K 线图生成器

        Args:
            data_file: 股票数据文件路径
            ticker: 股票代码
            output_dir: 输出目录（相对于 data 目录）
            ma_periods: 均线周期列表，例如 [5, 20, 50, 100, 200]
        """
        self.data_file = Path(data_file)
        self.ticker = ticker.upper()

        # 设置均线周期（默认使用 5, 20, 50, 100, 200 日 EMA）
        if ma_periods is None:
            self.ma_periods = [5, 20, 50, 100, 200]
        else:
            self.ma_periods = sorted(ma_periods)  # 排序以便显示

        # 设置输出目录（允许传入绝对/相对路径）
        output_dir_path = Path(output_dir)
        if not output_dir_path.is_absolute():
            output_dir_path = (Path(__file__).parent / output_dir_path).resolve()

        self.output_dir = output_dir_path / self.ticker
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 读取数据
        self.df = None
        self.load_data()

    def load_data(self):
        """加载股票数据"""
        print(f"正在读取数据: {self.data_file}")

        # 读取 CSV
        self.df = pd.read_csv(self.data_file)

        # 转换日期格式
        self.df['date'] = pd.to_datetime(self.df['date'])

        # 按日期排序
        self.df = self.df.sort_values('date').reset_index(drop=True)

        print(f"数据加载完成: {len(self.df)} 行")
        print(f"日期范围: {self.df['date'].min().date()} 至 {self.df['date'].max().date()}")

    def split_data_by_years(self, max_years=2):
        """
        将数据按指定年限切分成多个时间段

        Args:
            max_years: 每个时间段的最大年限（默认2年）

        Returns:
            list of tuples: [(start_date, end_date), ...]
        """
        if len(self.df) == 0:
            return []

        min_date = self.df['date'].min()
        max_date = self.df['date'].max()

        # 计算总天数
        total_days = (max_date - min_date).days

        # 如果数据跨度小于等于 max_years，返回整个范围
        if total_days <= max_years * 365:
            return [(min_date, max_date)]

        # 切分数据
        periods = []
        current_start = min_date

        while current_start < max_date:
            # 计算当前段的结束日期（max_years后）
            current_end = current_start + pd.DateOffset(years=max_years)

            # 确保不超过最大日期
            if current_end > max_date:
                current_end = max_date

            periods.append((current_start, current_end))

            # 下一段从当前段结束的下一天开始
            current_start = current_end + pd.DateOffset(days=1)

            # 如果剩余时间太短（少于6个月），合并到前一段
            if (max_date - current_start).days < 180 and len(periods) > 0:
                # 更新最后一段的结束日期
                periods[-1] = (periods[-1][0], max_date)
                break

        return periods

    def plot_all_periods(self, max_years=2, dpi=150):
        """
        自动将数据按年限切分并生成所有时间段的 K 线图

        Args:
            max_years: 每个时间段的最大年限（默认2年）
            dpi: 图像分辨率

        Returns:
            生成的文件路径列表
        """
        periods = self.split_data_by_years(max_years)

        if not periods:
            print("没有可用数据")
            return []

        print(f"\n数据将被切分为 {len(periods)} 个时间段（每段最多 {max_years} 年）：")
        for i, (start, end) in enumerate(periods, 1):
            days = (end - start).days
            print(f"  {i}. {start.date()} 至 {end.date()} ({days} 天)")

        # 生成每个时间段的图表
        output_files = []
        for i, (start, end) in enumerate(periods, 1):
            print(f"\n{'='*60}")
            print(f"正在生成第 {i}/{len(periods)} 个图表...")
            filepath = self.plot_candlestick(
                start_date=start,
                end_date=end,
                dpi=dpi
            )
            if filepath:
                output_files.append(filepath)

        return output_files

    def plot_candlestick(self, start_date=None, end_date=None, dpi=150, figsize=(16, 14)):
        """
        绘制 K 线图（完整 6 面板布局）

        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            dpi: 图像分辨率
            figsize: 图像尺寸

        Returns:
            保存的文件路径
        """
        # 筛选日期范围
        df = self.df.copy()
        if start_date:
            df = df[df['date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['date'] <= pd.to_datetime(end_date)]

        if len(df) == 0:
            print("错误：指定日期范围内没有数据")
            return None

        # 获取实际的日期范围
        actual_start = df['date'].min()
        actual_end = df['date'].max()

        print(f"\n正在生成 K 线图...")
        print(f"日期范围: {actual_start.date()} 至 {actual_end.date()}")
        print(f"数据点数: {len(df)}")

        # 创建图形（增加高度以容纳更多面板）
        fig = plt.figure(figsize=figsize, facecolor='white')

        # 创建 6 个子图 - 专业级完整布局
        # 面板高度分配：40% + 12% + 12% + 12% + 12% + 12% = 100%
        ax1 = plt.subplot2grid((25, 1), (0, 0), rowspan=10)   # 面板1: K线 + 均线 + 布林带 + SAR (40%)
        ax2 = plt.subplot2grid((25, 1), (10, 0), rowspan=3, sharex=ax1)  # 面板2: MACD (12%)
        ax3 = plt.subplot2grid((25, 1), (13, 0), rowspan=3, sharex=ax1)  # 面板3: Stochastic (12%)
        ax4 = plt.subplot2grid((25, 1), (16, 0), rowspan=3, sharex=ax1)  # 面板4: RSI (12%)
        ax5 = plt.subplot2grid((25, 1), (19, 0), rowspan=3, sharex=ax1)  # 面板5: ADX + ATR (12%)
        ax6 = plt.subplot2grid((25, 1), (22, 0), rowspan=3, sharex=ax1)  # 面板6: 成交量 + OBV (12%)

        # 绘制各个面板
        self._plot_candlesticks(ax1, df)  # K线
        self._plot_indicators(ax1, df)     # 均线 + 布林带
        self._plot_sar(ax1, df)            # SAR 转向点

        self._plot_macd(ax2, df)           # MACD
        self._plot_stochastic(ax3, df)     # Stochastic (KDJ)
        self._plot_rsi(ax4, df)            # RSI
        self._plot_adx_atr(ax5, df)        # ADX + ATR
        self._plot_volume_obv(ax6, df)     # 成交量 + OBV

        # 设置标题
        fig.suptitle(f'{self.ticker} 股票技术分析图表', fontsize=16, fontweight='bold', y=0.995)

        # 调整布局
        plt.tight_layout(rect=[0, 0, 1, 0.99])

        # 生成文件名（纯数字格式：20221011_20241010）
        filename = f"{actual_start.strftime('%Y%m%d')}_{actual_end.strftime('%Y%m%d')}.png"
        filepath = self.output_dir / filename

        # 保存图像
        print(f"\n正在保存图像到: {filepath}")
        plt.savefig(filepath, dpi=dpi, bbox_inches='tight', facecolor='white')
        plt.close()

        print(f"✓ 图像已保存: {filepath}")
        print(f"  文件大小: {filepath.stat().st_size / 1024:.1f} KB")

        return str(filepath)

    def _plot_candlesticks(self, ax, df):
        """绘制 K 线"""
        dates = df['date'].values
        opens = df['open'].values
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values

        # 计算 K 线宽度
        if len(dates) > 1:
            width = 0.6 / max(1, len(dates) / 100)
        else:
            width = 0.6

        # 绘制每根 K 线
        for i in range(len(df)):
            date = mdates.date2num(dates[i])
            open_p = opens[i]
            high_p = highs[i]
            low_p = lows[i]
            close_p = closes[i]

            # 判断涨跌
            if close_p >= open_p:
                # 阳线（绿色）
                color = '#26a69a'
                body_color = '#26a69a'
                height = close_p - open_p
                bottom = open_p
            else:
                # 阴线（红色）
                color = '#ef5350'
                body_color = '#ef5350'
                height = open_p - close_p
                bottom = close_p

            # 绘制上下影线
            ax.plot([date, date], [low_p, high_p], color=color, linewidth=0.8, zorder=1)

            # 绘制实体
            if height > 0:
                rect = Rectangle((date - width/2, bottom), width, height,
                               facecolor=body_color, edgecolor=color, linewidth=0.8, zorder=2)
                ax.add_patch(rect)
            else:
                # 十字星
                ax.plot([date - width/2, date + width/2], [close_p, close_p],
                       color=color, linewidth=1.5, zorder=2)

        ax.set_ylabel('价格 (USD)', fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.set_title(f'{self.ticker} K线图', fontsize=12, fontweight='bold', pad=10)

    def _plot_indicators(self, ax, df):
        """绘制技术指标（均线、布林带）"""
        dates = mdates.date2num(df['date'].values)

        # 绘制布林带
        if 'bb_upper_20' in df.columns and 'bb_lower_20' in df.columns:
            bb_upper = df['bb_upper_20'].values
            bb_lower = df['bb_lower_20'].values

            # 移除 NaN
            valid_mask = ~(np.isnan(bb_upper) | np.isnan(bb_lower))
            if valid_mask.any():
                ax.fill_between(dates[valid_mask], bb_upper[valid_mask], bb_lower[valid_mask],
                              alpha=0.15, color='gray', label='布林带')
                ax.plot(dates[valid_mask], bb_upper[valid_mask], '--', color='gray',
                       linewidth=0.8, alpha=0.7)
                ax.plot(dates[valid_mask], bb_lower[valid_mask], '--', color='gray',
                       linewidth=0.8, alpha=0.7)

        # 绘制移动平均线（使用动态配置的周期）
        # 定义颜色调色板（最多支持10种均线）
        colors = ['#2196F3', '#FF9800', '#9C27B0', '#4CAF50', '#F44336',
                  '#00BCD4', '#FF5722', '#3F51B5', '#E91E63', '#009688']

        for i, period in enumerate(self.ma_periods):
            col = f'ema_{period}'
            if col in df.columns:
                values = df[col].values
                valid_mask = ~np.isnan(values)
                if valid_mask.any():
                    color = colors[i % len(colors)]
                    # 短期均线用细线，长期均线用粗线
                    linewidth = 1.2 if period <= 20 else 1.5 if period <= 100 else 1.8
                    ax.plot(dates[valid_mask], values[valid_mask],
                           color=color, linewidth=linewidth,
                           label=f'EMA {period}', alpha=0.85)

        ax.legend(loc='upper left', fontsize=9, framealpha=0.9, ncol=2)

    def _plot_macd(self, ax, df):
        """绘制 MACD 指标"""
        if 'macd' not in df.columns:
            ax.text(0.5, 0.5, 'MACD 数据不可用', ha='center', va='center',
                   transform=ax.transAxes)
            return

        dates = mdates.date2num(df['date'].values)
        macd = df['macd'].values
        signal = df['macds'].values if 'macds' in df.columns else df['macd_signal'].values
        hist = df['macdh'].values if 'macdh' in df.columns else df['macd_hist'].values

        # 移除 NaN
        valid_mask = ~(np.isnan(macd) | np.isnan(signal) | np.isnan(hist))

        if valid_mask.any():
            dates_valid = dates[valid_mask]
            macd_valid = macd[valid_mask]
            signal_valid = signal[valid_mask]
            hist_valid = hist[valid_mask]

            # 绘制柱状图
            colors = ['#26a69a' if h >= 0 else '#ef5350' for h in hist_valid]
            ax.bar(dates_valid, hist_valid, width=0.6, color=colors, alpha=0.6, label='MACD Hist')

            # 绘制 MACD 线和信号线
            ax.plot(dates_valid, macd_valid, color='#2196F3', linewidth=1.5, label='MACD')
            ax.plot(dates_valid, signal_valid, color='#FF9800', linewidth=1.5, label='Signal')

            # 零线
            ax.axhline(y=0, color='black', linestyle='--', linewidth=0.5, alpha=0.5)

        ax.set_ylabel('MACD', fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.legend(loc='upper left', fontsize=8, framealpha=0.9)

    def _plot_rsi(self, ax, df):
        """绘制 RSI 指标"""
        if 'rsi_14' not in df.columns:
            ax.text(0.5, 0.5, 'RSI 数据不可用', ha='center', va='center',
                   transform=ax.transAxes)
            return

        dates = mdates.date2num(df['date'].values)
        rsi = df['rsi_14'].values

        # 移除 NaN
        valid_mask = ~np.isnan(rsi)

        if valid_mask.any():
            dates_valid = dates[valid_mask]
            rsi_valid = rsi[valid_mask]

            # 绘制 RSI 线
            ax.plot(dates_valid, rsi_valid, color='#9C27B0', linewidth=1.5, label='RSI 14')

            # 超买超卖线
            ax.axhline(y=70, color='#ef5350', linestyle='--', linewidth=1, alpha=0.7, label='超买(70)')
            ax.axhline(y=30, color='#26a69a', linestyle='--', linewidth=1, alpha=0.7, label='超卖(30)')
            ax.axhline(y=50, color='black', linestyle='--', linewidth=0.5, alpha=0.3)

            # 填充超买超卖区域
            ax.fill_between(dates_valid, 70, 100, alpha=0.1, color='red')
            ax.fill_between(dates_valid, 0, 30, alpha=0.1, color='green')

        ax.set_ylim(0, 100)
        ax.set_ylabel('RSI', fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.legend(loc='upper left', fontsize=8, framealpha=0.9)

    def _plot_sar(self, ax, df):
        """在 K 线图上绘制 SAR 转向点"""
        if 'sar' not in df.columns:
            return

        dates = mdates.date2num(df['date'].values)
        sar = df['sar'].values
        close = df['close'].values

        # 移除 NaN
        valid_mask = ~np.isnan(sar)

        if valid_mask.any():
            dates_valid = dates[valid_mask]
            sar_valid = sar[valid_mask]
            close_valid = close[valid_mask]

            # SAR 在价格下方时用绿色（看涨），在价格上方时用红色（看跌）
            colors = ['#26a69a' if s < c else '#ef5350' for s, c in zip(sar_valid, close_valid)]

            # 绘制 SAR 点
            ax.scatter(dates_valid, sar_valid, c=colors, s=20, marker='o',
                      alpha=0.7, zorder=5, label='SAR')

    def _plot_stochastic(self, ax, df):
        """绘制 Stochastic (KDJ) 指标"""
        # 优先使用 14 日，其次 9 日
        k_col = 'stoch_k_14' if 'stoch_k_14' in df.columns else 'stoch_k_9'
        d_col = 'stoch_d_14' if 'stoch_d_14' in df.columns else 'stoch_d_9'
        j_col = 'stoch_j_14' if 'stoch_j_14' in df.columns else 'stoch_j_9'

        if k_col not in df.columns:
            ax.text(0.5, 0.5, 'Stochastic 数据不可用', ha='center', va='center',
                   transform=ax.transAxes)
            return

        dates = mdates.date2num(df['date'].values)
        k_values = df[k_col].values
        d_values = df[d_col].values if d_col in df.columns else None
        j_values = df[j_col].values if j_col in df.columns else None

        # 移除 NaN
        valid_mask = ~np.isnan(k_values)
        if d_values is not None:
            valid_mask &= ~np.isnan(d_values)

        if valid_mask.any():
            dates_valid = dates[valid_mask]
            k_valid = k_values[valid_mask]

            # 绘制 %K 线（快线）
            ax.plot(dates_valid, k_valid, color='#2196F3', linewidth=1.5, label='%K (快线)')

            # 绘制 %D 线（慢线）
            if d_values is not None:
                d_valid = d_values[valid_mask]
                ax.plot(dates_valid, d_valid, color='#FF9800', linewidth=1.5, label='%D (慢线)')

            # 绘制 %J 线（超快线）
            if j_values is not None:
                j_mask = ~np.isnan(j_values)
                if j_mask.any():
                    dates_j = dates[j_mask]
                    j_valid = j_values[j_mask]
                    ax.plot(dates_j, j_valid, color='#9C27B0', linewidth=1.2,
                           linestyle='--', alpha=0.7, label='%J')

            # 超买超卖线
            ax.axhline(y=80, color='#ef5350', linestyle='--', linewidth=1, alpha=0.7, label='超买(80)')
            ax.axhline(y=20, color='#26a69a', linestyle='--', linewidth=1, alpha=0.7, label='超卖(20)')
            ax.axhline(y=50, color='black', linestyle='--', linewidth=0.5, alpha=0.3)

            # 填充超买超卖区域
            ax.fill_between(dates_valid, 80, 100, alpha=0.1, color='red')
            ax.fill_between(dates_valid, 0, 20, alpha=0.1, color='green')

        ax.set_ylim(0, 100)
        ax.set_ylabel('Stochastic', fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.legend(loc='upper left', fontsize=8, framealpha=0.9)

    def _plot_adx_atr(self, ax, df):
        """绘制 ADX 和 ATR 指标（双 Y 轴）"""
        dates = mdates.date2num(df['date'].values)

        # 创建第二个 Y 轴
        ax2 = ax.twinx()

        # 绘制 ADX（左轴）
        if 'adx' in df.columns:
            adx = df['adx'].values
            valid_mask = ~np.isnan(adx)

            if valid_mask.any():
                dates_valid = dates[valid_mask]
                adx_valid = adx[valid_mask]
                ax.plot(dates_valid, adx_valid, color='#9C27B0', linewidth=2, label='ADX', alpha=0.9)

                # ADX 参考线
                ax.axhline(y=25, color='#ef5350', linestyle='--', linewidth=1, alpha=0.5, label='强趋势(25)')
                ax.axhline(y=20, color='gray', linestyle='--', linewidth=0.5, alpha=0.3)

        # 绘制 +DI 和 -DI（左轴）
        if 'pos_di' in df.columns and 'neg_di' in df.columns:
            pos_di = df['pos_di'].values
            neg_di = df['neg_di'].values
            valid_mask = ~(np.isnan(pos_di) | np.isnan(neg_di))

            if valid_mask.any():
                dates_valid = dates[valid_mask]
                ax.plot(dates_valid, pos_di[valid_mask], color='#26a69a',
                       linewidth=1.2, alpha=0.7, label='+DI')
                ax.plot(dates_valid, neg_di[valid_mask], color='#ef5350',
                       linewidth=1.2, alpha=0.7, label='-DI')

        # 绘制 ATR（右轴）
        if 'atr_14' in df.columns:
            atr = df['atr_14'].values
            valid_mask = ~np.isnan(atr)

            if valid_mask.any():
                dates_valid = dates[valid_mask]
                atr_valid = atr[valid_mask]
                ax2.plot(dates_valid, atr_valid, color='#FF9800', linewidth=1.5,
                        linestyle='--', alpha=0.8, label='ATR 14')
                ax2.fill_between(dates_valid, 0, atr_valid, alpha=0.1, color='orange')

        # 设置标签和图例
        ax.set_ylabel('ADX / DMI', fontsize=10, fontweight='bold', color='#9C27B0')
        ax2.set_ylabel('ATR', fontsize=10, fontweight='bold', color='#FF9800')
        ax.set_ylim(0, 100)
        ax.tick_params(axis='y', labelcolor='#9C27B0')
        ax2.tick_params(axis='y', labelcolor='#FF9800')

        # 合并图例
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=8, framealpha=0.9)

        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

    def _plot_volume_obv(self, ax, df):
        """绘制成交量和 OBV（双 Y 轴）"""
        dates = mdates.date2num(df['date'].values)
        volume = df['volume'].values
        close = df['close'].values

        # 创建第二个 Y 轴
        ax2 = ax.twinx()

        # 根据价格涨跌设置成交量颜色
        vol_colors = []
        for i in range(len(volume)):
            if i == 0:
                vol_colors.append('#808080')  # 第一根为灰色
            elif close[i] >= close[i-1]:
                vol_colors.append('#26a69a')  # 绿色（涨）
            else:
                vol_colors.append('#ef5350')  # 红色（跌）

        # 绘制成交量柱状图（左轴）
        ax.bar(dates, volume, width=0.6, color=vol_colors, alpha=0.6, label='成交量')

        # 绘制成交量移动平均线（左轴）
        if 'vol_ma_5' in df.columns:
            vol_ma = df['vol_ma_5'].values
            valid_mask = ~np.isnan(vol_ma)
            if valid_mask.any():
                ax.plot(dates[valid_mask], vol_ma[valid_mask], color='#2196F3',
                       linewidth=1.2, alpha=0.8, label='Vol MA 5')

        if 'vol_ma_20' in df.columns:
            vol_ma = df['vol_ma_20'].values
            valid_mask = ~np.isnan(vol_ma)
            if valid_mask.any():
                ax.plot(dates[valid_mask], vol_ma[valid_mask], color='#FF9800',
                       linewidth=1.2, alpha=0.8, label='Vol MA 20')

        # 绘制 OBV（右轴）
        if 'obv' in df.columns:
            obv = df['obv'].values
            valid_mask = ~np.isnan(obv)

            if valid_mask.any():
                dates_valid = dates[valid_mask]
                obv_valid = obv[valid_mask]
                ax2.plot(dates_valid, obv_valid, color='#9C27B0', linewidth=2,
                        alpha=0.8, label='OBV')

        # 设置标签和图例
        ax.set_ylabel('成交量', fontsize=10, fontweight='bold', color='#26a69a')
        ax2.set_ylabel('OBV (能量潮)', fontsize=10, fontweight='bold', color='#9C27B0')
        ax.set_xlabel('日期', fontsize=10, fontweight='bold')
        ax.tick_params(axis='y', labelcolor='#26a69a')
        ax2.tick_params(axis='y', labelcolor='#9C27B0')

        # 合并图例
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=8, framealpha=0.9)

        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

        # 格式化 x 轴日期（只在最后一个面板显示）
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='生成股票 K 线图',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 自动切分并生成所有时间段的 K 线图（推荐）
  python generate_candlestick_charts.py AAPL --auto-split

  # 自定义切分年限和均线
  python generate_candlestick_charts.py AAPL --auto-split --max-years 1 --ma-periods 5,10,20,50,100,200

  # 生成指定日期范围的 K 线图
  python generate_candlestick_charts.py AAPL --start 2024-01-01 --end 2024-12-31

  # 生成多个股票的 K 线图（自动切分）
  python generate_candlestick_charts.py AAPL TSLA GOOGL --auto-split

  # 高分辨率输出
  python generate_candlestick_charts.py AAPL --auto-split --dpi 300
        """
    )

    parser.add_argument('tickers', nargs='+', help='股票代码（可以指定多个）')
    parser.add_argument('--start', '-s', help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end', '-e', help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--auto-split', action='store_true',
                       help='自动按年限切分数据（推荐）')
    parser.add_argument('--max-years', type=int, default=2,
                       help='每个时间段的最大年限（默认: 2）')
    parser.add_argument('--ma-periods', type=str, default='5,20,50,100,200',
                       help='均线周期，用逗号分隔（默认: 5,20,50,100,200）')
    parser.add_argument(
        '--output-dir',
        '-o',
        default=str(DEFAULT_OUTPUT_DIR),
        help='输出目录，默认写入项目 data/candles'
    )
    parser.add_argument('--dpi', type=int, default=150, help='图像分辨率（默认: 150）')
    parser.add_argument(
        '--data-dir',
        default=str(DEFAULT_DATA_DIR),
        help='数据目录，默认读取项目 data/prices'
    )

    args = parser.parse_args()

    # 解析均线周期
    try:
        ma_periods = [int(x.strip()) for x in args.ma_periods.split(',')]
        ma_periods = sorted(ma_periods)  # 排序
    except ValueError:
        print(f"错误：均线周期格式不正确: {args.ma_periods}")
        print("正确格式示例: 5,20,50,100,200")
        sys.exit(1)

    print("=" * 60)
    print("股票 K 线图生成器")
    print("=" * 60)
    print(f"配置:")
    print(f"  - 均线周期: {', '.join(map(str, ma_periods))}")
    print(f"  - 自动切分: {'是' if args.auto_split else '否'}")
    if args.auto_split:
        print(f"  - 每段最多: {args.max_years} 年")
    print(f"  - 图像分辨率: {args.dpi} DPI")

    # 获取数据目录（相对于脚本位置）
    data_dir = Path(args.data_dir).expanduser().resolve()

    if not data_dir.exists():
        print(f"错误：数据目录不存在: {data_dir}")
        sys.exit(1)

    # 处理每个股票
    for ticker in args.tickers:
        ticker_upper = ticker.upper()
        print(f"\n处理股票: {ticker_upper}")
        print("-" * 60)

        # 查找数据文件（支持多种文件名格式）
        possible_files = [
            data_dir / f"{ticker_upper}.csv",
            data_dir / f"{ticker_upper}_with_indicators.csv",
            data_dir / f"{ticker.lower()}.csv",
            data_dir / f"{ticker.lower()}_with_indicators.csv",
        ]

        data_file = None
        for f in possible_files:
            if f.exists():
                data_file = f
                break

        if data_file is None:
            print(f"警告：数据文件不存在，跳过")
            print(f"  尝试过的文件名: {[f.name for f in possible_files]}")
            continue

        print(f"找到数据文件: {data_file.name}")

        try:
            # 创建图表生成器
            generator = CandlestickChartGenerator(
                data_file=str(data_file),
                ticker=ticker_upper,
                output_dir=args.output_dir,
                ma_periods=ma_periods
            )

            # 根据参数决定生成方式
            if args.auto_split:
                # 自动切分并生成多个时间段的图表
                output_paths = generator.plot_all_periods(
                    max_years=args.max_years,
                    dpi=args.dpi
                )
                if output_paths:
                    print(f"\n✓ 成功生成 {len(output_paths)} 个图表")
                    for path in output_paths:
                        print(f"  - {path}")
                else:
                    print(f"✗ 图表生成失败")
            else:
                # 生成单个时间段的图表
                output_path = generator.plot_candlestick(
                    start_date=args.start,
                    end_date=args.end,
                    dpi=args.dpi
                )

                if output_path:
                    print(f"✓ 成功生成图表")
                else:
                    print(f"✗ 图表生成失败")

        except Exception as e:
            print(f"✗ 错误: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("所有任务完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
