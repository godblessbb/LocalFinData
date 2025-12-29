#!/usr/bin/env python3
"""
Find top price changes over 10-day windows in 2024.
Scans all CSV files in data/prices and finds the top 2000 highest and lowest
10-day price changes. Only processes stocks that have news data available.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import argparse
from datetime import datetime


def calculate_price_changes(
    data_dir: str,
    news_dir: str,
    start_date: str = '2024-01-01',
    end_date: str = '2024-12-31',
    window: int = 10,
    top_n: int = 2000,
    output_dir: str = None,
):
    """
    Calculate price changes over sliding windows for all stocks.

    Args:
        data_dir: Directory containing price CSV files
        news_dir: Directory containing news CSV files (for filtering)
        start_date: Start date for filtering (YYYY-MM-DD)
        end_date: End date for filtering (YYYY-MM-DD)
        window: Number of trading days for the window
        top_n: Number of top/bottom results to return
        output_dir: Output directory for results (defaults to data_dir)
    """
    data_path = Path(data_dir)
    news_path = Path(news_dir)
    if output_dir is None:
        output_dir = data_path.parent
    else:
        output_dir = Path(output_dir)

    # Step 1: Get list of tickers with news data
    news_files = set(f.stem.upper() for f in news_path.glob('*.csv'))
    print(f"Found {len(news_files)} tickers with news data in {news_path}")

    # Find all CSV files in prices
    csv_files = list(data_path.glob('*.csv'))
    print(f"Found {len(csv_files)} CSV files in {data_path}")

    # Filter to only those with news
    csv_files_with_news = [f for f in csv_files if f.stem.upper() in news_files]
    print(f"Processing {len(csv_files_with_news)} files that have news data")

    all_changes = []
    processed_count = 0

    for csv_file in csv_files_with_news:
        try:
            df = pd.read_csv(csv_file)

            # Check required columns
            required_cols = ['date', 'open', 'close', 'volume']
            missing_cols = [c for c in required_cols if c not in df.columns]
            if missing_cols:
                print(f"Skipping {csv_file.name}: missing columns {missing_cols}")
                continue

            # Get ticker from 'tic' column or filename
            if 'tic' in df.columns:
                ticker = df['tic'].iloc[0]
            else:
                ticker = csv_file.stem.upper()

            # Convert date and filter
            df['date'] = pd.to_datetime(df['date'])
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
            df = df.sort_values('date').reset_index(drop=True)

            if len(df) < window + 1:
                print(f"Skipping {ticker}: not enough data ({len(df)} rows)")
                continue

            # Pre-calculate values for anchors
            # Absolute daily return
            df['daily_return'] = df['close'].pct_change().abs()

            # Gap: |open_t - close_{t-1}|
            df['gap'] = (df['open'] - df['close'].shift(1)).abs()

            # Volume z-score (rolling would be better but use full period for simplicity)
            vol_mean = df['volume'].mean()
            vol_std = df['volume'].std()
            if vol_std > 0:
                df['volume_zscore'] = (df['volume'] - vol_mean) / vol_std
            else:
                df['volume_zscore'] = 0

            # Calculate price changes for each window
            for i in range(len(df) - window):
                window_df = df.iloc[i:i + window + 1].copy()

                t0_row = df.iloc[i]
                t10_row = df.iloc[i + window]

                t0_date = t0_row['date']
                t0_close = t0_row['close']
                t10_date = t10_row['date']
                t10_close = t10_row['close']

                if t0_close == 0:
                    continue

                price_change = (t10_close - t0_close) / t0_close

                # Anchor A: Maximum absolute return day
                # Skip first day since daily_return is NaN
                window_returns = window_df.iloc[1:].copy()
                if len(window_returns) > 0 and window_returns['daily_return'].notna().any():
                    anchor_a_idx = window_returns['daily_return'].idxmax()
                    anchor_a_date = df.loc[anchor_a_idx, 'date'].strftime('%Y-%m-%d')
                    anchor_a_value = round(df.loc[anchor_a_idx, 'daily_return'], 6)
                else:
                    anchor_a_date = None
                    anchor_a_value = None

                # Anchor B: Maximum gap day
                # Skip first day since gap uses shift
                window_gaps = window_df.iloc[1:].copy()
                if len(window_gaps) > 0 and window_gaps['gap'].notna().any():
                    anchor_b_idx = window_gaps['gap'].idxmax()
                    anchor_b_date = df.loc[anchor_b_idx, 'date'].strftime('%Y-%m-%d')
                    anchor_b_value = round(df.loc[anchor_b_idx, 'gap'], 6)
                else:
                    anchor_b_date = None
                    anchor_b_value = None

                # Anchor C: Maximum volume z-score day
                if window_df['volume_zscore'].notna().any():
                    anchor_c_idx = window_df['volume_zscore'].idxmax()
                    anchor_c_date = df.loc[anchor_c_idx, 'date'].strftime('%Y-%m-%d')
                    anchor_c_value = round(df.loc[anchor_c_idx, 'volume_zscore'], 6)
                else:
                    anchor_c_date = None
                    anchor_c_value = None

                all_changes.append({
                    'start_date': t0_date.strftime('%Y-%m-%d'),
                    'tic': ticker,
                    'end_date': t10_date.strftime('%Y-%m-%d'),
                    'start_price': round(t0_close, 4),
                    'end_price': round(t10_close, 4),
                    'price_change': round(price_change, 6),
                    'anchor_a_date': anchor_a_date,
                    'anchor_a_return': anchor_a_value,
                    'anchor_b_date': anchor_b_date,
                    'anchor_b_gap': anchor_b_value,
                    'anchor_c_date': anchor_c_date,
                    'anchor_c_vol_zscore': anchor_c_value,
                })

            processed_count += 1
            if processed_count % 100 == 0:
                print(f"Processed {processed_count} stocks...")

        except Exception as e:
            print(f"Error processing {csv_file.name}: {e}")
            continue

    if not all_changes:
        print("No data found!")
        return

    # Convert to DataFrame
    changes_df = pd.DataFrame(all_changes)
    print(f"\nTotal windows calculated: {len(changes_df)}")

    # Column order
    columns = [
        'start_date', 'tic', 'end_date', 'start_price', 'end_price', 'price_change',
        'anchor_a_date', 'anchor_a_return',
        'anchor_b_date', 'anchor_b_gap',
        'anchor_c_date', 'anchor_c_vol_zscore',
    ]
    changes_df = changes_df[columns]

    # Sort and get top N highest
    top_gainers = changes_df.nlargest(top_n, 'price_change')
    top_gainers_file = output_dir / f'top_{top_n}_gainers_{window}d_{start_date[:4]}.csv'
    top_gainers.to_csv(top_gainers_file, index=False)
    print(f"\nTop {top_n} gainers saved to: {top_gainers_file}")
    print(f"  Max gain: {top_gainers['price_change'].max():.6f}")
    print(f"  Min gain in top: {top_gainers['price_change'].min():.6f}")

    # Sort and get top N lowest
    top_losers = changes_df.nsmallest(top_n, 'price_change')
    top_losers_file = output_dir / f'top_{top_n}_losers_{window}d_{start_date[:4]}.csv'
    top_losers.to_csv(top_losers_file, index=False)
    print(f"\nTop {top_n} losers saved to: {top_losers_file}")
    print(f"  Max loss: {top_losers['price_change'].min():.6f}")
    print(f"  Min loss in top: {top_losers['price_change'].max():.6f}")

    return top_gainers_file, top_losers_file


def main():
    parser = argparse.ArgumentParser(
        description='Find top price changes over N-day windows',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default: 10-day window, top 2000, year 2024
  python find_top_price_changes.py

  # Custom date range and window
  python find_top_price_changes.py --start 2023-01-01 --end 2023-12-31 --window 5

  # Custom data directory
  python find_top_price_changes.py --data-dir D:/GitHub/LocalFinData/data/prices
        """
    )

    parser.add_argument('--data-dir', '-d', type=str,
                       default='D:/GitHub/LocalFinData/data/prices',
                       help='Directory containing price CSV files')
    parser.add_argument('--news-dir', '-n', type=str,
                       default='D:/GitHub/LocalFinData/data/news-yh-stock',
                       help='Directory containing news CSV files (for filtering)')
    parser.add_argument('--start', '-s', type=str, default='2024-01-01',
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', '-e', type=str, default='2024-12-31',
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--window', '-w', type=int, default=10,
                       help='Window size in trading days (default: 10)')
    parser.add_argument('--top-n', '-t', type=int, default=2000,
                       help='Number of top/bottom results (default: 2000)')
    parser.add_argument('--output-dir', '-o', type=str, default=None,
                       help='Output directory (defaults to parent of data-dir)')

    args = parser.parse_args()

    calculate_price_changes(
        data_dir=args.data_dir,
        news_dir=args.news_dir,
        start_date=args.start,
        end_date=args.end,
        window=args.window,
        top_n=args.top_n,
        output_dir=args.output_dir,
    )


if __name__ == '__main__':
    main()
