#!/usr/bin/env python3

import argparse
import csv
import json
from pathlib import Path

import pandas as pd


def find_transactions(lines):
    for i, line in enumerate(lines):
        if line.startswith("Date,Description,Amount,Running Bal."):
            return i
    raise Exception("Transaction section not found")


def parse_amount(x):
    s = str(x).replace(",", "").replace('"', "").strip()
    if s == "":
        return 0.0
    return float(s)


def parse_transaction_amount(row):
    amt = parse_amount(row.get("Amount", ""))
    desc = str(row.get("Description", ""))

    if amt == 0.0 and "BEGINNING BALANCE" in desc.upper():
        return parse_amount(row.get("Running Bal.", ""))

    return amt


def load_rules(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def categorize(desc, rules, amount):
    desc_upper = desc.upper()

    for rule in rules.get("contains", []):
        if rule["match"].upper() in desc_upper:
            return rule["category"]

    if amount > 0:
        return rules["default_credit_category"]

    return rules["default_debit_category"]


def get_opening_balance_override(date_str, desc, amount):
    try:
        dt = pd.to_datetime(date_str)
    except Exception:
        return None

    desc_u = str(desc).upper()
    if "BEGINNING BALANCE" in desc_u and dt.month == 12 and dt.day == 31 and amount != 0:
        return "Retained Earnings"

    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--rules", required=True)
    args = parser.parse_args()

    rules = load_rules(args.rules)

    with open(args.input, "r", encoding="utf-8-sig") as f:
        lines = f.read().splitlines()

    start = find_transactions(lines)
    reader = csv.DictReader(lines[start:])

    rows = []
    for r in reader:
        date = r["Date"]
        desc = r["Description"]
        amt = parse_transaction_amount(r)

        override = get_opening_balance_override(date, desc, amt)
        if override is not None:
            category = override
        else:
            category = categorize(desc, rules, amt)

        rows.append(
            {
                "date": date,
                "description": desc,
                "amount": amt,
                "category": category,
                "counterparty": "",
                "account": rules.get("cash_account", "Checking"),
                "memo": "",
            }
        )

    df = pd.DataFrame(rows)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)

    print(f"Imported {len(df)} transactions to {args.output}")
    print("\nCategory counts:")
    print(df["category"].value_counts().to_string())


if __name__ == "__main__":
    main()