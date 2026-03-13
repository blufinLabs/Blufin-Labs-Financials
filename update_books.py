#!/usr/bin/env python3

import subprocess
from pathlib import Path

ROOT = Path(".")

WORKBOOK = ROOT / "Finance" / "reports" / "blufin_financial_statements.xlsx"
ACCOUNT_MAP = ROOT / "account_map.json"
STATEMENT_DIR = ROOT / "Finance" / "statements"


def discover_latest_statement():
    statements = sorted(STATEMENT_DIR.glob("*.csv"))
    if not statements:
        raise FileNotFoundError("No statement CSV files found in Finance/statements")
    return statements[-1]


def main():
    if not WORKBOOK.exists():
        raise FileNotFoundError(f"Workbook not found: {WORKBOOK}")

    stmt = discover_latest_statement()

    subprocess.run(
        [
            "python",
            "blufin_accounting_engine.py",
            "--xlsx-ledger", str(WORKBOOK),
            "--map", str(ACCOUNT_MAP),
            "--stmt", str(stmt),
            "--xlsx", str(WORKBOOK),
        ],
        check=True,
    )

    print(f"Workbook refreshed: {WORKBOOK}")


if __name__ == "__main__":
    main()