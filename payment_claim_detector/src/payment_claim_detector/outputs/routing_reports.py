"""Utilities for building routing issue reports."""

import pandas as pd


def build_routing_issues(enriched_df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame summarizing routing issues (unmatched or incomplete contacts)."""
    if "contact_status" not in enriched_df.columns:
        return pd.DataFrame(columns=["examiner", "contact_status", "row_count"])

    issues = enriched_df[enriched_df["contact_status"] != "ROUTING_READY_SUPERVISOR"]
    if issues.empty:
        return pd.DataFrame(columns=["examiner", "contact_status", "row_count"])

    report = (
        issues.groupby(["examiner", "contact_status"])
        .size()
        .reset_index(name="row_count")
    )
    return report
