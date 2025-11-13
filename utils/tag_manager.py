# utils/tag_manager.py
"""
Tag mapping extraction and management.

Extracts tag group mappings from the metadata row (record_type='tag_group_mapping')
and provides utilities for displaying user-friendly labels.
"""

import pandas as pd
from typing import Dict, Optional


def extract_tag_mappings(df: pd.DataFrame) -> Dict[str, str]:
    """
    Extract tag group mappings from metadata row.

    Filters for record_type='tag_group_mapping' and extracts all non-null
    values from tag columns to build a mapping of column_name -> display_label.

    Args:
        df: DataFrame containing the metadata row

    Returns:
        Dictionary mapping: {tag_column_name: display_label}
        Example: {'project_tag_1': 'Prosjekttype', 'project_tag_2': 'Prosjektfase'}
    """
    # Filter for metadata row
    metadata_df = df[df['record_type'] == 'tag_group_mapping']

    if metadata_df.empty:
        return {}

    # Get first (and only) metadata row
    metadata_row = metadata_df.iloc[0]

    # Build mapping from non-null tag values
    tag_mappings = {}

    # Look for any column that contains 'tag' and has a non-null value
    for col in df.columns:
        if 'tag' in col.lower():
            value = metadata_row[col]
            # Only include non-null, non-empty values
            if pd.notna(value) and value != '':
                tag_mappings[col] = str(value)

    return tag_mappings


def get_tag_display_name(tag_column: str, tag_mappings: Dict[str, str]) -> str:
    """
    Get display name for a tag column, with fallback to column name.

    Args:
        tag_column: Technical column name (e.g., 'project_tag_1')
        tag_mappings: Mapping dict from extract_tag_mappings()

    Returns:
        Display label if found, otherwise the column name
    """
    return tag_mappings.get(tag_column, tag_column)
