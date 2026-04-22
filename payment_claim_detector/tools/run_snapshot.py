"""Utility script: run the pipeline and print a supervisor-level snapshot.

This script mirrors the CLI usage but prints a concise snapshot grouped by
supervisor -> claim_number -> check_date to the console. It can be run as:

python tools/run_snapshot.py --tracker-file data/raw/tracker.xlsx \
    --register-file data/raw/register.xlsx --output-dir data/outputs \
    --processed-log data/outputs/processed_payment_log.csv --ttd-only

The script avoids changing any existing outputs by default and focuses on
printing a short interactive summary after enrichment.
"""

from pathlib import Path
import argparse
import pandas as pd

from payment_claim_detector.ingestion import parse_tracker_workbook_by_state, parse_weekly_register
from payment_claim_detector.compare import count_tracker_matches, detect_duplicate_payments, classify_rows
from payment_claim_detector.normalize import filter_by_date_range
from payment_claim_detector.contacts.matrix import load_contact_matrix, enrich_with_supervisor_contacts


def build_snapshot_from_enriched(enriched_df: pd.DataFrame, max_lines: int = 200) -> str:
    """Return a textual snapshot grouped by supervisor, claim, and date.

    The output groups by `supervisor_name`, then lists claim_number and check_date.
    """
    out_lines = []
    if "supervisor_name" not in enriched_df.columns:
        enriched_df["supervisor_name"] = pd.NA

    grouped = (
        enriched_df
        .assign(check_date=enriched_df.get("check_date").astype("string"))
        .groupby(["supervisor_name", "claim_number", "check_date"], dropna=False)
        .size()
        .reset_index(name="count")
    )

    supervisors = grouped["supervisor_name"].fillna("<UNMAPPED>").unique().tolist()
    for sup in supervisors:
        sup_rows = grouped[grouped["supervisor_name"] == sup]
        out_lines.append(f"Supervisor: {sup}  (claims={len(sup_rows)})")
        for _, r in sup_rows.iterrows():
            out_lines.append(f"  - {r['claim_number']} | {r['check_date']} | rows={r['count']}")
        out_lines.append("")
        if len(out_lines) > max_lines:
            out_lines.append("...truncated...")
            break

    return "\n".join(out_lines)


def run_snapshot(tracker_file: Path, register_file: Path, output_dir: Path, start_date=None, end_date=None, processed_log: Path = None, state: str = None, ttd_only: bool = False, contact_matrix_file: Path = None):
    tracker_by_state = parse_tracker_workbook_by_state(tracker_file)
    register_df = parse_weekly_register(register_file)

    if start_date and end_date:
        register_df = filter_by_date_range(register_df, start_date, end_date)

    if ttd_only:
        # lightweight TTD mask copied from main
        candidate_columns = [c for c in ["payment_description", "benefit_type"] if c in register_df.columns]
        if candidate_columns:
            mask = pd.Series(False, index=register_df.index)
            for col in candidate_columns:
                mask = mask | register_df[col].astype("string").str.upper().str.contains(r"\bTTD\b|TEMPORARY\s+TOTAL", na=False, regex=True)
            register_df = register_df[mask].copy()

    if state:
        state_upper = state.strip().upper()
        register_df = register_df[register_df["jurisdiction"].astype("string").str.strip().str.upper() == state_upper].copy()
        tracker_by_state = {k: v for k, v in tracker_by_state.items() if k.upper() == state_upper}

    register_df = count_tracker_matches(register_df, tracker_by_state)

    processed_payment_ids = set()
    if processed_log and Path(processed_log).exists():
        try:
            pdf = pd.read_csv(processed_log)
            if "payment_id" in pdf.columns:
                processed_payment_ids = {str(x).strip() for x in pdf["payment_id"].dropna()}
        except Exception:
            processed_payment_ids = set()

    register_df = detect_duplicate_payments(register_df, processed_payment_ids)
    register_df = classify_rows(register_df)

    matrix_df = None
    if contact_matrix_file and Path(contact_matrix_file).exists():
        try:
            matrix_df = load_contact_matrix(contact_matrix_file)
        except Exception as e:
            print("Failed to load contact matrix:", e)

    if matrix_df is not None:
        enriched = enrich_with_supervisor_contacts(register_df, matrix_df)
    else:
        enriched = register_df.copy()
        enriched["supervisor_name"] = pd.NA

    snapshot = build_snapshot_from_enriched(enriched)
    print(snapshot)


def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--tracker-file", required=True)
    p.add_argument("--register-file", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--processed-log", required=False)
    p.add_argument("--start-date", required=False)
    p.add_argument("--end-date", required=False)
    p.add_argument("--state", required=False)
    p.add_argument("--ttd-only", action="store_true")
    p.add_argument("--contact-matrix", required=False)
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_snapshot(
        tracker_file=Path(args.tracker_file),
        register_file=Path(args.register_file),
        output_dir=Path(args.output_dir),
        start_date=args.start_date,
        end_date=args.end_date,
        processed_log=Path(args.processed_log) if args.processed_log else None,
        state=args.state,
        ttd_only=args.ttd_only,
        contact_matrix_file=Path(args.contact_matrix) if args.contact_matrix else None,
    )
