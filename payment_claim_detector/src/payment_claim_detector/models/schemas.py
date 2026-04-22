"""Data schemas using dataclasses."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class HistoricalClaimRecord:
    """Represents a claim record from the historical tracker."""
    jurisdiction: Optional[str]
    claim_number: str
    insured: Optional[str]
    claimant_first_name: Optional[str]
    claimant_last_name: Optional[str]
    full_name: Optional[str]
    last_check_sent: Optional[date]
    next_payment_to_be_sent: Optional[date]
    examiner: Optional[str]
    supervisor: Optional[str]
    comments: Optional[str]
    notes: Optional[str]
    source_sheet: str
    source_file: str


@dataclass
class PaymentEventRecord:
    """Represents a payment event from the weekly register."""
    jurisdiction: Optional[str]
    claim_number: str
    insured: Optional[str]
    claimant_first_name: Optional[str]
    claimant_last_name: Optional[str]
    check_date: Optional[date]
    service_start: Optional[date]
    service_end: Optional[date]
    amount_issued: Optional[Decimal]
    payment_description: Optional[str]
    payment_id: Optional[str]
    examiner: Optional[str]
    claim_type: Optional[str]
    source_sheet: str
    source_file: str


@dataclass
class ClassifiedResult:
    """Represents the result of classification."""
    classification: str
    classification_reason: str
    claim_number: str
    payment_id: Optional[str]
    jurisdiction: Optional[str]
    claimant_first_name: Optional[str]
    claimant_last_name: Optional[str]
    examiner: Optional[str]
    supervisor: Optional[str]
    amount_issued: Optional[float]
    payment_description: Optional[str]
    source_file: str
    source_sheet: str