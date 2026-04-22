"""Data validation utilities."""

import pandas as pd
from typing import List, Optional


def validate_dataframe(df: pd.DataFrame, required_columns: Optional[List[str]] = None) -> List[str]:
    """Validate DataFrame structure and return list of issues.

    Args:
        df: DataFrame to validate
        required_columns: List of columns that should be present

    Returns:
        List of validation error messages
    """
    issues = []

    if df.empty:
        issues.append("DataFrame is empty")
        return issues

    if required_columns:
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            issues.append(f"Missing required columns: {missing_cols}")

    # Check for completely empty rows
    empty_rows = df.isnull().all(axis=1).sum()
    if empty_rows > 0:
        issues.append(f"Found {empty_rows} completely empty rows")

    return issues