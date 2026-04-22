# Payment Claim Detector

A Python tool for analyzing multi-state workers' compensation payment data. It ingests historical tracking workbooks and weekly payment registers to identify new claims, duplicate payments, and adjustments.

## Features

- Ingest multi-state payment tracking workbooks (NV, CO, AZ, ID, UT)
- Parse weekly payment registers
- Normalize inconsistent column names
- Detect new claims based on claim numbers
- Identify duplicate payments using Payment IDs
- Classify payments into categories (New Claim, Existing Claim/New Payment, Duplicate, Adjustment)
- Filter by date ranges
- Output detailed and summary Excel files

## Installation

```bash
pip install -e .
```

## Usage

```bash
payment-claim-detector run --tracker-file path/to/tracker.xlsx --register-file path/to/register.xlsx --output-dir ./outputs
```

## Project Structure

- `src/payment_claim_detector/`: Main package
- `config/`: Configuration files
- `data/`: Data directories
- `tests/`: Unit tests

## Development

1. Install dependencies: `pip install -e .[dev]`
2. Run tests: `pytest`
3. Format code: `black src/ tests/`

## Running Tests with Script

From the repository root, run either:

```powershell
.\run_tests.ps1
```

or:

```cmd
run_tests.cmd
```

You can also run the Python test runner directly if the venv is active:

```bash
python run_tests.py
```

## Configuration

Edit `config/settings.yaml` to customize behavior.