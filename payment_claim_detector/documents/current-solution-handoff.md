# Payment Claim Detector: Current Solution Handoff

## Purpose

This document is a distilled handoff of the current Payment Claim Detector implementation.

It is written for future AI agents and engineers who need to:

- understand what the system is actually doing today
- preserve the intent behind the current logic
- avoid reintroducing bugs that were already discovered and fixed
- extend the architecture without breaking the state-scoped comparison model

This project currently answers one narrow question well:

> Which TTD payment rows in the weekly register appear to represent claims that are new to the historical tracker, when evaluated by state?

It does **not** yet answer the broader enterprise question:

> Is this claim truly new to CareMC, the proprietary system of record?

That distinction matters. The tracker workbook is a human-maintained mirror of operational reality, not the authoritative source itself. The current solution is therefore a state-scoped Excel reconciliation system, not a source-of-truth platform integration.

---

## Executive Summary

The current implementation works by:

1. Parsing TTD tracker tabs by explicit state map.
2. Parsing the weekly payment register.
3. Normalizing inconsistent column names aggressively but safely.
4. Filtering register rows to TTD only.
5. Counting tracker matches by state.
6. Treating `tracker_match_count == 0` as the definition of a true new claim.
7. Classifying remaining rows for review and writing Excel outputs.

The most important architectural shift was moving away from a mixed logic model:

- old model: exact-match exclusion plus separate claim-number-only new-claim detection
- current model: one count-based model driven by state-scoped tracker match counts

That change fixed the earlier contradiction where a row could be excluded by identity logic or survive exclusion, but still be considered not new because its claim number existed somewhere in the tracker.

The current definition is now coherent:

> A row is a true new claim if, within its state, the tracker contains zero matching rows for the selected identity rule.

---

## Core Business Context

The team is effectively being asked to create an Excel mirror of software behavior that properly belongs in CareMC.

That has consequences:

- data quality is uneven
- headers vary by state and even by tab
- tracker structure is not uniform across jurisdictions
- the tracker is useful, but not authoritative
- perfect accuracy will require system integration later

The current strategy is pragmatic and appropriate:

- make the tracker comparison as accurate as possible
- make the logic state-aware
- keep results auditable in Excel
- leave room for future API augmentation

Future agents should preserve that mindset. Do not over-claim what the current outputs mean.

---

## Current Architecture

### Main flow

Primary orchestration lives in `src/payment_claim_detector/main.py`.

Current execution path:

1. `parse_tracker_workbook_by_state(tracker_file)`
2. `parse_weekly_register(register_file)`
3. optional date filtering
4. optional TTD-only filtering via `_build_ttd_mask()`
5. optional state scoping for targeted testing
6. `count_tracker_matches(register_df, tracker_by_state)`
7. optional processed-payment log lookup
8. `detect_duplicate_payments()`
9. `classify_rows()`
10. `write_outputs()`

### Major modules

- `src/payment_claim_detector/cli.py`
  - Typer CLI entrypoint
  - supports `--tracker-file`, `--register-file`, `--output-dir`, `--processed-log`, `--state`, `--ttd-only`

- `src/payment_claim_detector/main.py`
  - orchestration
  - TTD filter helper
  - console count summary
  - processed log update

- `src/payment_claim_detector/ingestion/tracker_parser.py`
  - explicit TTD sheet map
  - tracker parsing by state
  - jurisdiction normalization

- `src/payment_claim_detector/ingestion/register_parser.py`
  - weekly register parse and canonical column standardization

- `src/payment_claim_detector/compare/claim_detector.py`
  - state normalization
  - historical index logic
  - identity index logic
  - count-based tracker matching

- `src/payment_claim_detector/compare/classifier.py`
  - business classification rules

- `src/payment_claim_detector/outputs/writer.py`
  - Excel output generation
  - true new claims sheets
  - state breakdown sheets

- `src/payment_claim_detector/normalize/values.py`
  - loose header normalization
  - safe alias-based renaming

- `config/column_aliases.yaml`
  - alias registry for all canonical columns

---

## State Model

### States currently included

Tracker TTD sheet map is explicit, not inferred dynamically:

- `CO -> CO TTD`
- `NV -> NV TTD`
- `AZ -> AZ TTD`
- `ID -> ID TTD`
- `UT -> UT TTD`

State normalization must support both abbreviations and names.

Current normalization set includes:

- `CO`, `COLORADO`
- `NV`, `NEVADA`
- `AZ`, `ARIZONA`
- `ID`, `IDAHO`
- `UT`, `UTAH`

This normalization exists in both:

- `src/payment_claim_detector/ingestion/tracker_parser.py`
- `src/payment_claim_detector/compare/claim_detector.py`

Future agents should keep these maps synchronized.

---

## Definition of a True New Claim

The current system uses a count-based definition.

Each register row receives:

- `tracker_match_count`
- `register_appearance_count`
- `is_new_claim`

### Semantics

- `tracker_match_count`
  - how many matching tracker rows exist in the row's jurisdiction

- `register_appearance_count`
  - how many times that `(jurisdiction, claim_number)` appears in the current weekly register

- `is_new_claim`
  - `True` when `tracker_match_count == 0`

### Why this replaced the old model

The earlier logic had two distinct mechanisms:

1. exact-match claimant exclusion
2. claim-number-only new-claim detection

That created contradictions, especially when:

- claim number existed historically
- claimant identity did not match exactly
- output tabs appeared empty or misleading

The count-based model resolved that mismatch by making one state-scoped truth source drive the output.

---

## Matching Rules by State

### Default rule

If the tracker for a state contains all three identity columns:

- `claim_number`
- `claimant_last_name`
- `claimant_first_name`

Then matching is done on the full identity key:

`(claim_number, claimant_last_name, claimant_first_name)`

### Fallback rule

If a state tracker does **not** have the split claimant name columns, matching falls back to claim number only.

Current practical impact:

- `AZ`, `ID`, `NV`, `UT` use full-key matching because their tracker tabs provide split claimant names
- `CO` falls back to claim-number-only because its tracker structure is materially different

### Colorado caveat

Colorado is structurally different:

- it uses `Claimant:` rather than split first/last columns
- it still contains a valid claim number signal
- therefore CO currently uses claim-number fallback rather than full identity matching

This is intentional, not an accident.

Do not force CO into split-name matching unless the underlying tracker source changes or a reliable name parser is introduced.

---

## TTD Filtering Logic

TTD filtering lives in `_build_ttd_mask()` in `src/payment_claim_detector/main.py`.

### Important lesson

An earlier assumption was wrong:

- the system initially filtered on literal `TTD`
- the live register described TTD rows as `Temporary Total Disability`
- result: all TTD rows were incorrectly filtered out

The current filter intentionally matches both:

- `TTD`
- `Temporary Total ...`

This is a critical lesson for future agents:

> When a filter unexpectedly returns zero rows, inspect live values before blaming parsing or tracker logic.

---

## Column Normalization Strategy

### Why it matters

This project depends heavily on column normalization because the Excel sources are inconsistent.

Examples of real issues encountered:

- `Claim Number:` with punctuation
- `Jursidiction` misspelled in Idaho
- mixed spacing and punctuation across tabs
- state-specific alternative headers

### Current normalization behavior

Header normalization uses `_normalize_header_name()` in `src/payment_claim_detector/normalize/values.py`.

It normalizes by:

- lowercasing
- trimming whitespace
- stripping non-alphanumeric characters

This means headers like these normalize into the same matching space:

- `Claim Number`
- `Claim Number:`
- `claim-number`

### Critical bug that was fixed

Loose matching originally introduced a subtle bug:

- multiple raw columns could normalize to the same alias bucket
- a dict-based intermediate structure caused duplicate mappings
- downstream operations broke because a DataFrame was produced where a Series was expected

The fix was to:

- preserve the ordered list of existing columns
- track `used_existing`
- allow only the first valid canonical assignment per raw column

That behavior is now essential and should not be removed casually.

---

## Tracker Parsing Notes

Tracker parsing is explicit and state-bucketed.

### Important behaviors

- only expected TTD tabs are parsed
- if a tracker row includes its own jurisdiction column, that value is used
- if jurisdiction is missing, the parser falls back to the tab's default state
- parsed tracker rows are grouped into state buckets after normalization

### Arizona-specific note

`AZ TTD` is high-volume and wide.

Observed characteristics:

- it contains the required identity fields
- it contains many additional filler columns
- parser performance is acceptable because only known canonical columns matter downstream

Future agents should resist the temptation to over-model irrelevant AZ columns unless there is a business need.

---

## Classification Semantics

Classification lives in `src/payment_claim_detector/compare/classifier.py`.

Current order of precedence:

1. negative amount -> `ADJUSTMENT_REVIEW`
2. payment already processed -> `DUPLICATE_PAYMENT`
3. `is_new_claim == True` -> `NEW_CLAIM`
4. otherwise -> `EXISTING_CLAIM_NEW_PAYMENT`

This ordering matters.

For example:

- a row can be a true new claim by tracker logic
- but if its payment ID already exists in the processed log, the classification tab may show duplicate instead of new claim

That is why `True New Claims` output is now driven from `tracker_match_count == 0`, not solely from classification.

---

## Output Model

Outputs are written by `src/payment_claim_detector/outputs/writer.py`.

### Detailed Results workbook currently includes

- `Detailed Results`
- one sheet per classification value
- `True New Claims`
- `True New By State`
- `True New CO`
- `True New NV`
- `True New ID`
- `True New UT`
- `True New AZ`
- `Claim Number Not Found`

### Important output rule

Per-state True New sheets are written even when the count is zero.

This was deliberate.

Future reviewers often need to know whether a state was:

- not processed
- processed but empty
- processed with zero true new claims

Zero-row state sheets preserve that distinction.

### Summary workbook

`summary_results.xlsx` is generated from the classified DataFrame.

### Excluded workbook

`excluded_existing_claimants.xlsx` currently remains structurally present but is mostly empty under the new count-based approach because pre-filter exclusion is no longer the primary mechanism.

---

## Console Summary Design

The console summary prints:

- raw register rows
- rows after date filter, if used
- rows after TTD filter
- rows after state filter, if used
- total rows analyzed
- true new claims count
- existing claims count
- duplicate count, if present
- per-state breakdown
- classification breakdown

Important refinement:

- summary now prints even when the final filtered dataset is empty

That prevents silent runs that say only `Analysis complete!` and hide the real cause of the empty output.

---

## Wins

### 1. The logic is now state-scoped

This is the most important macro-level success.

Claims are no longer evaluated against a flattened multi-state history. The tracker is parsed by state, and comparisons are performed in-state.

### 2. The architecture is more honest

The current solution does not pretend to know what CareMC knows. It answers the narrower and defensible question: what is new to the tracker, by state?

### 3. True New Claims now reflect the real comparison model

`tracker_match_count == 0` is easy to understand, auditable, and directly explainable.

### 4. TTD-only filtering now reflects real data

The filter now matches the live payment descriptions instead of a narrow abbreviation assumption.

### 5. Output auditing improved

Per-state sheets, by-state summary, and explicit count summaries make troubleshooting materially easier.

### 6. Arizona is now integrated cleanly

AZ was added without a new architectural branch because the current design was already extensible enough to absorb it.

---

## Pitfalls and Failure Modes Already Discovered

### 1. Header mismatch is a first-class risk

Excel tabs are not trustworthy schema contracts.

Assume punctuation, misspelling, spacing, and naming variations will continue.

### 2. State maps must stay synchronized

If a state is added in tracker parsing but not in state normalization, matches will silently fail.

### 3. Set ordering bugs can be surprisingly destructive

One bug came from building claimant identity tuples from an unordered `set` of columns. That made tuple ordering unstable and caused exact-match logic to fail.

Always use explicit ordered column lists for identity tuple construction.

### 4. Reruns can distort classification via processed log reuse

`processed_payment_log.csv` is useful operationally, but it changes classification behavior on reruns.

This can make valid rows appear as duplicates even though the tracker comparison logic is unchanged.

### 5. Empty outputs are not always parser failures

The TTD filter returning zero rows initially looked like a tracker problem, but the real issue was a mismatch between filter assumptions and live payment descriptions.

### 6. Colorado is structurally special

CO should not be treated like AZ, ID, NV, or UT until its claimant naming structure supports equivalent identity logic.

---

## Lessons Learned

### Micro-level lessons

- Always inspect raw workbook headers before changing alias logic.
- Always inspect real value distributions before changing filters.
- Never rely on unordered collections for tuple semantics.
- When a workbook is wide, focus on required columns and ignore the noise.
- Empty output tabs usually indicate a logic or filter mismatch, not necessarily bad input files.

### Macro-level lessons

- Accuracy improved most when the model became state-aware.
- The best refinement was replacing mixed heuristics with one explicit count-based rule.
- Excel mirror systems should optimize for auditability, not false precision.
- Future API access to CareMC would be a major architectural upgrade, but the current tracker-first model still has operational value.

---

## Chronology of Important Refinements

This sequence matters because many later decisions only make sense in light of earlier failures.

1. narrowed the project to TTD-only tracker processing
2. replaced dynamic tracker assumptions with explicit state TTD tabs
3. removed stray debug-only Idaho filtering from orchestration
4. allowed tracker-provided jurisdiction values when available
5. normalized state names such as `Idaho -> ID`
6. loosened header matching to survive punctuation and spelling variants
7. fixed duplicate canonical column assignment in header normalization
8. confirmed Colorado used `Claim Number:` and not the plain variant
9. replaced exclude-plus-detect logic with count-based `tracker_match_count`
10. added `register_appearance_count`
11. broadened TTD filtering to match real payment descriptions
12. made console summaries print even for zero-result runs
13. added state-specific True New Claims sheets including zero-count states
14. added Arizona end to end

---

## Current Known Limitations

### 1. The tracker is not the system of record

This is the biggest limitation.

The tool currently detects what is new to the tracker, not what is new to CareMC.

### 2. Colorado still uses fallback logic

That is acceptable for now, but it is a known fidelity gap.

### 3. Classification and tracker-newness are related but not identical

Because duplicates and adjustments can override classification labels, future consumers must distinguish between:

- `tracker_match_count == 0`
- `classification == NEW_CLAIM`

### 4. Processed log behavior can confuse reviews

Rerunning against the same payment file without resetting the log can skew classification output.

---

## How a Future AI Should Extend This System

### Safe extensions

- add new states by updating both tracker parsing and state normalization together
- add new aliases only after confirming raw headers from live workbooks
- add targeted unit tests for each new state or structural exception
- keep true-new logic anchored to `tracker_match_count == 0`
- preserve state-specific output sheets for audit clarity

### Higher-value future work

- integrate CareMC API access for authoritative claim existence validation
- differentiate tracker-new from system-new as separate concepts in output
- formalize CO name parsing if the business needs stronger CO identity validation
- add explicit CLI control for whether to ignore or reset processed payment log behavior during review runs
- add fixture-based tracker parser tests for each TTD tab layout

### Unsafe extensions to avoid without evidence

- flattening all states into one historical pool
- removing header normalization safeguards
- redefining true-new status purely from classification
- treating CO as if it already had robust split-name identity support

---

## Operational Commands

### Typical all-state TTD run

```powershell
python -m payment_claim_detector.cli run `
  --tracker-file data/raw/tracker.xlsx `
  --register-file data/raw/register.xlsx `
  --output-dir data/outputs `
  --processed-log data/outputs/processed_payment_log.csv `
  --ttd-only
```

### Single-state targeted run

```powershell
python -m payment_claim_detector.cli run `
  --tracker-file data/raw/tracker.xlsx `
  --register-file data/raw/register.xlsx `
  --output-dir data/outputs `
  --processed-log data/outputs/processed_payment_log.csv `
  --state AZ `
  --ttd-only
```

### Test invocation

```powershell
& .\run_tests.ps1
```

---

## Snapshot From the Latest Verified Run

This snapshot is data-dependent and may change with future files, but it records the current observed behavior after Arizona was added.

All-state TTD register counts:

- `AZ`: 40 total, 0 true new
- `CO`: 147 total, 81 true new
- `ID`: 29 total, 0 true new
- `NV`: 181 total, 29 true new
- `UT`: 26 total, 0 true new

Interpretation:

- Arizona is now being parsed and evaluated correctly
- current live data does not show Arizona true new claims in the latest sample
- the absence of AZ true new claims is a result, not a parsing failure

---

## Final Guidance to Future Agents

If you inherit this codebase, treat the following as non-negotiable until proven otherwise:

1. keep matching state-scoped
2. keep true-new semantics count-based
3. preserve CO fallback behavior unless source data changes
4. inspect live headers and values before changing aliases or filters
5. remember that the tracker is a mirror, not the system of record

The current system is good because it is explicit, auditable, and increasingly accurate within the boundaries of Excel-based reconciliation.

That boundary is the key design truth.
