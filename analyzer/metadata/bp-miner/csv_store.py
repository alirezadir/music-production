"""CSV storage utilities for managing data files."""
import os
import pandas as pd
from typing import List, Optional
from datetime import datetime


def load_or_create_csv(path: str, columns: List[str]) -> pd.DataFrame:
    """
    Load existing CSV or create new one with specified columns.
    
    Args:
        path: Path to CSV file.
        columns: List of column names.
    
    Returns:
        DataFrame with the CSV data or empty DataFrame with columns.
    """
    # Resolve relative paths
    if not os.path.isabs(path):
        project_root = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(project_root, path)
    
    if os.path.exists(path):
        df = pd.read_csv(path)
        # Ensure all required columns exist
        for col in columns:
            if col not in df.columns:
                df[col] = None
        # Reorder columns to match schema
        df = df[columns]
        return df
    else:
        return pd.DataFrame(columns=columns)


def append_and_save(
    path: str,
    new_rows_df: pd.DataFrame,
    key_columns: List[str],
    deduplicate: bool = True
) -> None:
    """
    Append new rows to CSV, avoiding duplicates based on key columns.
    
    Args:
        path: Path to CSV file.
        new_rows_df: DataFrame with new rows to append.
        key_columns: Columns to use for deduplication.
        deduplicate: Whether to deduplicate before saving.
    """
    if new_rows_df.empty:
        return
    
    # Resolve relative paths
    if not os.path.isabs(path):
        project_root = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(project_root, path)
    
    # Load existing data
    existing_df = load_or_create_csv(path, list(new_rows_df.columns))
    
    if existing_df.empty:
        # No existing data, just save new rows
        new_rows_df.to_csv(path, index=False)
        return
    
    if deduplicate:
        # Create composite key for deduplication
        existing_df["_composite_key"] = existing_df[key_columns].apply(
            lambda row: "|".join(row.astype(str)), axis=1
        )
        new_rows_df["_composite_key"] = new_rows_df[key_columns].apply(
            lambda row: "|".join(row.astype(str)), axis=1
        )
        
        # Filter out duplicates
        new_rows_df = new_rows_df[
            ~new_rows_df["_composite_key"].isin(existing_df["_composite_key"])
        ]
        
        # Drop temporary key column
        existing_df = existing_df.drop(columns=["_composite_key"])
        if not new_rows_df.empty:
            new_rows_df = new_rows_df.drop(columns=["_composite_key"])
    
    if not new_rows_df.empty:
        # Append and save
        combined_df = pd.concat([existing_df, new_rows_df], ignore_index=True)
        combined_df.to_csv(path, index=False)
    else:
        # No new rows, just ensure existing is saved
        existing_df.to_csv(path, index=False)

