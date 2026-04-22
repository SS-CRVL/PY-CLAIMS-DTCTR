"""Date handling and filtering utilities."""

import pandas as pd
from typing import Optional


def filter_by_date_range(
    df: pd.DataFrame,
    start_date: str,
    end_date: str,
    date_column: str = "check_date",
) -> pd.DataFrame:
    """Filter DataFrame by date range.

    Args:
        df: Input DataFrame
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        date_column: Name of the date column to filter on

    Returns:
        Filtered DataFrame
    """
    out = df.copy()
    if date_column not in out.columns:
        return out

    out[date_column] = pd.to_datetime(out[date_column], errors="coerce")

    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)

    mask = (out[date_column] >= start) & (out[date_column] <= end)
    return out[mask].copy()


def normalize_date_columns(df: pd.DataFrame, date_columns: list[str]) -> pd.DataFrame:
    """Normalize date columns to datetime format.

    Args:
        df: Input DataFrame
        date_columns: List of column names to convert to dates

    Returns:
        DataFrame with normalized date columns
    """
    out = df.copy()
    for col in date_columns:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors="coerce")
    return out