"""Duplicate payment detection logic."""

import pandas as pd
from typing import Set


def detect_duplicate_payments(register_df: pd.DataFrame, processed_payment_ids: Set[str]) -> pd.DataFrame:
    """Detect payments that have already been processed.

    Args:
        register_df: DataFrame from weekly register
        processed_payment_ids: Set of payment IDs that have been processed

    Returns:
        DataFrame with 'is_duplicate_payment' column added
    """
    out = register_df.copy()

    if "payment_id" not in out.columns:
        out["is_duplicate_payment"] = False
        return out

    payment_ids = out["payment_id"].astype(str).str.strip()
    out["is_duplicate_payment"] = payment_ids.isin(processed_payment_ids)
    return out