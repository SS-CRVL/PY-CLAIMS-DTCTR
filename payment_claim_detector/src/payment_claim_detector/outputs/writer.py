"""Output file writing utilities."""

from pathlib import Path

import pandas as pd

from payment_claim_detector.outputs.summary import generate_summary


def _get_true_new_claims_df(detailed_df: pd.DataFrame) -> pd.DataFrame:
    """Return rows that qualify as truly new claims.

    The count-based pipeline defines a truly new claim as a row with
    tracker_match_count == 0. Older outputs may only have is_new_claim or
    classification available, so keep those as fallbacks.
    """
    if "tracker_match_count" in detailed_df.columns:
        return detailed_df[detailed_df["tracker_match_count"] == 0].copy()

    if "is_new_claim" in detailed_df.columns:
        return detailed_df[detailed_df["is_new_claim"]].copy()

    if "classification" in detailed_df.columns:
        return detailed_df[detailed_df["classification"].astype("string") == "NEW_CLAIM"].copy()

    return detailed_df.iloc[0:0].copy()


def write_outputs(detailed_df: pd.DataFrame, excluded_df: pd.DataFrame, output_dir: Path) -> None:
    """Write detailed and summary output files.

    Args:
        detailed_df: DataFrame with classified payment data
        excluded_df: DataFrame with rows filtered out as existing tracker rows
        output_dir: Directory to write output files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_input = detailed_df.copy()

    for column in ["classification", "jurisdiction"]:
        if column not in summary_input.columns:
            summary_input[column] = pd.NA

    # Write detailed results
    detailed_path = output_dir / "detailed_results.xlsx"
    with pd.ExcelWriter(detailed_path, engine="openpyxl") as writer:
        detailed_df.to_excel(writer, index=False, sheet_name="Detailed Results")
        true_new_claims_df = _get_true_new_claims_df(detailed_df)

        # Write separate sheets for each classification
        if "classification" in detailed_df.columns:
            for classification, group in detailed_df.groupby("classification", dropna=False):
                safe_name = str(classification)[:31]  # Excel sheet name limit
                group.to_excel(writer, index=False, sheet_name=safe_name)

            true_new_claims_df.to_excel(writer, index=False, sheet_name="True New Claims")

        if "classification" not in detailed_df.columns:
            true_new_claims_df.to_excel(writer, index=False, sheet_name="True New Claims")

        if "jurisdiction" in detailed_df.columns:
            state_summary = (
                detailed_df.assign(
                    jurisdiction=detailed_df["jurisdiction"].astype("string").str.strip().str.upper(),
                    is_true_new=(detailed_df.index.isin(true_new_claims_df.index)),
                )
                .groupby("jurisdiction", dropna=False)
                .agg(
                    total_rows=("jurisdiction", "size"),
                    true_new_claims=("is_true_new", "sum"),
                )
                .reset_index()
            )
            state_summary.to_excel(writer, index=False, sheet_name="True New By State")

            all_states = (
                detailed_df["jurisdiction"]
                .astype("string")
                .str.strip()
                .str.upper()
                .drop_duplicates()
                .tolist()
            )
            true_new_states = true_new_claims_df["jurisdiction"].astype("string").str.strip().str.upper()

            for state in all_states:
                state_name = str(state).strip()
                state_mask = true_new_states == state
                group = true_new_claims_df.loc[state_mask].copy()
                sheet_name = f"True New {state_name or 'UNKNOWN'}"[:31]
                group.to_excel(writer, index=False, sheet_name=sheet_name)

        # Write sheet for rows whose claim number was not found in tracker history.
        if "is_new_claim" in detailed_df.columns:
            new_claims_df = detailed_df[detailed_df["is_new_claim"]]
            new_claims_df.to_excel(writer, index=False, sheet_name="Claim Number Not Found")

    # Write summary results
    summary_df = generate_summary(summary_input)
    summary_path = output_dir / "summary_results.xlsx"
    with pd.ExcelWriter(summary_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, index=False, sheet_name="Summary")

    # Write excluded results
    excluded_path = output_dir / "excluded_existing_claimants.xlsx"
    with pd.ExcelWriter(excluded_path, engine="openpyxl") as writer:
        excluded_df.to_excel(writer, index=False, sheet_name="Excluded Claimants")

    # Write processed payment log
    log_path = output_dir / "processed_payment_log.csv"
    log_df = detailed_df.reindex(
        columns=["payment_id", "claim_number", "check_date", "source_file", "classification"]
    ).copy()
    log_df["processed_at"] = pd.Timestamp.now()
    log_df.to_csv(log_path, index=False)