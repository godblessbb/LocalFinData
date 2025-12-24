#!/usr/bin/env python3
"""
Generate simple candlestick + moving average chart.
Supports all MA types: EMA, SMA, WMA, DEMA, TEMA
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np
from pathlib import Path
import argparse

# Configure Chinese font support
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def plot_candlestick_with_ma(
    data_file: str,
    end_date: str = None,
    days: int = 20,
    output_file: str = None,
    ma_types: list = None,
    figsize: tuple = (16, 10),
    dpi: int = 150,
):
    """
    Generate candlestick chart with moving averages.

    Args:
        data_file: Path to CSV file with OHLCV and MA data
        end_date: End date (YYYY-MM-DD), defaults to last date in data
        days: Number of trading days to show
        output_file: Output file path (optional, will auto-generate if not provided)
        ma_types: List of MA types to include ['ema', 'sma', 'wma', 'dema', 'tema']
        figsize: Figure size (width, height)
        dpi: Output resolution

    Returns:
        Path to saved chart
    """
    # Default MA types
    if ma_types is None:
        ma_types = ['ema', 'sma', 'wma', 'dema', 'tema']

    # Load data
    print(f"Loading data from: {data_file}")
    df = pd.read_csv(data_file)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)

    # Filter by end date
    if end_date:
        end_dt = pd.to_datetime(end_date)
        df = df[df['date'] <= end_dt]

    # Take last N days
    df = df.tail(days).reset_index(drop=True)

    if len(df) == 0:
        print("Error: No data in specified date range")
        return None

    actual_start = df['date'].min()
    actual_end = df['date'].max()
    print(f"Date range: {actual_start.date()} to {actual_end.date()}")
    print(f"Data points: {len(df)}")

    # Get ticker from file name or data
    if 'tic' in df.columns:
        ticker = df['tic'].iloc[0]
    else:
        ticker = Path(data_file).stem.split('_')[0].upper()

    # Find all MA columns
    ma_columns = {}
    for col in df.columns:
        for ma_type in ma_types:
            if col.startswith(f'{ma_type}_'):
                period = col.split('_')[1]
                if ma_type not in ma_columns:
                    ma_columns[ma_type] = []
                ma_columns[ma_type].append((col, int(period)))

    # Sort by period
    for ma_type in ma_columns:
        ma_columns[ma_type] = sorted(ma_columns[ma_type], key=lambda x: x[1])

    print(f"\nFound MA columns:")
    for ma_type, cols in ma_columns.items():
        periods = [p for _, p in cols]
        print(f"  {ma_type.upper()}: {periods}")

    # Create figure
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')

    # Plot candlesticks
    dates = df['date'].values
    opens = df['open'].values
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values

    # Calculate candlestick width
    width = 0.6 / max(1, len(dates) / 30)

    for i in range(len(df)):
        date = mdates.date2num(dates[i])
        open_p = opens[i]
        high_p = highs[i]
        low_p = lows[i]
        close_p = closes[i]

        # Bullish or bearish
        if close_p >= open_p:
            color = '#26a69a'  # Green (bullish)
            height = close_p - open_p
            bottom = open_p
        else:
            color = '#ef5350'  # Red (bearish)
            height = open_p - close_p
            bottom = close_p

        # Draw wicks
        ax.plot([date, date], [low_p, high_p], color=color, linewidth=0.8, zorder=1)

        # Draw body
        if height > 0:
            rect = Rectangle(
                (date - width/2, bottom), width, height,
                facecolor=color, edgecolor=color, linewidth=0.8, zorder=2
            )
            ax.add_patch(rect)
        else:
            # Doji
            ax.plot([date - width/2, date + width/2], [close_p, close_p],
                   color=color, linewidth=1.5, zorder=2)

    # Color palette for different MA types
    ma_colors = {
        'ema': ['#2196F3', '#1976D2', '#1565C0', '#0D47A1', '#0288D1', '#0277BD',
                '#01579B', '#039BE5', '#03A9F4', '#29B6F6', '#4FC3F7', '#81D4FA',
                '#B3E5FC', '#E1F5FE', '#00BCD4', '#00ACC1'],
        'sma': ['#FF9800', '#F57C00', '#EF6C00', '#E65100', '#FB8C00', '#FFA726',
                '#FFB74D', '#FFCC80', '#FFE0B2'],
        'wma': ['#4CAF50', '#43A047', '#388E3C'],
        'dema': ['#9C27B0', '#8E24AA', '#7B1FA2'],
        'tema': ['#F44336', '#E53935', '#D32F2F'],
    }

    # Line width by period
    def get_linewidth(period):
        if period <= 10:
            return 1.0
        elif period <= 30:
            return 1.2
        elif period <= 100:
            return 1.5
        else:
            return 1.8

    # Plot MAs
    dates_num = mdates.date2num(df['date'].values)

    for ma_type, cols in ma_columns.items():
        colors = ma_colors.get(ma_type, ['#607D8B'] * 20)
        for i, (col, period) in enumerate(cols):
            values = df[col].values
            valid_mask = ~np.isnan(values)
            if valid_mask.any():
                color = colors[i % len(colors)]
                lw = get_linewidth(period)
                ax.plot(dates_num[valid_mask], values[valid_mask],
                       color=color, linewidth=lw,
                       label=f'{ma_type.upper()}({period})', alpha=0.85)

    # Formatting
    ax.set_ylabel('Price (USD)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_title(f'{ticker} Candlestick with Moving Averages\n{actual_start.date()} to {actual_end.date()}',
                fontsize=14, fontweight='bold', pad=10)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

    # Legend - multiple columns if many MAs
    total_mas = sum(len(cols) for cols in ma_columns.values())
    ncol = min(5, max(2, total_mas // 8 + 1))
    ax.legend(loc='upper left', fontsize=8, framealpha=0.9, ncol=ncol)

    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    plt.tight_layout()

    # Save
    if output_file is None:
        output_dir = Path(data_file).parent
        output_file = output_dir / f"{ticker}_ma_chart_{actual_start.strftime('%Y%m%d')}_{actual_end.strftime('%Y%m%d')}.png"

    output_path = Path(output_file)
    print(f"\nSaving chart to: {output_path}")
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"Chart saved: {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024:.1f} KB")

    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description='Generate candlestick chart with moving averages',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default: last 20 days with all MA types
  python generate_simple_ma_chart.py Sample_Data_AAPL.csv

  # Specify end date and number of days
  python generate_simple_ma_chart.py Sample_Data_AAPL.csv --end 2023-06-30 --days 20

  # Only show specific MA types
  python generate_simple_ma_chart.py Sample_Data_AAPL.csv --ma-types ema,sma

  # Custom output file
  python generate_simple_ma_chart.py Sample_Data_AAPL.csv -o my_chart.png
        """
    )

    parser.add_argument('data_file', help='Path to CSV file with OHLCV and MA data')
    parser.add_argument('--end', '-e', help='End date (YYYY-MM-DD), defaults to last date in data')
    parser.add_argument('--days', '-d', type=int, default=20, help='Number of trading days (default: 20)')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--ma-types', type=str, default='ema,sma,wma,dema,tema',
                       help='MA types to include, comma-separated (default: ema,sma,wma,dema,tema)')
    parser.add_argument('--dpi', type=int, default=150, help='Output resolution (default: 150)')
    parser.add_argument('--figsize', type=str, default='16,10',
                       help='Figure size as width,height (default: 16,10)')

    args = parser.parse_args()

    # Parse MA types
    ma_types = [t.strip().lower() for t in args.ma_types.split(',')]

    # Parse figsize
    try:
        figsize = tuple(float(x) for x in args.figsize.split(','))
    except ValueError:
        print(f"Invalid figsize format: {args.figsize}")
        figsize = (16, 10)

    # Generate chart
    plot_candlestick_with_ma(
        data_file=args.data_file,
        end_date=args.end,
        days=args.days,
        output_file=args.output,
        ma_types=ma_types,
        figsize=figsize,
        dpi=args.dpi,
    )


if __name__ == '__main__':
    main()
