"""Value standardization and cleaning utilities."""

import re
from typing import Dict, List

import pandas as pd


def _normalize_header_name(value: object) -> str:
    """Normalize a header for loose alias matching."""
    text = str(value).strip().lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def standardize_columns(df: pd.DataFrame, aliases: Dict[str, List[str]]) -> pd.DataFrame:
    """Standardize column names using aliases.

    Args:
        df: Input DataFrame
        aliases: Dictionary mapping canonical names to possible aliases

    Returns:
        DataFrame with standardized column names
    """
    rename_map = {}
    normalized_existing = [
        (existing, _normalize_header_name(existing))
        for existing in df.columns
    ]
    used_existing = set()

    for canonical, possible_names in aliases.items():
        normalized_candidates = {
            _normalize_header_name(canonical),
            *(_normalize_header_name(name) for name in possible_names),
        }

        for existing, normalized_name in normalized_existing:
            if existing in used_existing:
                continue

            if normalized_name in normalized_candidates:
                rename_map[existing] = canonical
                used_existing.add(existing)
                break

    out = df.rename(columns=rename_map).copy()

    # Clean string columns
    string_columns = [
        "claim_number", "claimant_first_name", "claimant_last_name",
        "full_name", "insured", "payment_description", "examiner",
        "supervisor", "comments", "notes", "payment_id", "claim_type",
        "jurisdiction"
    ]

    for col in string_columns:
        if col in out.columns:
            out[col] = (
                out[col]
                .astype("string")
                .str.strip()
                .replace({"<NA>": pd.NA, "nan": pd.NA, "None": pd.NA, "": pd.NA})
            )

    # Convert date columns
    date_columns = [
        "check_date", "last_check_sent", "next_payment_to_be_sent",
        "service_start", "service_end", "date_of_loss"
    ]

    for col in date_columns:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors="coerce")

    # Convert numeric columns
    if "amount_issued" in out.columns:
        out["amount_issued"] = pd.to_numeric(out["amount_issued"], errors="coerce")

    return out