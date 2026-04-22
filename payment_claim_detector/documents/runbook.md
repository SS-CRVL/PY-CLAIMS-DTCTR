# Payment Claim Detector Runbook

This runbook is for operating the current CLI from the project root.

All commands below use the current supported entrypoint:

```powershell
python -m payment_claim_detector.cli run
```

## Preconditions

- Run commands from the `payment_claim_detector` project root.
- Close `tracker.xlsx`, `register.xlsx`, and output workbooks before running.
- The current payment-type filter implemented in the CLI is `--ttd-only`.
- If `--ttd-only` is omitted, the run includes all payment types currently present in the register.
- If `--processed-log` is included, reruns may classify rows as duplicate payments.

## Core Flags

- `--tracker-file`: tracker workbook path
- `--register-file`: register workbook path
- `--output-dir`: output directory path
- `--processed-log`: processed payment log CSV path
- `--state`: restrict run to one state
- `--ttd-only`: keep only TTD payments
- `--start-date`: optional date filter lower bound
- `--end-date`: optional date filter upper bound

## Canonical All-States Command

### All states, all payment types

```powershell
python -m payment_claim_detector.cli run `
  --tracker-file data/raw/tracker.xlsx `
  --register-file data/raw/register.xlsx `
  --output-dir data/outputs `
  --processed-log data/outputs/processed_payment_log.csv
```

### All states, TTD only

```powershell
python -m payment_claim_detector.cli run `
  --tracker-file data/raw/tracker.xlsx `
  --register-file data/raw/register.xlsx `
  --output-dir data/outputs `
  --processed-log data/outputs/processed_payment_log.csv `
  --ttd-only
```

## State-Specific Commands

### Arizona, all payment types

```powershell
python -m payment_claim_detector.cli run `
  --tracker-file data/raw/tracker.xlsx `
  --register-file data/raw/register.xlsx `
  --output-dir data/outputs `
  --processed-log data/outputs/processed_payment_log.csv `
  --state AZ
```

### Arizona, TTD only

```powershell
python -m payment_claim_detector.cli run `
  --tracker-file data/raw/tracker.xlsx `
  --register-file data/raw/register.xlsx `
  --output-dir data/outputs `
  --processed-log data/outputs/processed_payment_log.csv `
  --state AZ `
  --ttd-only
```

### Colorado, all payment types

```powershell
python -m payment_claim_detector.cli run `
  --tracker-file data/raw/tracker.xlsx `
  --register-file data/raw/register.xlsx `
  --output-dir data/outputs `
  --processed-log data/outputs/processed_payment_log.csv `
  --state CO
```

### Colorado, TTD only

```powershell
python -m payment_claim_detector.cli run `
  --tracker-file data/raw/tracker.xlsx `
  --register-file data/raw/register.xlsx `
  --output-dir data/outputs `
  --processed-log data/outputs/processed_payment_log.csv `
  --state CO `
  --ttd-only
```

### Idaho, all payment types

```powershell
python -m payment_claim_detector.cli run `
  --tracker-file data/raw/tracker.xlsx `
  --register-file data/raw/register.xlsx `
  --output-dir data/outputs `
  --processed-log data/outputs/processed_payment_log.csv `
  --state ID
```

### Idaho, TTD only

```powershell
python -m payment_claim_detector.cli run `
  --tracker-file data/raw/tracker.xlsx `
  --register-file data/raw/register.xlsx `
  --output-dir data/outputs `
  --processed-log data/outputs/processed_payment_log.csv `
  --state ID `
  --ttd-only
```

### Nevada, all payment types

```powershell
python -m payment_claim_detector.cli run `
  --tracker-file data/raw/tracker.xlsx `
  --register-file data/raw/register.xlsx `
  --output-dir data/outputs `
  --processed-log data/outputs/processed_payment_log.csv `
  --state NV
```

### Nevada, TTD only

```powershell
python -m payment_claim_detector.cli run `
  --tracker-file data/raw/tracker.xlsx `
  --register-file data/raw/register.xlsx `
  --output-dir data/outputs `
  --processed-log data/outputs/processed_payment_log.csv `
  --state NV `
  --ttd-only
```

### Utah, all payment types

```powershell
python -m payment_claim_detector.cli run `
  --tracker-file data/raw/tracker.xlsx `
  --register-file data/raw/register.xlsx `
  --output-dir data/outputs `
  --processed-log data/outputs/processed_payment_log.csv `
  --state UT
```

### Utah, TTD only

```powershell
python -m payment_claim_detector.cli run `
  --tracker-file data/raw/tracker.xlsx `
  --register-file data/raw/register.xlsx `
  --output-dir data/outputs `
  --processed-log data/outputs/processed_payment_log.csv `
  --state UT `
  --ttd-only
```

## Clean Rerun Commands

If you want to evaluate tracker-new logic without prior payment IDs changing classification to `DUPLICATE_PAYMENT`, omit the processed log:

### All states, TTD only, no processed log

```powershell
python -m payment_claim_detector.cli run `
  --tracker-file data/raw/tracker.xlsx `
  --register-file data/raw/register.xlsx `
  --output-dir data/outputs `
  --ttd-only
```

### One state, TTD only, no processed log

```powershell
python -m payment_claim_detector.cli run `
  --tracker-file data/raw/tracker.xlsx `
  --register-file data/raw/register.xlsx `
  --output-dir data/outputs `
  --state AZ `
  --ttd-only
```

## Optional Date-Scoped Run

```powershell
python -m payment_claim_detector.cli run `
  --tracker-file data/raw/tracker.xlsx `
  --register-file data/raw/register.xlsx `
  --output-dir data/outputs `
  --processed-log data/outputs/processed_payment_log.csv `
  --ttd-only `
  --start-date 2026-01-01 `
  --end-date 2026-01-31
```

## Expected Console Summary Shape

Successful runs print a count summary like:

```text
--------------------------------------
  COUNT SUMMARY
--------------------------------------
  Register rows (raw)         : 1117
  After TTD filter            : 383  (-734 non-TTD)
--------------------------------------
  Total rows analysed         : 383
  True New Claims (count = 0) : 110
  Existing claims             : 273
--------------------------------------
```

The live code currently also prints a by-state section and a classification breakdown when rows remain after filtering.

## Output Files

Current run outputs are written to `data/outputs`:

- `detailed_results.xlsx`
- `summary_results.xlsx`
- `excluded_existing_claimants.xlsx`
- `processed_payment_log.csv`

`detailed_results.xlsx` currently includes:

- `Detailed Results`
- classification sheets
- `True New Claims`
- `True New By State`
- one `True New <STATE>` sheet for each processed state, even when count is zero
- `Claim Number Not Found`

## Troubleshooting

### Output shows zero TTD rows

This usually means the payment-type filter assumptions do not match the live register values.

Current live data uses `Temporary Total Disability`, and the implemented filter already accounts for that.

### Output classifications are all duplicates

This usually means `processed_payment_log.csv` already contains the payment IDs from the current register.

Use a clean rerun command without `--processed-log` if you want to inspect tracker-new logic without duplicate classification interference.

### A state is missing from the output

Check three things:

1. the tracker workbook includes the expected `<STATE> TTD` sheet
2. state normalization includes both the code and long-form name
3. the register actually contains rows for that state after filtering
