#!/usr/bin/env python3

import argparse
import subprocess
from pathlib import Path

ROOT = Path(".")

WORKBOOK = ROOT / "Finance" / "reports" / "blufin_financial_statements.xlsx"
ACCOUNT_MAP = ROOT / "account_map.json"
STATEMENT_DIR = ROOT / "Finance" / "statements"


def discover_latest_statement():
    statements = sorted(STATEMENT_DIR.glob("*.csv"))
    if not statements:
        return None
    return statements[-1]


def main():
    parser = argparse.ArgumentParser(description="Rebuild Blufin financial reports from the Raw_GL ledger")
    parser.add_argument("--start-date", help="Report start date YYYY-MM-DD (overrides statement period)")
    parser.add_argument("--end-date", help="Report end date YYYY-MM-DD (overrides statement period)")
    args = parser.parse_args()

    if not WORKBOOK.exists():
        raise FileNotFoundError(f"Workbook not found: {WORKBOOK}")

    stmt = discover_latest_statement()

    if stmt is None and not (args.start_date and args.end_date):
        raise FileNotFoundError(
            "No statement CSV files found in Finance/statements. "
            "Use --start-date and --end-date to specify a reporting period."
        )

    cmd = [
        "python",
        "blufin_accounting_engine.py",
        "--xlsx-ledger", str(WORKBOOK),
        "--map", str(ACCOUNT_MAP),
        "--xlsx", str(WORKBOOK),
    ]
    # Only pass --stmt when no explicit date range is given; the statement's
    # ending balance only makes sense for the full statement period.
    if stmt is not None and not (args.start_date and args.end_date):
        cmd += ["--stmt", str(stmt)]
    if args.start_date:
        cmd += ["--start-date", args.start_date]
    if args.end_date:
        cmd += ["--end-date", args.end_date]

    subprocess.run(cmd, check=True)

    print(f"Workbook refreshed: {WORKBOOK}")


if __name__ == "__main__":
    main()