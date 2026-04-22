# Payment Claim Detector Architecture Diagram

This diagram reflects the current working architecture as implemented in the repository.

It is intended for future AI agents and engineers who need a fast visual map of how data moves through the system and where state-specific logic is applied.

```mermaid
flowchart TD
    A[Tracker Workbook<br/>tracker.xlsx] --> B[parse_tracker_workbook_by_state]
    C[Register Workbook<br/>register.xlsx] --> D[parse_weekly_register]

    B --> E[Standardize tracker columns]
    E --> F[Normalize jurisdiction values<br/>CO NV AZ ID UT]
    F --> G[Bucket tracker rows by state]

    D --> H[Standardize register columns]
    H --> I[Optional date filter]
    I --> J[Optional TTD filter<br/>TTD or Temporary Total Disability]
    J --> K[Optional state filter]

    G --> L[count_tracker_matches]
    K --> L

    L --> M[Compute tracker_match_count]
    L --> N[Compute register_appearance_count]
    L --> O[Set is_new_claim<br/>tracker_match_count == 0]

    M --> P[detect_duplicate_payments]
    N --> P
    O --> P

    P --> Q[classify_rows]
    Q --> R[write_outputs]

    R --> S[detailed_results.xlsx]
    R --> T[summary_results.xlsx]
    R --> U[excluded_existing_claimants.xlsx]
    R --> V[processed_payment_log.csv]

    W[State-specific matching rules] --> L
    W --> W1[AZ ID NV UT<br/>full-key match:<br/>claim_number + last_name + first_name]
    W --> W2[CO<br/>fallback match:<br/>claim_number only]

    X[True New Claims output] --> R
    X --> X1[True New Claims]
    X --> X2[True New By State]
    X --> X3[True New CO]
    X --> X4[True New NV]
    X --> X5[True New ID]
    X --> X6[True New UT]
    X --> X7[True New AZ]
```

## Notes

- The state-scoped tracker parse is the backbone of the architecture. Future changes should not flatten all states into one historical pool.
- The definition of a true new claim is count-based, not classification-based.
- `tracker_match_count == 0` is the authoritative signal for tracker-new rows.
- `classification` is still useful, but duplicates and adjustments can override how a row is labeled in the classification sheets.
- Colorado is intentionally handled differently because its tracker structure does not provide split first and last claimant name columns in the same way as the other states.
- Arizona is now part of the explicit TTD state map and is processed with full-key matching.

## Macro Design Intent

The design is optimized for auditable Excel reconciliation, not for pretending the tracker is the authoritative system of record.

The long-term likely evolution is:

1. keep the tracker-based reconciliation path for operational review
2. add CareMC API validation later
3. distinguish "new to tracker" from "new to system of record" as separate concepts
