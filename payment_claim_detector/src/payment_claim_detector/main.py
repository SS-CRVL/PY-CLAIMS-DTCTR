"""Main entry point for the Payment Claim Detector application."""

from pathlib import Path
from typing import Optional

import pandas as pd

from payment_claim_detector.ingestion import parse_tracker_workbook_by_state, parse_weekly_register
from payment_claim_detector.compare import (
    count_tracker_matches,
    detect_duplicate_payments,
    classify_rows,
)
from payment_claim_detector.outputs import write_outputs
from payment_claim_detector.normalize import filter_by_date_range


def _build_ttd_mask(register_df: pd.DataFrame) -> pd.Series:
    """Return a mask for rows representing TTD payments.

    Supports both abbreviated labels like "TTD" and spelled-out descriptions
    like "Temporary Total Disability" across any known payment-type columns.
    """
    candidate_columns = [
        column for column in ["payment_description", "benefit_type"]
        if column in register_df.columns
    ]

    if not candidate_columns:
        return pd.Series(True, index=register_df.index, dtype="bool")

    ttd_pattern = r"\bTTD\b|TEMPORARY\s+TOTAL"
    combined_mask = pd.Series(False, index=register_df.index, dtype="bool")

    for column in candidate_columns:
        values = register_df[column].astype("string").str.upper()
        combined_mask = combined_mask | values.str.contains(ttd_pattern, na=False, regex=True)

    return combined_mask


def _print_count_summary(
    register_df: pd.DataFrame,
    rows_raw: int,
    rows_after_date: int,
    rows_after_ttd: int,
    state_filter: Optional[str],
    ttd_only: bool,
) -> None:
    """Print the console count summary for the current analysis run."""
    total = len(register_df)
    tracker_match_count = register_df.get("tracker_match_count", pd.Series(dtype="int64"))
    duplicate_flags = register_df.get("is_duplicate_payment", pd.Series(dtype="bool"))

    new_claims = int((tracker_match_count == 0).sum())
    existing = int((tracker_match_count > 0).sum())
    duplicates = int(duplicate_flags.fillna(False).sum())

    width = 38
    print(f"\n{'─' * width}")
    print("  COUNT SUMMARY")
    print(f"{'─' * width}")
    print(f"  Register rows (raw)         : {rows_raw}")
    if rows_after_date != rows_raw:
        print(f"  After date filter           : {rows_after_date}")
    if ttd_only:
        print(f"  After TTD filter            : {rows_after_ttd}  (-{rows_after_date - rows_after_ttd} non-TTD)")
    if state_filter:
        print(f"  After state filter ({state_filter.upper():<2})     : {total}")
    print(f"{'─' * width}")
    print(f"  Total rows analysed         : {total}")
    print(f"  True New Claims (count = 0) : {new_claims}")
    print(f"  Existing claims             : {existing}")
    if duplicates:
        print(f"  Duplicate payments          : {duplicates}")
    print(f"{'─' * width}")

    if total > 0 and "jurisdiction" in register_df.columns:
        print("  By state:")
        grouped_states = register_df.groupby(
            register_df["jurisdiction"].astype("string").str.strip().str.upper(),
            dropna=False,
        )
        for state, group in grouped_states:
            state_new = int((group["tracker_match_count"] == 0).sum())
            print(
                f"    {str(state):<4}  total={len(group):>4}  new={state_new:>4}  existing={len(group) - state_new:>4}"
            )

    if total > 0 and "classification" in register_df.columns:
        print("  By classification:")
        for classification, group in register_df.groupby("classification", dropna=False):
            print(f"    {str(classification):<35} : {len(group)}")

    print(f"{'─' * width}\n")


def run_analysis(
    tracker_file: Path,
    register_file: Path,
    output_dir: Path,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    processed_payment_log: Optional[Path] = None,
    state_filter: Optional[str] = None,
    ttd_only: bool = False,
    export_json: bool = False,
    contact_matrix_file: Optional[Path] = None,
    json_output_dir: Optional[Path] = None,
) -> None:
    """Run the complete payment claim detection analysis.

    Args:
        tracker_file: Path to the historical tracker workbook
        register_file: Path to the weekly payment register
        output_dir: Directory to write output files
        start_date: Optional start date for filtering (YYYY-MM-DD)
        end_date: Optional end date for filtering (YYYY-MM-DD)
        processed_payment_log: Optional path to CSV with previously processed payment IDs
        state_filter: Optional state code to restrict analysis (e.g. "ID")
        ttd_only: When True, keep only rows where payment_description contains "TTD"
    """
    # Parse tracker
    tracker_by_state = parse_tracker_workbook_by_state(tracker_file)

    # Parse register
    register_df = parse_weekly_register(register_file)
    rows_raw = len(register_df)

    # Optional date filtering
    if start_date and end_date:
        register_df = filter_by_date_range(register_df, start_date, end_date)
    rows_after_date = len(register_df)

    # Optional TTD-only filter on payment_description
    rows_after_ttd = rows_after_date
    if ttd_only:
        mask = _build_ttd_mask(register_df)
        register_df = register_df[mask].copy()
        rows_after_ttd = len(register_df)

    # Optional state scoping (for targeted testing)
    if state_filter:
        state_upper = state_filter.strip().upper()
        register_df = register_df[
            register_df["jurisdiction"].str.strip().str.upper() == state_upper
        ].copy()
        tracker_by_state = {
            k: v for k, v in tracker_by_state.items() if k.upper() == state_upper
        }

    # Count tracker appearances — sets tracker_match_count, register_appearance_count, is_new_claim
    register_df = count_tracker_matches(register_df, tracker_by_state)

    # Excluded DF is empty under the count approach (no pre-filter step)
    excluded_df = register_df.iloc[0:0].copy()

    # If nothing to analyse, short-circuit
    if register_df.empty:
        _print_count_summary(
            register_df=register_df,
            rows_raw=rows_raw,
            rows_after_date=rows_after_date,
            rows_after_ttd=rows_after_ttd,
            state_filter=state_filter,
            ttd_only=ttd_only,
        )
        write_outputs(register_df, excluded_df, output_dir)
        return

    # Load processed payment IDs
    processed_payment_ids: set = set()
    if processed_payment_log and processed_payment_log.exists():
        processed_df = pd.read_csv(processed_payment_log)
        if "payment_id" in processed_df.columns:
            processed_payment_ids = {
                str(pid).strip()
                for pid in processed_df["payment_id"].dropna()
            }

    # Detect duplicate payments
    register_df = detect_duplicate_payments(register_df, processed_payment_ids)

    # Classify rows (tracker_match_count == 0 → NEW_CLAIM)
    register_df = classify_rows(register_df)

    _print_count_summary(
        register_df=register_df,
        rows_raw=rows_raw,
        rows_after_date=rows_after_date,
        rows_after_ttd=rows_after_ttd,
        state_filter=state_filter,
        ttd_only=ttd_only,
    )

    # Write outputs
    write_outputs(register_df, excluded_df, output_dir)

    # Optional JSON export/integration (non-blocking)
    if export_json:
        try:
            from payment_claim_detector.contacts.matrix import (
                load_contact_matrix,
                enrich_with_supervisor_contacts,
            )
            from payment_claim_detector.outputs.json_payloads import (
                build_record_payload,
                build_supervisor_batches,
                write_json_outputs,
            )
            from payment_claim_detector.outputs.routing_reports import build_routing_issues
        except Exception as e:
            print("JSON export helpers unavailable:", e)
        else:
            matrix_df = None
            if contact_matrix_file and Path(contact_matrix_file).exists():
                try:
                    matrix_df = load_contact_matrix(contact_matrix_file)
                except Exception as e:
                    print("Failed to load contact matrix:", e)

            if matrix_df is not None:
                enriched_df = enrich_with_supervisor_contacts(register_df, matrix_df)
            else:
                enriched_df = register_df.copy()
                enriched_df["supervisor_name"] = pd.NA
                enriched_df["supervisor_email"] = pd.NA
                enriched_df["contact_status"] = "MISSING_ADJUSTER_MAPPING"
                enriched_df["routing_ready"] = False

            record_payload = build_record_payload(enriched_df, source_file=register_file.name)
            supervisor_payload = build_supervisor_batches(enriched_df)
            out_dir = Path(json_output_dir) if json_output_dir else output_dir
            try:
                write_json_outputs(record_payload, supervisor_payload, out_dir)
                routing_df = build_routing_issues(enriched_df)
                routing_df.to_csv(out_dir / "routing_issues.csv", index=False)
            except Exception as e:
                print("Failed to write JSON outputs:", e)

    # Update processed payment log
    if processed_payment_log:
        _update_processed_log(register_df, processed_payment_log)


def _update_processed_log(register_df: pd.DataFrame, log_path: Path) -> None:
    """Update the processed payment log with new payment IDs."""
    new_payments = register_df[["payment_id", "claim_number", "check_date", "source_file"]].copy()
    new_payments["processed_at"] = pd.Timestamp.now()

    if log_path.exists():
        existing = pd.read_csv(log_path)
        combined = pd.concat([existing, new_payments], ignore_index=True)
        combined.drop_duplicates(subset=["payment_id"], keep="first", inplace=True)
    else:
        combined = new_payments

    combined.to_csv(log_path, index=False)