# Blufin Labs Accounting Engine

A lightweight accounting tool for small businesses with relatively low transaction counts.

It is designed to support a simple and reliable workflow:

- bank CSV import
- transaction categorization and review
- master ledger stored in Excel
- Profit & Loss
- Balance Sheet
- Cash Flow
- XLSX export with charts and quarter-over-quarter summary analysis

The system intentionally uses **Excel as the master ledger** to keep the accounting transparent, auditable, and easy to edit.

---

# Quick Start (Windows PowerShell)

The normal workflow has two commands:

### 1. Import new bank statements and update the ledger

```powershell
python run_blufin_books.py
```

This will:

* locate new statement CSV files
* parse and normalize transactions
* allow interactive categorization review
* merge transactions into the **Raw_GL ledger**
* regenerate financial statements

---

### 2. Rebuild reports after editing the ledger

If you manually edit the Excel ledger (recommended for counterparty cleanup or category corrections):

```powershell
python update_books.py
```

This regenerates:

* Summary
* Profit & Loss
* Balance Sheet
* Cash Flow

without modifying the Raw_GL ledger.

---

# Overview

The accounting engine consists of five primary scripts:

* `run_blufin_books.py`
* `update_books.py`
* `import_stmt.py`
* `review_transactions.py`
* `blufin_accounting_engine.py`

Typical workflow:

1. Download bank statement CSV
2. Place it in the `Finance/statements` directory
3. Run the import workflow
4. Review uncategorized transactions
5. Inspect or edit the Raw_GL ledger
6. Generate updated financial statements

---

# Directory Layout

Example working directory:

```text
blufin_accounting_engine/
|
|-- run_blufin_books.py
|-- update_books.py
|-- import_stmt.py
|-- review_transactions.py
|-- blufin_accounting_engine.py
|
|-- categorization_rules.json
|-- vendor_aliases.json
|-- account_map.json
|
|-- processed_statements.json
|-- new_transactions.csv
|
|-- Finance/
|   |-- statements/
|   |   `-- stmt_YYYY_MM_DD.csv
|   |
|   `-- reports/
|       `-- blufin_financial_statements.xlsx
|
`-- README.md
```

---

# Master Ledger

The Excel workbook is the authoritative ledger.

```
Finance/reports/blufin_financial_statements.xlsx
```

The master ledger sheet is:

```
Raw_GL
```

Columns:

| Column       | Description                           |
| ------------ | ------------------------------------- |
| date         | transaction date                      |
| description  | original bank description             |
| amount       | positive = income, negative = expense |
| category     | accounting category                   |
| counterparty | vendor or customer                    |
| account      | optional account field                |
| memo         | optional notes                        |

You may safely edit the following fields:

* category
* counterparty
* memo

Reports are rebuilt from this ledger.

---

# Financial Reports Generated

The workbook contains these sheets:

* `Raw_GL`
* `Summary`
* `P&L`
* `Balance Sheet`
* `Cash Flow`

Only **Raw_GL** should be edited manually.

All other sheets are regenerated automatically.

---

# Step 1 - Import Bank Statements

Place the bank CSV into:

```
Finance/statements
```

Example:

```
stmt_2026_03_10.csv
```

Run:

```bash
python run_blufin_books.py
```

This performs:

1. CSV parsing
2. transaction normalization
3. automatic categorization
4. interactive review of uncategorized transactions
5. merge into Raw_GL ledger
6. generation of financial reports

---

# Step 2 - Review Uncategorized Transactions

During import you may see the review menu:

```
Select review action:
1. Uncategorized Income
2. Uncategorized Expense
3. Balance Sheet Adjustment
```

For each transaction the system will:

1. display the transaction
2. suggest categories
3. allow assignment
4. optionally create a permanent vendor rule

Over time the system becomes smarter through rule learning.

---

# Step 3 - Edit the Ledger (Optional but Recommended)

Open:

```
Finance/reports/blufin_financial_statements.xlsx
```

Edit the **Raw_GL** sheet.

Typical edits:

* assign customer names to income
* clean vendor names
* adjust categories
* add memos

---

# Step 4 - Rebuild Financial Reports

After editing the ledger:

```bash
python update_books.py
```

This regenerates the entire workbook from Raw_GL.

---

# XLSX Workbook Contents

## Summary sheet

The Summary page includes:

### Income vs Customer pie chart

This chart uses the `counterparty` field.

If no counterparty is provided the system groups income under:

```
Unspecified
```

---

### Rolling Income & Expense Totals chart

Displays cumulative monthly totals for:

* Rolling Income
* Rolling Expense

---

### Quarter-over-Quarter P&L comparison

The comparison table shows:

* Current Quarter
* Previous Quarter
* Percent Change

Highlighting rules:

* **income reductions greater than 10%**
* **expense increases greater than 10%**

---

# Balance Sheet Logic

Balance sheet values are derived from the bank statement header.

Assets:

```
Assets = statement ending balance
```

Equity:

```
Equity =
  beginning retained earnings
+ current period earnings
+ equity activity from ledger
```

Equity activity includes categories such as:

```
Owner Draw
Owner Contribution
Balance Sheet Adjustment
```

The Balance Sheet includes a validation line:

```
Balance Check
```

The accounting identity must hold:

```
Assets - Liabilities - Equity = 0
```

---

# Categorization Rules

Automatic categorization is controlled by:

```
categorization_rules.json
```

Example:

```json
{
  "contains": [
    {"match": "DIGI-KEY", "category": "Electronic Components"},
    {"match": "THORLABS", "category": "Optical Components"},
    {"match": "XOMETRY", "category": "Machining/Fabrication"},
    {"match": "OPENAI", "category": "Software"}
  ]
}
```

---

# Vendor Aliasing

Vendor normalization is controlled by:

```
vendor_aliases.json
```

Example:

```json
{
  "Thorlabs": ["THORLAB", "THORLABS INC"],
  "Digikey": ["DIGI KEY", "DIGI-KEY"]
}
```

Example transformation:

```
8904THORLABS324*
```

becomes:

```
Thorlabs
```

---

# Account Mapping

Financial statement presentation is controlled by:

```
account_map.json
```

Example:

```json
{
  "categories": {
    "Electronic Components": {
      "statement_type": "expense",
      "report_name": "Electronic Components"
    },
    "Consulting Revenue": {
      "statement_type": "income",
      "report_name": "Consulting Revenue"
    }
  }
}
```

Supported statement types:

```
income
expense
asset
liability
equity
```

---

# Adding New Categories

To add a category update both files.

### categorization_rules.json

Example:

```json
{"match": "OSH PARK", "category": "PCB Fabrication"}
```

### account_map.json

```json
"PCB Fabrication": {
  "statement_type": "expense",
  "report_name": "PCB Fabrication"
}
```

---

# Dependencies

Install required packages:

```bash
pip install pandas openpyxl
```

---

# Typical Workflow

Import and categorize:

```bash
python run_blufin_books.py
```

Update reports after manual edits:

```bash
python update_books.py
```

---

# PowerShell Note (Windows)

If you use multiline commands in PowerShell, use the **backtick (`)** character for line continuation.

Example:

```powershell
python import_stmt.py `
  --input stmt.csv `
  --output transactions.csv `
  --rules categorization_rules.json
```

If PowerShell shows this error:

```
Missing expression after unary operator '--'
```

use either:

* single-line commands (recommended)
* backticks for multiline continuation

---

# Notes

* `categorization_rules.json` controls classification
* `account_map.json` controls financial statement presentation
* the Raw_GL worksheet is the master ledger
* the engine raises an error if a category exists in the ledger but not in `account_map.json`
* the system is designed for practical small-business reporting rather than GAAP audit compliance

---

# Recommended Future Improvements

Possible enhancements:

* bank-specific CSV importers
* automated vendor rule suggestions
* depreciation tracking
* invoice / customer lookup integration
* tax summary reporting
* year-end archive process
* Git versioning of accounting history

---

# License

Internal use for Blufin Labs financial operations only.
