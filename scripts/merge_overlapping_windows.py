#!/usr/bin/env python3
"""
Merge overlapping price change windows for the same stock.
Reads the output from find_top_price_changes.py and merges overlapping windows,
then recalculates all metrics using the merged period.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import argparse


def merge_overlapping_windows(windows: list) -> list:
    """
    Merge overlapping date windows.

    Args:
        windows: List of (start_date, end_date) tuples, sorted by start_date

    Returns:
        List of merged (start_date, end_date) tuples
    """
    if not windows:
        return []

    # Sort by start date
    windows = sorted(windows, key=lambda x: x[0])

    merged = [windows[0]]

    for current_start, current_end in windows[1:]:
        last_start, last_end = merged[-1]

        # Check if current window overlaps with the last merged window
        # Overlap means current_start <= last_end (they share at least one day)
        if current_start <= last_end:
            # Merge: extend the end date if needed
            merged[-1] = (last_start, max(last_end, current_end))
        else:
            # No overlap, add as new window
            merged.append((current_start, current_end))

    return merged


def recalculate_metrics(df: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp) -> dict:
    """
    Recalculate all metrics for a given date range.

    Args:
        df: Stock price DataFrame with date, open, close, volume columns
        start_date: Start date of the window
        end_date: End date of the window

    Returns:
        Dictionary with recalculated metrics
    """
    # Filter to window
    window_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)].copy()

    if len(window_df) < 2:
        return None

    # Basic metrics
    t0_row = window_df.iloc[0]
    tn_row = window_df.iloc[-1]

    start_price = t0_row['close']
    end_price = tn_row['close']

    if start_price == 0:
        return None

    price_change = (end_price - start_price) / start_price
    duration = len(window_df)  # Number of trading days

    # Calculate daily return and gap for anchor calculations
    window_df['daily_return'] = window_df['close'].pct_change()
    window_df['gap'] = window_df['open'] - window_df['close'].shift(1)

    # Volume z-score (based on window period)
    vol_mean = window_df['volume'].mean()
    vol_std = window_df['volume'].std()
    if vol_std > 0:
        window_df['volume_zscore'] = (window_df['volume'] - vol_mean) / vol_std
    else:
        window_df['volume_zscore'] = 0

    # Skip first row for return and gap calculations
    calc_df = window_df.iloc[1:].copy()

    # Anchor A+: max positive return
    anchor_a_pos_date = None
    anchor_a_pos_return = None
    anchor_a_neg_date = None
    anchor_a_neg_return = None

    if len(calc_df) > 0 and calc_df['daily_return'].notna().any():
        pos_idx = calc_df['daily_return'].idxmax()
        anchor_a_pos_date = window_df.loc[pos_idx, 'date'].strftime('%Y-%m-%d')
        anchor_a_pos_return = round(window_df.loc[pos_idx, 'daily_return'], 4)

        neg_idx = calc_df['daily_return'].idxmin()
        anchor_a_neg_date = window_df.loc[neg_idx, 'date'].strftime('%Y-%m-%d')
        anchor_a_neg_return = round(window_df.loc[neg_idx, 'daily_return'], 4)

    # Anchor B+: max gap up / gap down
    anchor_b_pos_date = None
    anchor_b_pos_gap = None
    anchor_b_neg_date = None
    anchor_b_neg_gap = None

    if len(calc_df) > 0 and calc_df['gap'].notna().any():
        pos_idx = calc_df['gap'].idxmax()
        anchor_b_pos_date = window_df.loc[pos_idx, 'date'].strftime('%Y-%m-%d')
        anchor_b_pos_gap = round(window_df.loc[pos_idx, 'gap'], 4)

        neg_idx = calc_df['gap'].idxmin()
        anchor_b_neg_date = window_df.loc[neg_idx, 'date'].strftime('%Y-%m-%d')
        anchor_b_neg_gap = round(window_df.loc[neg_idx, 'gap'], 4)

    # Anchor C: max volume z-score
    anchor_c_date = None
    anchor_c_vol_zscore = None

    if window_df['volume_zscore'].notna().any():
        vol_idx = window_df['volume_zscore'].idxmax()
        anchor_c_date = window_df.loc[vol_idx, 'date'].strftime('%Y-%m-%d')
        anchor_c_vol_zscore = round(window_df.loc[vol_idx, 'volume_zscore'], 4)

    return {
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'duration': duration,
        'start_price': round(start_price, 4),
        'end_price': round(end_price, 4),
        'price_change': round(price_change, 4),
        'anchor_a_pos_date': anchor_a_pos_date,
        'anchor_a_pos_return': anchor_a_pos_return,
        'anchor_a_neg_date': anchor_a_neg_date,
        'anchor_a_neg_return': anchor_a_neg_return,
        'anchor_b_pos_date': anchor_b_pos_date,
        'anchor_b_pos_gap': anchor_b_pos_gap,
        'anchor_b_neg_date': anchor_b_neg_date,
        'anchor_b_neg_gap': anchor_b_neg_gap,
        'anchor_c_date': anchor_c_date,
        'anchor_c_vol_zscore': anchor_c_vol_zscore,
    }


def merge_windows_in_file(
    input_file: str,
    prices_dir: str,
    output_file: str = None,
):
    """
    Process a price changes CSV file and merge overlapping windows.

    Args:
        input_file: Path to input CSV (e.g., top_2000_gainers_10d_2024.csv)
        prices_dir: Directory containing original price CSV files
        output_file: Output file path (defaults to input_file with _merged suffix)
    """
    input_path = Path(input_file)
    prices_path = Path(prices_dir)

    if output_file is None:
        output_file = input_path.parent / f"{input_path.stem}_merged.csv"
    else:
        output_file = Path(output_file)

    print(f"Reading input file: {input_path}")
    df = pd.read_csv(input_path)
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['end_date'] = pd.to_datetime(df['end_date'])

    print(f"Total rows: {len(df)}")
    print(f"Unique tickers: {df['tic'].nunique()}")

    # Group by ticker and find overlapping windows
    results = []

    for tic, group in df.groupby('tic'):
        # Get all windows for this ticker
        windows = list(zip(group['start_date'], group['end_date']))

        # Merge overlapping windows
        merged_windows = merge_overlapping_windows(windows)

        # Load price data for this ticker
        price_file = prices_path / f"{tic}.csv"
        if not price_file.exists():
            # Try lowercase
            price_file = prices_path / f"{tic.lower()}.csv"

        if not price_file.exists():
            print(f"Warning: Price file not found for {tic}, skipping")
            continue

        try:
            price_df = pd.read_csv(price_file)
            price_df['date'] = pd.to_datetime(price_df['date'])
            price_df = price_df.sort_values('date').reset_index(drop=True)
        except Exception as e:
            print(f"Error loading price data for {tic}: {e}")
            continue

        # Recalculate metrics for each merged window
        for start_date, end_date in merged_windows:
            metrics = recalculate_metrics(price_df, start_date, end_date)
            if metrics:
                metrics['tic'] = tic
                results.append(metrics)

    if not results:
        print("No results after merging!")
        return

    # Create output DataFrame
    result_df = pd.DataFrame(results)

    # Reorder columns
    columns = [
        'start_date', 'tic', 'end_date', 'duration', 'start_price', 'end_price', 'price_change',
        'anchor_a_pos_date', 'anchor_a_pos_return',
        'anchor_a_neg_date', 'anchor_a_neg_return',
        'anchor_b_pos_date', 'anchor_b_pos_gap',
        'anchor_b_neg_date', 'anchor_b_neg_gap',
        'anchor_c_date', 'anchor_c_vol_zscore',
    ]
    result_df = result_df[columns]

    # Sort by price_change (descending for gainers, ascending for losers)
    if 'gainer' in str(input_path).lower():
        result_df = result_df.sort_values('price_change', ascending=False)
    else:
        result_df = result_df.sort_values('price_change', ascending=True)

    result_df.to_csv(output_file, index=False)

    print(f"\nMerge complete!")
    print(f"Original windows: {len(df)}")
    print(f"Merged windows: {len(result_df)}")
    print(f"Output saved to: {output_file}")

    # Statistics
    print(f"\nStatistics:")
    print(f"  Duration range: {result_df['duration'].min()} - {result_df['duration'].max()} days")
    print(f"  Average duration: {result_df['duration'].mean():.1f} days")
    print(f"  Price change range: {result_df['price_change'].min():.4f} - {result_df['price_change'].max():.4f}")

    return output_file


def main():
    parser = argparse.ArgumentParser(
        description='Merge overlapping price change windows',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Merge gainers file
  python merge_overlapping_windows.py --input D:/GitHub/LocalFinData/data/top_2000_gainers_10d_2024.csv

  # Merge losers file
  python merge_overlapping_windows.py --input D:/GitHub/LocalFinData/data/top_2000_losers_10d_2024.csv

  # Custom output file
  python merge_overlapping_windows.py --input input.csv --output merged.csv
        """
    )

    parser.add_argument('--input', '-i', type=str, required=True,
                       help='Input CSV file (output from find_top_price_changes.py)')
    parser.add_argument('--prices-dir', '-p', type=str,
                       default='D:/GitHub/LocalFinData/data/prices',
                       help='Directory containing price CSV files')
    parser.add_argument('--output', '-o', type=str, default=None,
                       help='Output file path (defaults to input_merged.csv)')

    args = parser.parse_args()

    merge_windows_in_file(
        input_file=args.input,
        prices_dir=args.prices_dir,
        output_file=args.output,
    )


if __name__ == '__main__':
    main()
