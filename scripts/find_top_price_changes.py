#!/usr/bin/env python3
"""
Find top price changes over 10-day windows in 2024.
Scans all CSV files in data/prices and finds the top 200 highest and lowest
10-day price changes.
"""

import pandas as pd
from pathlib import Path
import argparse
from datetime import datetime


def calculate_price_changes(
    data_dir: str,
    start_date: str = '2024-01-01',
    end_date: str = '2024-12-31',
    window: int = 10,
    top_n: int = 200,
    output_dir: str = None,
):
    """
    Calculate price changes over sliding windows for all stocks.

    Args:
        data_dir: Directory containing CSV files
        start_date: Start date for filtering (YYYY-MM-DD)
        end_date: End date for filtering (YYYY-MM-DD)
        window: Number of trading days for the window
        top_n: Number of top/bottom results to return
        output_dir: Output directory for results (defaults to data_dir)
    """
    data_path = Path(data_dir)
    if output_dir is None:
        output_dir = data_path.parent
    else:
        output_dir = Path(output_dir)

    # Find all CSV files
    csv_files = list(data_path.glob('*.csv'))
    print(f"Found {len(csv_files)} CSV files in {data_path}")

    all_changes = []

    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)

            # Check required columns
            if 'date' not in df.columns or 'close' not in df.columns:
                print(f"Skipping {csv_file.name}: missing date or close column")
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

            # Calculate price changes for each window
            for i in range(len(df) - window):
                t0_date = df.iloc[i]['date']
                t0_close = df.iloc[i]['close']
                t10_date = df.iloc[i + window]['date']
                t10_close = df.iloc[i + window]['close']

                if t0_close == 0:
                    continue

                price_change = (t10_close - t0_close) / t0_close

                all_changes.append({
                    'start_date': t0_date.strftime('%Y-%m-%d'),
                    'tic': ticker,
                    'end_date': t10_date.strftime('%Y-%m-%d'),
                    'price_change': round(price_change, 6),
                })

        except Exception as e:
            print(f"Error processing {csv_file.name}: {e}")
            continue

    if not all_changes:
        print("No data found!")
        return

    # Convert to DataFrame
    changes_df = pd.DataFrame(all_changes)
    print(f"\nTotal windows calculated: {len(changes_df)}")

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
  # Default: 10-day window, top 200, year 2024
  python find_top_price_changes.py

  # Custom date range and window
  python find_top_price_changes.py --start 2023-01-01 --end 2023-12-31 --window 5

  # Custom data directory
  python find_top_price_changes.py --data-dir D:/GitHub/LocalFinData/data/prices
        """
    )

    parser.add_argument('--data-dir', '-d', type=str,
                       default='D:/GitHub/LocalFinData/data/prices',
                       help='Directory containing CSV files')
    parser.add_argument('--start', '-s', type=str, default='2024-01-01',
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', '-e', type=str, default='2024-12-31',
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--window', '-w', type=int, default=10,
                       help='Window size in trading days (default: 10)')
    parser.add_argument('--top-n', '-n', type=int, default=200,
                       help='Number of top/bottom results (default: 200)')
    parser.add_argument('--output-dir', '-o', type=str, default=None,
                       help='Output directory (defaults to parent of data-dir)')

    args = parser.parse_args()

    calculate_price_changes(
        data_dir=args.data_dir,
        start_date=args.start,
        end_date=args.end,
        window=args.window,
        top_n=args.top_n,
        output_dir=args.output_dir,
    )


if __name__ == '__main__':
    main()
