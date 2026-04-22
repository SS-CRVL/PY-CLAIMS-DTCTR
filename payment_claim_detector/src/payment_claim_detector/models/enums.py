"""Enumeration types."""

from enum import Enum


class Classification(str, Enum):
    """Payment classification categories."""
    NEW_CLAIM = "NEW_CLAIM"
    EXISTING_CLAIM_NEW_PAYMENT = "EXISTING_CLAIM_NEW_PAYMENT"
    DUPLICATE_PAYMENT = "DUPLICATE_PAYMENT"
    ADJUSTMENT_REVIEW = "ADJUSTMENT_REVIEW"
    UNCLASSIFIED_REVIEW = "UNCLASSIFIED_REVIEW"


class StateCode(str, Enum):
    """Supported state codes."""
    NV = "NV"
    CO = "CO"
    AZ = "AZ"
    ID = "ID"
    UT = "UT"