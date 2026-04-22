"""Parser for weekly payment register files."""

from pathlib import Path

import pandas as pd

from payment_claim_detector.normalize.columns import CANONICAL_COLUMNS
from payment_claim_detector.normalize.values import standardize_columns
from payment_claim_detector.settings import get_settings


def parse_weekly_register(
    workbook_path: Path,
    sheet_name: str = None
) -> pd.DataFrame:
    """Parse a weekly payment register workbook.

    Args:
        workbook_path: Path to the register Excel file
        sheet_name: Name of the sheet to parse (uses default if None)

    Returns:
        DataFrame with standardized payment event data
    """
    settings = get_settings()
    if sheet_name is None:
        sheet_name = settings.processing.default_sheet_name

    df = pd.read_excel(workbook_path, sheet_name=sheet_name, engine="openpyxl")
    df = standardize_columns(df, CANONICAL_COLUMNS)
    df["source_sheet"] = sheet_name
    df["source_file"] = workbook_path.name
    return df