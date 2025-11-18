"""
Temporary utility for loading parquet test data without manual UI selection.
This allows testing features without requiring users to upload files through the UI.
"""

import pandas as pd
import glob
import os


def find_first_parquet_file(data_dir):
    """
    Find the first parquet file in data directory (searches recursively).

    Args:
        data_dir: Path to data directory

    Returns:
        Path to first parquet file found, or None
    """
    # Look in subdirectories first (e.g., data/lundhagem/*.parquet)
    pattern = os.path.join(data_dir, "**", "*.parquet")
    files = glob.glob(pattern, recursive=True)

    if files:
        # Return the most recently modified file
        return max(files, key=os.path.getmtime)

    # Fallback: look in root data directory
    pattern = os.path.join(data_dir, "*.parquet")
    files = glob.glob(pattern)

    if files:
        return max(files, key=os.path.getmtime)

    return None


def auto_load_test_data(data_dir):
    """
    Automatically load test parquet data and split by record type.

    Args:
        data_dir: Path to data directory

    Returns:
        dict with keys: 'transformed_df', 'transformed_planned_df', 'success'
        Returns empty dicts if loading fails
    """
    result = {
        'transformed_df': None,
        'transformed_planned_df': None,
        'success': False,
        'file_loaded': None
    }

    try:
        parquet_file = find_first_parquet_file(data_dir)

        if not parquet_file:
            print(f"[TEST_LOADER] No parquet files found in {data_dir}")
            return result

        print(f"[TEST_LOADER] Found parquet file: {parquet_file}")

        # Load the parquet file
        df = pd.read_parquet(parquet_file)
        print(f"[TEST_LOADER] Loaded {len(df)} rows, {len(df.columns)} columns")
        print(f"[TEST_LOADER] Columns: {list(df.columns)[:10]}...")

        # Split by record_type if available
        if 'record_type' in df.columns:
            time_records = df[df['record_type'] == 'time_record']
            planned_records = df[df['record_type'] == 'planned_record']

            print(f"[TEST_LOADER] Split: {len(time_records)} time_records, {len(planned_records)} planned_records")

            result['transformed_df'] = time_records if len(time_records) > 0 else df
            result['transformed_planned_df'] = planned_records if len(planned_records) > 0 else None
        else:
            # No record_type column - assume all data is time records
            print(f"[TEST_LOADER] No record_type column found - treating as time_records")
            result['transformed_df'] = df
            result['transformed_planned_df'] = None

        result['success'] = True
        result['file_loaded'] = os.path.basename(parquet_file)

        return result

    except Exception as e:
        print(f"[TEST_LOADER] Error loading parquet: {type(e).__name__}: {e}")
        return result
