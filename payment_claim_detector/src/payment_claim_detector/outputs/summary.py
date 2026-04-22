"""Summary generation utilities."""

import pandas as pd


def generate_summary(detailed_df: pd.DataFrame) -> pd.DataFrame:
    """Generate summary statistics from detailed results.

    Args:
        detailed_df: DataFrame with classified payment data

    Returns:
        DataFrame with summary statistics
    """
    # Count by classification and jurisdiction
    summary = (
        detailed_df.groupby(["classification", "jurisdiction"], dropna=False)
        .size()
        .reset_index(name="row_count")
    )

    # Add totals
    total_row = pd.DataFrame({
        "classification": ["TOTAL"],
        "jurisdiction": [pd.NA],
        "row_count": [len(detailed_df)]
    })

    summary = pd.concat([summary, total_row], ignore_index=True)

    # Add amount totals where applicable
    if "amount_issued" in detailed_df.columns:
        amount_summary = (
            detailed_df.groupby(["classification", "jurisdiction"], dropna=False)["amount_issued"]
            .sum()
            .reset_index(name="total_amount")
        )
        summary = summary.merge(amount_summary, on=["classification", "jurisdiction"], how="left")

    return summary