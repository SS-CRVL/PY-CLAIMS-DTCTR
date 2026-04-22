"""JSON payload builders for Power Automate integration."""

from pathlib import Path
from typing import Any, Dict
import json
from datetime import datetime, timezone

import pandas as pd


def build_record_payload(enriched_df: pd.DataFrame, source_file: str) -> Dict[str, Any]:
    """Build a record-level JSON payload with run metadata and records list."""
    run = {
        "source_file": source_file,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    classifications = {}
    if "classification" in enriched_df.columns:
        classifications = (
            enriched_df["classification"].fillna("")
            .astype("string")
            .value_counts()
            .to_dict()
        )

    summary = {
        "total_rows": int(len(enriched_df)),
        "classifications": classifications,
    }

    fields = [
        "claim_number",
        "payment_id",
        "jurisdiction",
        "examiner",
        "insured",
        "claimant_last_name",
        "claimant_first_name",
        "amount_issued",
        "payment_description",
        "check_date",
        "classification",
        "classification_reason",
        "tracker_match_count",
        "register_appearance_count",
        "is_new_claim",
        "is_duplicate_payment",
        "supervisor_name",
        "supervisor_email",
        "contact_status",
        "routing_ready",
    ]

    records = []
    for _, row in enriched_df.iterrows():
        rec = {f: (None if pd.isna(row.get(f, None)) else row.get(f, None)) for f in fields}
        records.append(rec)

    return {"run": run, "summary": summary, "records": records}


def build_supervisor_batches(enriched_df: pd.DataFrame, batch_size: int = 100) -> Dict[str, Any]:
    """Group records by supervisor email into batches suitable for Power Automate."""
    batches = []
    if "supervisor_email" not in enriched_df.columns:
        return {"supervisor_batches": batches, "routing_issues": []}

    grouped = enriched_df.groupby("supervisor_email", dropna=False)
    for sup_email, group in grouped:
        if pd.isna(sup_email) or str(sup_email).strip() == "":
            continue
        records = []
        for _, row in group.iterrows():
            records.append(
                {
                    "claim_number": row.get("claim_number"),
                    "examiner": row.get("examiner"),
                    "classification": row.get("classification"),
                    "jurisdiction": row.get("jurisdiction"),
                    "amount_issued": row.get("amount_issued"),
                }
            )

        # chunk
        for i in range(0, len(records), batch_size):
            chunk = records[i : i + batch_size]
            batches.append({"supervisor_email": sup_email, "row_count": len(chunk), "records": chunk})

    # routing issues
    routing_issues = []
    if "contact_status" in enriched_df.columns:
        issues = enriched_df[enriched_df["contact_status"] != "ROUTING_READY_SUPERVISOR"]
        if not issues.empty:
            for examiner, group in issues.groupby("examiner"):
                routing_issues.append(
                    {"examiner": examiner, "reason": group.iloc[0]["contact_status"], "row_count": int(len(group))}
                )

    return {"supervisor_batches": batches, "routing_issues": routing_issues}


def write_json_outputs(record_payload: dict, supervisor_payload: dict, output_dir: Path) -> None:
    """Write JSON payloads to `output_dir` as two files.

    Files:
      - records_payload.json
      - supervisor_payload.json
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    records_path = output_dir / "records_payload.json"
    sup_path = output_dir / "supervisor_payload.json"

    with records_path.open("w", encoding="utf-8") as f:
        json.dump(record_payload, f, default=str, indent=2)

    with sup_path.open("w", encoding="utf-8") as f:
        json.dump(supervisor_payload, f, default=str, indent=2)
