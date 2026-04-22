"""Helper utility functions."""

import pandas as pd
from typing import Any, Optional


def safe_str(value: Any) -> Optional[str]:
    """Safely convert value to string, handling None and NaN."""
    if pd.isna(value) or value is None:
        return None
    return str(value).strip()


def safe_float(value: Any) -> Optional[float]:
    """Safely convert value to float, handling None and NaN."""
    if pd.isna(value) or value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def get_file_size_mb(file_path) -> float:
    """Get file size in MB."""
    return file_path.stat().st_size / (1024 * 1024)