"""Sheet selection logic for state-specific payment sheets."""

from pathlib import Path
from typing import Dict

import pandas as pd

from payment_claim_detector.models.enums import StateCode
from payment_claim_detector.settings import load_state_sheet_map


def select_state_payment_sheets(workbook_path: Path) -> Dict[str, str]:
    """Select the appropriate payment sheet for each state.

    Args:
        workbook_path: Path to the workbook

    Returns:
        Dictionary mapping state codes to sheet names
    """
    xl = pd.ExcelFile(workbook_path, engine="openpyxl")
    available_sheets = set(xl.sheet_names)
    state_map = load_state_sheet_map()

    result: Dict[str, str] = {}

    for state in StateCode:
        state_str = state.value
        preferred_sheets = state_map.get(state_str, [f"{state_str} | Payments"])

        for sheet_pattern in preferred_sheets:
            # Try exact match first
            if sheet_pattern in available_sheets:
                result[state_str] = sheet_pattern
                break

            # Try case-insensitive match
            for sheet in available_sheets:
                if sheet.upper() == sheet_pattern.upper():
                    result[state_str] = sheet
                    break

            if state_str in result:
                break

        # Fallback: any sheet containing the state code
        if state_str not in result:
            for sheet in available_sheets:
                if state_str.upper() in sheet.upper():
                    result[state_str] = sheet
                    break

    return result