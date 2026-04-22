"""Tests for column normalization."""

import pandas as pd
import pytest

from payment_claim_detector.normalize.columns import CANONICAL_COLUMNS
from payment_claim_detector.normalize.values import standardize_columns


def test_standardize_columns_basic():
    """Test basic column standardization."""
    df = pd.DataFrame({
        "Claim Number": ["C001", "C002"],
        "Amount Issued": [100.0, 200.0],
        "Examiner": ["John", "Jane"]
    })

    result = standardize_columns(df, CANONICAL_COLUMNS)

    assert "claim_number" in result.columns
    assert "amount_issued" in result.columns
    assert "examiner" in result.columns
    assert list(result["claim_number"]) == ["C001", "C002"]


def test_standardize_columns_no_match():
    """Test with columns that don't match any aliases."""
    df = pd.DataFrame({
        "Unknown Column": [1, 2, 3],
        "Another Unknown": ["a", "b", "c"]
    })

    result = standardize_columns(df, CANONICAL_COLUMNS)

    # Columns should remain unchanged
    assert "Unknown Column" in result.columns
    assert "Another Unknown" in result.columns


def test_standardize_columns_matches_header_variants():
    """Test that punctuation and spacing variants still map correctly."""
    df = pd.DataFrame({
        " Claim No. ": ["C001"],
        "Claimant Last-Name": ["Smith"],
        "First_Name": ["John"],
        "Jur": ["ID"],
    })

    result = standardize_columns(df, CANONICAL_COLUMNS)

    assert "claim_number" in result.columns
    assert "claimant_last_name" in result.columns
    assert "claimant_first_name" in result.columns
    assert "jurisdiction" in result.columns
    assert result.loc[0, "claim_number"] == "C001"