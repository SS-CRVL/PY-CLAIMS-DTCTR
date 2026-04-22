"""Contact matrix loading and enrichment helpers.

This module provides a small, defensive contact-matrix loader, a name
normalization helper, and an enrichment function that joins supervisor
contact info onto the classified results DataFrame.
"""

from pathlib import Path
from typing import Dict, Optional

import pandas as pd


NAME_ALIASES: Dict[str, str] = {}


def load_contact_matrix(path: Path) -> pd.DataFrame:
    """Load a contact matrix Excel file and normalize expected columns.

    The function attempts to map common column names to the canonical
    `adjuster_name`, `supervisor_name`, and `supervisor_email` fields.
    It also computes an `adjuster_norm` column used for joining.
    """
    df = pd.read_excel(path, engine="openpyxl")

    # Map likely column names to canonical names (tolerant to small typos)
    col_map = {}
    for col in df.columns:
        lc = str(col).strip().lower()
        # detect adjuster-like columns
        if "adjust" in lc:
            col_map[col] = "adjuster_name"
        # detect supervisor-like columns (cover small misspellings like 'supevisor')
        if ("super" in lc or "supe" in lc) and "email" not in lc:
            col_map[col] = "supervisor_name"
        if ("super" in lc or "supe" in lc) and "email" in lc:
            col_map[col] = "supervisor_email"
        # fallback: if column mentions email and supervisor-like token anywhere
        if "email" in lc and ("super" in lc or "supe" in lc):
            col_map[col] = "supervisor_email"

    df = df.rename(columns=col_map)

    # Ensure required columns exist
    for col in ["adjuster_name", "supervisor_name", "supervisor_email"]:
        if col not in df.columns:
            df[col] = pd.NA

    # Compute a normalized adjuster key for robust matching
    df["adjuster_norm"] = df["adjuster_name"].astype("string").apply(normalize_person_name)

    # Deduplicate on normalized adjuster name (keep first)
    df = df.drop_duplicates(subset=["adjuster_norm"], keep="first").reset_index(drop=True)

    return df


def normalize_person_name(name: Optional[str]) -> str:
    """Return a compact normalized form of a person's name.

    Normalization rules (conservative):
    - Empty / missing values -> empty string
    - Collapse whitespace, trim, lowercase
    - If input contains a comma assume "Last, First" and normalize spacing
    - Otherwise, for two-token names assume "First Last" and return "last, first"
    """
    if pd.isna(name) or name is None:
        return ""
    s = str(name).strip()
    if not s:
        return ""
    # collapse repeated spaces
    s = " ".join(s.split())
    # preserve comma format if present
    if "," in s:
        parts = [p.strip() for p in s.split(",") if p.strip()]
        if len(parts) >= 2:
            last = parts[0].lower()
            first = parts[1].lower()
            return f"{last}, {first}"
        return parts[0].lower()

    parts = s.split()
    if len(parts) == 1:
        return parts[0].lower()
    # assume first last -> last, first
    first = parts[0].lower()
    last = " ".join(parts[1:]).lower()
    return f"{last}, {first}"


def enrich_with_supervisor_contacts(
    results_df: pd.DataFrame,
    matrix_df: pd.DataFrame,
    alias_map: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """Join supervisor contact info onto `results_df` using `matrix_df`.

    Adds these columns to the returned DataFrame:
      - `supervisor_name`
      - `supervisor_email`
      - `contact_status` (one of ROUTING_READY_SUPERVISOR, MISSING_ADJUSTER_MAPPING,
         MISSING_SUPERVISOR, MISSING_SUPERVISOR_EMAIL)
      - `routing_ready` (bool)
    """
    df = results_df.copy()

    # Build normalized keys
    df["examiner_norm"] = df.get("examiner", pd.Series(dtype="string")).astype("string").apply(normalize_person_name)
    m = matrix_df.copy()
    if "adjuster_norm" not in m.columns:
        m["adjuster_norm"] = m["adjuster_name"].astype("string").apply(normalize_person_name)

    lookup = m.set_index("adjuster_norm")[ ["supervisor_name", "supervisor_email"] ].to_dict(orient="index")

    supervisor_names = []
    supervisor_emails = []
    contact_status = []
    routing_ready = []

    for key in df["examiner_norm"]:
        sup_name = pd.NA
        sup_email = pd.NA
        status = "MISSING_ADJUSTER_MAPPING"
        ready = False

        lookup_key = key
        if alias_map and key in alias_map:
            lookup_key = alias_map[key]

        if lookup_key in lookup:
            row = lookup[lookup_key]
            sup_name = row.get("supervisor_name", pd.NA)
            sup_email = row.get("supervisor_email", pd.NA)
            if pd.isna(sup_name) or str(sup_name).strip() == "":
                status = "MISSING_SUPERVISOR"
            elif pd.isna(sup_email) or str(sup_email).strip() == "":
                status = "MISSING_SUPERVISOR_EMAIL"
            else:
                status = "ROUTING_READY_SUPERVISOR"
                ready = True

        supervisor_names.append(sup_name)
        supervisor_emails.append(sup_email)
        contact_status.append(status)
        routing_ready.append(ready)

    df["supervisor_name"] = supervisor_names
    df["supervisor_email"] = supervisor_emails
    df["contact_status"] = contact_status
    df["routing_ready"] = routing_ready

    # cleanup helper column
    df = df.drop(columns=["examiner_norm"])
    return df
