# Copilot Instructions for Blufin Labs Financials

## Project Overview

This is a lightweight Python-based accounting system for Blufin Labs. It imports bank statement CSVs, categorizes transactions, merges them into an Excel master ledger (`Raw_GL`), and regenerates financial reports (P&L, Balance Sheet, Cash Flow, Summary).

## Repository Layout

```
├── blufin_accounting_engine.py   # Core report generation engine
├── run_blufin_books.py           # Main entry point: import + review + merge + report
├── update_books.py               # Rebuild reports from existing Raw_GL (no import)
├── import_stmt.py                # Parse bank CSV → new_transactions.csv
├── review_transactions.py        # Interactive transaction categorization review
│
├── categorization_rules.json     # Auto-categorization rules (keyword → category)
├── vendor_aliases.json           # Vendor name normalization map
├── account_map.json              # Category → statement type/report name mapping
│
├── processed_statements.json     # Tracks already-processed statement files (by hash)
├── new_transactions.csv          # Staging file for newly imported transactions
│
└── Finance/
    ├── statements/               # Place bank CSV exports here (stmt_YYYY_MM_DD.csv)
    └── reports/
        └── blufin_financial_statements.xlsx  # Master Excel workbook (authoritative ledger)
```

## Key Architecture Decisions

- **Excel is the master ledger.** The `Raw_GL` worksheet in `blufin_financial_statements.xlsx` is the single source of truth. All other sheets are regenerated automatically and should not be edited manually.
- **No database.** State is stored in JSON config files and the Excel workbook.
- **Deduplication** is done via MD5 hash of `date|description|amount` in `run_blufin_books.py`.
- **Statement tracking** uses SHA-256 file hashes stored in `processed_statements.json` to avoid reprocessing.

## Raw_GL Schema

| Column | Description |
|---|---|
| `date` | Transaction date (YYYY-MM-DD) |
| `description` | Original bank description |
| `amount` | Positive = income, negative = expense |
| `category` | Accounting category (must exist in `account_map.json`) |
| `counterparty` | Vendor or customer name |
| `account` | Account identifier (e.g., "Checking") |
| `memo` | Optional notes |

## Coding Conventions

- **Python 3.10+** with standard library + `pandas` and `openpyxl`.
- All scripts use `argparse` for CLI options and `#!/usr/bin/env python3` shebangs.
- Paths are managed with `pathlib.Path`, not raw strings.
- Monetary amounts are `float`. Positive = income/credit, negative = expense/debit.
- Date strings in the ledger are formatted as `YYYY-MM-DD`.
- JSON config files use UTF-8 encoding; CSV files use `utf-8-sig` (BOM-aware) for Excel compatibility.
- Excel styling uses `openpyxl` directly (no xlsxwriter). Header fill is `1F4E78` (dark blue) with white bold font.
- Categorization falls back to `default_credit_category` or `default_debit_category` from `categorization_rules.json`.

## Configuration Files

### `categorization_rules.json`
Controls automatic transaction categorization:
```json
{
  "cash_account": "Checking",
  "default_credit_category": "Uncategorized Income",
  "default_debit_category": "Uncategorized Expense",
  "contains": [
    {"match": "DIGI-KEY", "category": "Electronic Components"}
  ]
}
```

### `account_map.json`
Maps categories to financial statement types:
```json
{
  "categories": {
    "Electronic Components": {
      "statement_type": "expense",
      "report_name": "Electronic Components"
    }
  }
}
```
Valid `statement_type` values: `income`, `expense`, `asset`, `liability`, `equity`.

**Important:** Every category that appears in the Raw_GL ledger must have an entry in `account_map.json`. The engine will raise an error if a category is missing.

### `vendor_aliases.json`
Maps canonical vendor names to lists of raw string patterns:
```json
{
  "Thorlabs": ["THORLAB", "THORLABS INC"]
}
```

## Common Workflows

### Full import workflow
```bash
python run_blufin_books.py
```
Place new bank CSVs in `Finance/statements/` before running.

### Rebuild reports only (after editing Raw_GL)
```bash
python update_books.py
```

### Custom date range report
```bash
python update_books.py --start-date 2025-01-01 --end-date 2025-03-31
```

### Install dependencies
```bash
pip install pandas openpyxl
```

## Adding a New Transaction Category

1. Add a rule to `categorization_rules.json` under `"contains"`:
   ```json
   {"match": "OSH PARK", "category": "PCB Fabrication"}
   ```
2. Add the category to `account_map.json`:
   ```json
   "PCB Fabrication": {"statement_type": "expense", "report_name": "PCB Fabrication"}
   ```

## Testing

There is no automated test suite. Validate changes manually by:
1. Running `python run_blufin_books.py` with a sample CSV in `Finance/statements/`.
2. Verifying the generated `blufin_financial_statements.xlsx` opens correctly and balances (`Balance Check = 0`).
3. Running `python update_books.py --start-date YYYY-MM-DD --end-date YYYY-MM-DD` and confirming all sheets are regenerated.

## Windows / PowerShell Note

Use backticks (`` ` ``) for multiline command continuation in PowerShell, not backslashes.
