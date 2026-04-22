from pathlib import Path
from typing import Dict, List

import pandas as pd

from payment_claim_detector.normalize.columns import CANONICAL_COLUMNS
from payment_claim_detector.normalize.values import standardize_columns

TTD_SHEET_MAP = {
    "CO": "CO TTD",
    "NV": "NV TTD",
    "AZ": "AZ TTD",
    "ID": "ID TTD",
    "UT": "UT TTD",
}

STATE_CODE_MAP = {
    "CO": "CO",
    "COLORADO": "CO",
    "NV": "NV",
    "NEVADA": "NV",
    "AZ": "AZ",
    "ARIZONA": "AZ",
    "ID": "ID",
    "IDAHO": "ID",
    "UT": "UT",
    "UTAH": "UT",
}


def _normalize_jurisdiction(value: object) -> str | None:
    if pd.isna(value):
        return None

    normalized = str(value).strip().upper()
    if not normalized:
        return None

    return STATE_CODE_MAP.get(normalized, normalized)


def parse_tracker_workbook_by_state(workbook_path: Path) -> Dict[str, pd.DataFrame]:
    """Parse TTD tracker tabs and bucket rows by jurisdiction."""
    xl = pd.ExcelFile(workbook_path, engine="openpyxl")
    available_sheets = [
        (default_state, sheet_name)
        for default_state, sheet_name in TTD_SHEET_MAP.items()
        if sheet_name in xl.sheet_names
    ]

    if not available_sheets:
        expected_sheets = ", ".join(TTD_SHEET_MAP.values())
        raise ValueError(f"No expected TTD tracker tabs found. Expected one of: {expected_sheets}")

    tracker_frames: Dict[str, List[pd.DataFrame]] = {}

    for default_state, sheet_name in available_sheets:
        df = pd.read_excel(workbook_path, sheet_name=sheet_name, engine="openpyxl")
        df = standardize_columns(df, CANONICAL_COLUMNS)

        if "jurisdiction" in df.columns:
            df["jurisdiction"] = df["jurisdiction"].apply(_normalize_jurisdiction)
            df["jurisdiction"] = df["jurisdiction"].fillna(default_state)
        else:
            df["jurisdiction"] = default_state

        df["source_sheet"] = sheet_name
        df["source_file"] = workbook_path.name

        for state, group in df.groupby("jurisdiction", dropna=False):
            normalized_state = _normalize_jurisdiction(state)
            if not normalized_state:
                continue

            tracker_frames.setdefault(normalized_state, []).append(group.copy())

    return {
        state: pd.concat(frames, ignore_index=True)
        for state, frames in tracker_frames.items()
    }
