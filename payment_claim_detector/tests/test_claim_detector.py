"""Tests for state-aware claim detection logic."""

import pandas as pd

from payment_claim_detector.compare.claim_detector import (
    count_tracker_matches,
    build_historical_claim_index,
    build_tracker_identity_index,
    detect_new_claims,
    exclude_existing_claimant_rows,
)


def test_build_historical_claim_index_by_state():
    tracker_by_state = {
        "NV": pd.DataFrame({"claim_number": ["NV123", "NV456"]}),
        "CO": pd.DataFrame({"claim_number": ["CO111", "CO222"]}),
    }

    index = build_historical_claim_index(tracker_by_state)

    assert index["NV"] == {"NV123", "NV456"}
    assert index["CO"] == {"CO111", "CO222"}


def test_detect_new_claims_uses_state_scoped_index():
    tracker_by_state = {
        "NV": pd.DataFrame({"claim_number": ["NV123"]}),
        "CO": pd.DataFrame({"claim_number": ["CO111"]}),
    }
    historical_index = build_historical_claim_index(tracker_by_state)

    register_df = pd.DataFrame(
        [
            {"claim_number": "NV123", "jurisdiction": "NV"},
            {"claim_number": "CO111", "jurisdiction": "CO"},
            {"claim_number": "NV999", "jurisdiction": "NV"},
            {"claim_number": "CO999", "jurisdiction": "CO"},
            {"claim_number": "NV123", "jurisdiction": "CO"},
            {"claim_number": "UNKNOWN", "jurisdiction": None},
        ]
    )

    result = detect_new_claims(register_df, historical_index)

    assert list(result["is_new_claim"]) == [
        False,
        False,
        True,
        True,
        True,
        True,
    ]


def test_detect_new_claims_respects_state_separation():
    tracker_by_state = {
        "NV": pd.DataFrame({"claim_number": ["NV123"]}),
        "CO": pd.DataFrame({"claim_number": ["CO123"]}),
    }
    historical_index = build_historical_claim_index(tracker_by_state)

    register_df = pd.DataFrame(
        [
            {"claim_number": "NV123", "jurisdiction": "NV"},
            {"claim_number": "NV123", "jurisdiction": "CO"},
            {"claim_number": "CO123", "jurisdiction": "CO"},
            {"claim_number": "CO123", "jurisdiction": "NV"},
        ]
    )

    result = detect_new_claims(register_df, historical_index)

    assert list(result["is_new_claim"]) == [
        False,
        True,
        False,
        True,
    ]


def test_detect_new_claims_falls_back_for_unknown_state():
    tracker_by_state = {
        "NV": pd.DataFrame({"claim_number": ["NV123"]}),
    }
    historical_index = build_historical_claim_index(tracker_by_state)

    register_df = pd.DataFrame(
        [
            {"claim_number": "NV123", "jurisdiction": "CO"},
            {"claim_number": "NV123", "jurisdiction": ""},
            {"claim_number": "NV999", "jurisdiction": ""},
        ]
    )

    result = detect_new_claims(register_df, historical_index)

    assert list(result["is_new_claim"]) == [
        True,
        False,
        True,
    ]


def test_detect_new_claims_normalizes_arizona_state_name():
    tracker_by_state = {
        "AZ": pd.DataFrame({"claim_number": ["AZ123"]}),
    }
    historical_index = build_historical_claim_index(tracker_by_state)

    register_df = pd.DataFrame(
        [
            {"claim_number": "AZ123", "jurisdiction": "Arizona"},
            {"claim_number": "AZ999", "jurisdiction": "Arizona"},
        ]
    )

    result = detect_new_claims(register_df, historical_index)

    assert list(result["is_new_claim"]) == [
        False,
        True,
    ]


def test_exclude_existing_claimant_rows():
    tracker_by_state = {
        "NV": pd.DataFrame({
            "claim_number": ["NV123", "NV456"],
            "claimant_last_name": ["Smith", "Jones"],
            "claimant_first_name": ["John", "Mary"],
        }),
    }
    identity_index = build_tracker_identity_index(tracker_by_state)

    register_df = pd.DataFrame(
        [
            {
                "claim_number": "NV123",
                "jurisdiction": "NV",
                "claimant_last_name": "Smith",
                "claimant_first_name": "John",
            },
            {
                "claim_number": "NV123",
                "jurisdiction": "NV",
                "claimant_last_name": "Smith",
                "claimant_first_name": "Johnny",
            },
            {
                "claim_number": "CO111",
                "jurisdiction": "CO",
                "claimant_last_name": "Smith",
                "claimant_first_name": "John",
            },
        ]
    )

    result = exclude_existing_claimant_rows(register_df, identity_index)

    assert len(result) == 2
    assert result.iloc[0]["claim_number"] == "NV123"
    assert result.iloc[0]["claimant_first_name"] == "Johnny"
    assert result.iloc[1]["jurisdiction"] == "CO"


def test_count_tracker_matches_uses_full_key_and_claim_fallback_by_state():
    tracker_by_state = {
        "UT": pd.DataFrame(
            {
                "claim_number": ["UT123", "UT123", "UT999"],
                "claimant_last_name": ["Smith", "Smith", "Jones"],
                "claimant_first_name": ["John", "John", "Mary"],
            }
        ),
        "CO": pd.DataFrame(
            {
                "claim_number": ["CO111", "CO111", "CO222"],
            }
        ),
    }

    register_df = pd.DataFrame(
        [
            {
                "jurisdiction": "UT",
                "claim_number": "UT123",
                "claimant_last_name": "Smith",
                "claimant_first_name": "John",
            },
            {
                "jurisdiction": "UT",
                "claim_number": "UT123",
                "claimant_last_name": "Smith",
                "claimant_first_name": "Johnny",
            },
            {
                "jurisdiction": "CO",
                "claim_number": "CO111",
                "claimant_last_name": "Any",
                "claimant_first_name": "Name",
            },
            {
                "jurisdiction": "CO",
                "claim_number": "CO999",
                "claimant_last_name": "Any",
                "claimant_first_name": "Name",
            },
        ]
    )

    result = count_tracker_matches(register_df, tracker_by_state)

    assert list(result["tracker_match_count"]) == [2, 0, 2, 0]
    assert list(result["is_new_claim"]) == [False, True, False, True]


def test_count_tracker_matches_uses_arizona_full_key_matching():
    tracker_by_state = {
        "AZ": pd.DataFrame(
            {
                "claim_number": ["AZ123", "AZ123", "AZ999"],
                "claimant_last_name": ["Smith", "Smith", "Jones"],
                "claimant_first_name": ["John", "John", "Mary"],
            }
        ),
    }

    register_df = pd.DataFrame(
        [
            {
                "jurisdiction": "Arizona",
                "claim_number": "AZ123",
                "claimant_last_name": "Smith",
                "claimant_first_name": "John",
            },
            {
                "jurisdiction": "AZ",
                "claim_number": "AZ123",
                "claimant_last_name": "Smith",
                "claimant_first_name": "Johnny",
            },
        ]
    )

    result = count_tracker_matches(register_df, tracker_by_state)

    assert list(result["tracker_match_count"]) == [2, 0]
    assert list(result["is_new_claim"]) == [False, True]


def test_count_tracker_matches_adds_register_appearance_count_by_state_and_claim():
    tracker_by_state = {"UT": pd.DataFrame({"claim_number": ["UT123"]})}
    register_df = pd.DataFrame(
        [
            {"jurisdiction": "UT", "claim_number": "UT123"},
            {"jurisdiction": "UT", "claim_number": "UT123"},
            {"jurisdiction": "UT", "claim_number": "UT999"},
            {"jurisdiction": "CO", "claim_number": "UT123"},
        ]
    )

    result = count_tracker_matches(register_df, tracker_by_state)

    assert list(result["register_appearance_count"]) == [2, 2, 1, 1]
