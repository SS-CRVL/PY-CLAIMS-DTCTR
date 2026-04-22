from pathlib import Path

content = '''"""Comparison and detection modules."""

from .claim_detector import (
    build_historical_claim_index,
    build_historical_claim_set,
    detect_new_claims,
)
from .duplicate_detector import detect_duplicate_payments
from .classifier import classify_rows

__all__ = [
    "build_historical_claim_index",
    "build_historical_claim_set",
    "detect_new_claims",
    "detect_duplicate_payments",
    "classify_rows",
]
'''

path = Path('src/payment_claim_detector/compare/__init__.py')
path.write_text(content, encoding='utf-8')
print('Wrote', path)
