"""New claim detection logic."""

from typing import Dict, Set, Tuple, Union

import pandas as pd

STATE_CODE_MAP = {
    "CO": "CO",
    "COLORADO": "CO",
    "NV": "NV",
    "NEVADA": "NV",
    "AZ": "AZ",
    "ARIZONA": "AZ",
    "ID": "ID",
    "IDAHO": "ID",
    "UT": "UT",
    "UTAH": "UT",
}


def _normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""

    return str(value).strip().upper()


def _normalize_state(value: object) -> str:
    normalized = _normalize_text(value)
    return STATE_CODE_MAP.get(normalized, normalized)


def build_historical_claim_index(
    tracker_by_state: Dict[str, pd.DataFrame]
) -> Dict[str, Set[str]]:
    """Build a state-scoped index of historical claim numbers.

    Args:
        tracker_by_state: Mapping of state codes to tracker DataFrames

    Returns:
        Mapping of state codes to sets of claim numbers
    """
    index: Dict[str, Set[str]] = {}

    for state, df in tracker_by_state.items():
        if "claim_number" not in df.columns:
            index[state] = set()
            continue

        claim_numbers = df["claim_number"].dropna().apply(_normalize_text)
        claim_numbers = claim_numbers[claim_numbers.astype(bool)]
        index[state] = set(claim_numbers.tolist())

    return index


def build_tracker_identity_index(
    tracker_by_state: Dict[str, pd.DataFrame]
) -> Dict[str, Set[Tuple[str, str, str]]]:
    """Build a state-scoped identity index of tracker claimants.

    The index is keyed by (claim_number, claimant_last_name, claimant_first_name)
    after trimming and uppercasing.
    """
    index: Dict[str, Set[Tuple[str, str, str]]] = {}
    ordered_cols = [
        "claim_number",
        "claimant_last_name",
        "claimant_first_name",
    ]
    required_cols = set(ordered_cols)

    for state, df in tracker_by_state.items():
        if not required_cols.issubset(df.columns):
            index[state] = set()
            continue

        subset = (
            df[ordered_cols]
            .dropna()
            .apply(lambda x: tuple(_normalize_text(v) for v in x), axis=1)
        )

        index[state] = set(subset.tolist())

    return index


def build_historical_claim_set(tracker_df: pd.DataFrame) -> Set[str]:
    """Build a flat set of historical claim numbers from tracker data."""
    if "claim_number" not in tracker_df.columns:
        return set()

    claim_numbers = tracker_df["claim_number"].dropna().apply(_normalize_text)
    claim_numbers = claim_numbers[claim_numbers.astype(bool)]
    return set(claim_numbers.tolist())


def detect_new_claims(
    register_df: pd.DataFrame,
    historical_claims: Union[Set[str], Dict[str, Set[str]]],
) -> pd.DataFrame:
    """Detect claims that are new compared to historical data.

    Args:
        register_df: DataFrame from weekly register
        historical_claims: Flat claim set or state-scoped historical claim index

    Returns:
        DataFrame with 'is_new_claim' column added
    """
    out = register_df.copy()

    if "claim_number" not in out.columns:
        out["is_new_claim"] = False
        return out

    if isinstance(historical_claims, dict):
        fallback_claims = set().union(*historical_claims.values()) if historical_claims else set()

        def _is_new(row) -> bool:
            claim_number = _normalize_text(row.get("claim_number", ""))
            state = _normalize_state(row.get("jurisdiction", ""))

            if not claim_number:
                return False

            if state:
                if state in historical_claims:
                    return claim_number not in historical_claims[state]
                return True

            return claim_number not in fallback_claims

        out["is_new_claim"] = out.apply(_is_new, axis=1)
        return out

    normalized_claims = out["claim_number"].apply(_normalize_text)
    out["is_new_claim"] = ~normalized_claims.isin(historical_claims)
    return out


def exclude_existing_claimant_rows(
    register_df: pd.DataFrame,
    tracker_identity_index: Dict[str, Set[Tuple[str, str, str]]],
) -> pd.DataFrame:
    """Exclude rows that exactly match an existing tracker claimant identity."""
    out = register_df.copy()

    required_cols = {
        "claim_number",
        "claimant_last_name",
        "claimant_first_name",
    }
    if not required_cols.issubset(out.columns):
        return out

    def should_exclude(row) -> bool:
        state = _normalize_state(row.get("jurisdiction", ""))
        claim = _normalize_text(row.get("claim_number", ""))
        last = _normalize_text(row.get("claimant_last_name", ""))
        first = _normalize_text(row.get("claimant_first_name", ""))

        if not (state and claim and last and first):
            return False

        if state not in tracker_identity_index:
            return False

        return (claim, last, first) in tracker_identity_index[state]

    mask = out.apply(should_exclude, axis=1)
    return out.loc[~mask].copy()


def count_tracker_matches(
    register_df: pd.DataFrame,
    tracker_by_state: Dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Count how many tracker rows match each register row's identity.

    For states whose tracker has claim_number + claimant_last_name + claimant_first_name:
        Matches on all three fields (full identity key).
    For states without split name columns (e.g. CO):
        Falls back to claim_number only.

    Adds columns:
        tracker_match_count       — times this identity appears in the tracker (0 = True New Claim)
        register_appearance_count — times this claim appears in the current register this week
        is_new_claim              — True when tracker_match_count == 0
    """
    FULL_KEY_COLS = {"claim_number", "claimant_last_name", "claimant_first_name"}

    # Build per-state lookup tables from tracker data
    full_key_counts: Dict[str, dict] = {}
    claim_only_counts: Dict[str, Dict[str, int]] = {}

    for state, df in tracker_by_state.items():
        if FULL_KEY_COLS.issubset(df.columns):
            norm = pd.DataFrame({
                "claim_number": df["claim_number"].apply(_normalize_text),
                "claimant_last_name": df["claimant_last_name"].apply(_normalize_text),
                "claimant_first_name": df["claimant_first_name"].apply(_normalize_text),
            })
            # Only count rows where all three fields are populated
            valid = norm[norm[["claim_number", "claimant_last_name", "claimant_first_name"]].apply(
                lambda r: all(r), axis=1
            )]
            full_key_counts[state] = (
                valid.groupby(["claim_number", "claimant_last_name", "claimant_first_name"])
                .size()
                .to_dict()
            )
        elif "claim_number" in df.columns:
            norm_claims = df["claim_number"].apply(_normalize_text)
            valid_claims = norm_claims[norm_claims.astype(bool)]
            claim_only_counts[state] = valid_claims.value_counts().to_dict()

    out = register_df.copy()

    # Register appearance count: how many payments this week share (jurisdiction, claim_number)
    if "claim_number" in out.columns and "jurisdiction" in out.columns:
        reg_key = out.apply(
            lambda r: (
                _normalize_state(r.get("jurisdiction", "")),
                _normalize_text(r.get("claim_number", "")),
            ),
            axis=1,
        )
        out["register_appearance_count"] = reg_key.map(reg_key.value_counts())
    else:
        out["register_appearance_count"] = 1

    # Tracker match count per register row
    def _count_match(row) -> int:
        state = _normalize_state(row.get("jurisdiction", ""))
        claim = _normalize_text(row.get("claim_number", ""))
        if not (state and claim):
            return 0
        if state in full_key_counts:
            last = _normalize_text(row.get("claimant_last_name", ""))
            first = _normalize_text(row.get("claimant_first_name", ""))
            if last and first:
                return full_key_counts[state].get((claim, last, first), 0)
        # Fallback to claim-number-only lookup
        return claim_only_counts.get(state, {}).get(claim, 0)

    out["tracker_match_count"] = out.apply(_count_match, axis=1)
    out["is_new_claim"] = out["tracker_match_count"] == 0

    return out
