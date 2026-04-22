"""Canonical column definitions and aliases."""

from payment_claim_detector.settings import load_column_aliases

# Load canonical columns from config
CANONICAL_COLUMNS = load_column_aliases()

# Default fallback if config not found
if not CANONICAL_COLUMNS:
    CANONICAL_COLUMNS = {
        "jurisdiction": ["Jurisdiction", "State"],
        "insured": ["Insured", "Employer"],
        "claim_number": ["Claim Number", "Claim #", "ClaimNumber"],
        "claimant_first_name": ["Claimant First Name", "First Name"],
        "claimant_last_name": ["Claimant Last Name", "Last Name"],
        "full_name": ["Full Name", "Claimant Name"],
        "date_of_loss": ["Date of Loss", "DOI"],
        "service_start": ["Starting Service Date", "Starting DOS"],
        "service_end": ["Ending Service Date", "Ending DOS"],
        "amount_issued": ["Amount Issued", "Amount"],
        "payment_description": ["Payment Description", "Description"],
        "check_date": ["Check Date", "Payment Date"],
        "payment_id": ["Payment ID", "PaymentID"],
        "examiner": ["Examiner", "Adjuster"],
        "supervisor": ["Supervisor"],
        "comments": ["Comments", "Notes"],
        "claim_type": ["Claim Type"],
    }