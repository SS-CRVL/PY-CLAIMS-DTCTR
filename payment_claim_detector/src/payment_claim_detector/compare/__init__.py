"""Comparison and detection modules."""

from .claim_detector import (
    build_historical_claim_index,
    build_tracker_identity_index,
    build_historical_claim_set,
    detect_new_claims,
    exclude_existing_claimant_rows,
    count_tracker_matches,
)
from .duplicate_detector import detect_duplicate_payments
from .classifier import classify_rows

__all__ = [
    "build_historical_claim_index",
    "build_tracker_identity_index",
    "build_historical_claim_set",
    "detect_new_claims",
    "exclude_existing_claimant_rows",
    "count_tracker_matches",
    "detect_duplicate_payments",
    "classify_rows",
]
