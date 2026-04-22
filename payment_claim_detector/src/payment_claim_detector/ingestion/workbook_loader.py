"""Workbook loading utilities."""

from pathlib import Path
from typing import Optional

import pandas as pd


def load_excel_sheet(
    file_path: Path,
    sheet_name: str,
    header: Optional[int] = 0,
    skiprows: Optional[int] = None,
) -> pd.DataFrame:
    """Load a specific sheet from an Excel workbook.

    Args:
        file_path: Path to the Excel file
        sheet_name: Name of the sheet to load
        header: Row number to use as column headers
        skiprows: Number of rows to skip at the beginning

    Returns:
        DataFrame containing the sheet data
    """
    try:
        return pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            engine="openpyxl",
            header=header,
            skiprows=skiprows,
        )
    except Exception as e:
        raise ValueError(f"Failed to load sheet '{sheet_name}' from {file_path}: {e}")


def get_sheet_names(file_path: Path) -> list[str]:
    """Get all sheet names from an Excel workbook.

    Args:
        file_path: Path to the Excel file

    Returns:
        List of sheet names
    """
    xl = pd.ExcelFile(file_path, engine="openpyxl")
    return xl.sheet_names