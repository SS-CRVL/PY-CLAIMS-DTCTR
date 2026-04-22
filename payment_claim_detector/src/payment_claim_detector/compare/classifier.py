"""Payment row classification logic."""

import pandas as pd

from payment_claim_detector.models.enums import Classification


def classify_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Classify each payment row into categories.

    Args:
        df: DataFrame with detection columns ('is_new_claim', 'is_duplicate_payment')

    Returns:
        DataFrame with 'classification' and 'classification_reason' columns added
    """
    out = df.copy()

    def _classify(row) -> tuple[str, str]:
        amount = row.get("amount_issued")
        is_new_claim = bool(row.get("is_new_claim", False))
        is_duplicate = bool(row.get("is_duplicate_payment", False))

        if pd.notna(amount) and amount < 0:
            return Classification.ADJUSTMENT_REVIEW.value, "Negative payment amount"

        if is_duplicate:
            return Classification.DUPLICATE_PAYMENT.value, "Payment ID already processed"

        if is_new_claim:
            return Classification.NEW_CLAIM.value, "Claim number not found in historical tracker"

        if not is_new_claim and not is_duplicate:
            return (
                Classification.EXISTING_CLAIM_NEW_PAYMENT.value,
                "Claim exists historically but payment is new"
            )

        return Classification.UNCLASSIFIED_REVIEW.value, "Unable to classify"

    classifications = out.apply(_classify, axis=1, result_type="expand")
    out["classification"] = classifications[0]
    out["classification_reason"] = classifications[1]

    return out