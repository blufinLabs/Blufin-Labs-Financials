#!/usr/bin/env python3

import argparse
import csv
import json
import re
from pathlib import Path

import pandas as pd


def format_currency(amount):
    sign = "-" if amount < 0 else ""
    return f"{sign}${abs(float(amount)):,.2f}"


def parse_amount(x):
    s = str(x).replace(",", "").replace('"', "").strip()
    if s == "":
        return 0.0
    return float(s)


def load_rules(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_rules(path, rules):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2)


def load_account_map(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_transactions(df, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def find_transactions(lines):
    for i, line in enumerate(lines):
        if line.startswith("Date,Description,Amount,Running Bal."):
            return i
    raise Exception("Transaction section not found")


def get_last_nonempty_cell(row):
    for cell in reversed(row):
        val = str(cell).strip()
        if val != "":
            return val
    return ""


def parse_statement_header(stmt_path):
    with open(stmt_path, "r", encoding="utf-8-sig") as f:
        lines = f.read().splitlines()

    tx_start_idx = find_transactions(lines)

    header = {
        "beginning_balance_label": "Beginning balance",
        "beginning_balance": 0.0,
        "total_credits": 0.0,
        "total_debits": 0.0,
        "ending_balance_label": "Ending balance",
        "ending_balance": 0.0,
    }

    for line in lines[:tx_start_idx]:
        if not line.strip():
            continue

        row = next(csv.reader([line]))
        if not row:
            continue

        label = str(row[0]).strip() if len(row) > 0 else ""
        if not label or label.upper() == "DESCRIPTION":
            continue

        value = get_last_nonempty_cell(row)
        label_u = label.upper()

        if "BEGINNING BALANCE AS OF" in label_u:
            header["beginning_balance_label"] = label
            header["beginning_balance"] = parse_amount(value)
        elif "TOTAL CREDITS" in label_u:
            header["total_credits"] = parse_amount(value)
        elif "TOTAL DEBITS" in label_u:
            header["total_debits"] = parse_amount(value)
        elif "ENDING BALANCE AS OF" in label_u:
            header["ending_balance_label"] = label
            header["ending_balance"] = parse_amount(value)

    return header


def print_header(statement_header, statement_date):
    report_date = pd.Timestamp.today().strftime("%Y-%m-%d")
    print("\n========================================================================")
    print("TRANSACTION REVIEW")
    print("------------------------------------------------------------------------")
    print(
        f"{statement_header.get('beginning_balance_label', 'Beginning balance')}: "
        f"{format_currency(statement_header.get('beginning_balance', 0.0))}"
    )
    print(f"Total credits: {format_currency(statement_header.get('total_credits', 0.0))}")
    print(f"Total debits:  {format_currency(statement_header.get('total_debits', 0.0))}")
    print(
        f"{statement_header.get('ending_balance_label', 'Ending balance')}: "
        f"{format_currency(statement_header.get('ending_balance', 0.0))}"
    )
    print(f"Statement Date: {statement_date}")
    print(f"Report Date:   {report_date}")
    print()


def extract_vendor_key(desc):
    desc = str(desc).upper()

    noise_tokens = [
        "DES:", "ID:", "INDN:", "CO", "WEB", "PURCHASE", "REFUND", "DEBIT",
        "CARD", "BILL", "PAYMENT", "ONLINE", "BANKING", "TRANSFER", "CONFIRMATION"
    ]
    for token in noise_tokens:
        desc = desc.replace(token, " ")

    cleaned = []
    for ch in desc:
        if ch.isalnum() or ch in " -/*.&":
            cleaned.append(ch)
        else:
            cleaned.append(" ")

    parts = " ".join("".join(cleaned).split()).split()

    filtered = []
    for p in parts:
        if p.count("/") == 2:
            continue
        if p.isdigit():
            continue
        if p.startswith("*"):
            continue
        filtered.append(p)

    if not filtered:
        return desc[:20].strip()

    return " ".join(filtered[:3]).strip()


def normalize_vendor_name(name):
    s = str(name).strip()
    if not s:
        return ""

    s = re.sub(r"[^A-Za-z0-9 &.\-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    words = []
    for w in s.split():
        if len(w) <= 3 and w.isupper():
            words.append(w)
        else:
            words.append(w.capitalize())

    return " ".join(words)


def load_vendor_aliases():
    path = Path("vendor_aliases.json")
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("aliases", {})


def canonicalize_vendor(name, aliases):
    if not name:
        return ""

    normalized = normalize_vendor_name(name)
    normalized_upper = normalized.upper()

    # Exact alias key
    for alias, canonical in aliases.items():
        if normalized_upper == alias.upper():
            return canonical

    # Contains match fallback
    for alias, canonical in aliases.items():
        if alias.upper() in normalized_upper:
            return canonical

    return normalized


def infer_vendor_name_from_description(desc):
    raw = str(desc)

    patterns = [
        r"(THORLABS)",
        r"(DIGI[\-\s]?KEY)",
        r"(MOUSER)",
        r"(MCMASTER[\-\s]?CARR)",
        r"(XOMETRY)",
        r"(ADVANCED CIRCUITS)",
        r"(OPENAI)",
        r"(FIGMA)",
        r"(INTUIT)",
        r"(NEWEGG)",
        r"(CENTRAL COMPUTERS)",
        r"(EDMUND)",
        r"(NEWPORT)",
        r"(BASLER)",
        r"(TEKTRONIX)",
        r"(KEYSIGHT)",
        r"(KEITHLEY)",
        r"(PRECITEC)",
    ]

    raw_u = raw.upper()
    for pat in patterns:
        m = re.search(pat, raw_u)
        if m:
            found = m.group(1)
            if found in {"DIGI KEY", "DIGI-KEY"}:
                return "Digi-Key"
            return normalize_vendor_name(found)

    cleaned = re.sub(r"[^A-Za-z ]", " ", raw)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if not cleaned:
        return ""

    words = cleaned.split()
    if not words:
        return ""

    candidate = " ".join(words[:3])
    return normalize_vendor_name(candidate)


def get_category_lists(account_map):
    income = []
    expense = []
    bs = []

    for name, cfg in account_map.get("categories", {}).items():
        st = cfg.get("statement_type")
        if st == "income":
            income.append(name)
        elif st == "expense":
            expense.append(name)
        elif st in {"asset", "liability", "equity"}:
            bs.append(name)

    income = [x for x in income if x != "Uncategorized Income"]
    expense = [x for x in expense if x != "Uncategorized Expense"]

    return sorted(income), sorted(expense), sorted(bs)


def choose_category(category_list, title):
    print(title)
    print("------------------------------------------------------------------------")
    for i, cat in enumerate(category_list, start=1):
        print(f"  {i}. {cat}")
    print(f"  {len(category_list) + 1}. Skip transaction")
    print(f"  {len(category_list) + 2}. Return to review menu")

    choice = input("Choose option: ").strip()

    try:
        n = int(choice)
    except ValueError:
        return "__SKIP__"

    if n == len(category_list) + 1:
        return "__SKIP__"
    if n == len(category_list) + 2:
        return "__MENU__"
    if 1 <= n <= len(category_list):
        return category_list[n - 1]

    return "__SKIP__"


def maybe_add_vendor_rule(desc, category, rules, rules_path, custom_vendor=None):
    if custom_vendor:
        vendor_key = normalize_vendor_name(custom_vendor)
    else:
        vendor_key = extract_vendor_key(desc)

    if not vendor_key:
        return

    print()
    print(f"Vendor rule candidate: {vendor_key} -> {category}")
    learn = input("Save vendor rule? [y/N]: ").strip().lower()

    if learn != "y":
        return

    exists = any(r["match"].upper() == vendor_key.upper() for r in rules.get("contains", []))
    if exists:
        print("A rule for that vendor key already exists.")
        return

    rules.setdefault("contains", [])
    rules["contains"].insert(0, {"match": vendor_key, "category": category})
    save_rules(rules_path, rules)
    print(f"Saved new rule: {vendor_key} -> {category}")


def suggest_vendor_rule(df, vendor, category, rules, rules_path):
    if not vendor:
        return

    vendor = str(vendor).strip()
    if not vendor:
        return

    vendor_rows = df[df["counterparty"].str.upper() == vendor.upper()]
    if len(vendor_rows) < 3:
        return

    same_category = vendor_rows[vendor_rows["category"] == category]
    if len(same_category) < 3:
        return

    exists = any(
        r["match"].upper() == vendor.upper()
        for r in rules.get("contains", [])
    )
    if exists:
        return

    print()
    print("------------------------------------------------")
    print("Suggested vendor rule")
    print("------------------------------------------------")
    print(f"{vendor} -> {category}")
    print("Based on repeated transaction history.")
    save = input("Create this rule automatically? [Y/n]: ").strip().lower()

    if save == "n":
        return

    rules.setdefault("contains", [])
    rules["contains"].insert(0, {
        "match": vendor,
        "category": category
    })
    save_rules(rules_path, rules)
    print("Vendor rule added.")


def process_queue(
    df,
    queue_name,
    category_list,
    rules,
    rules_path,
    statement_header,
    vendor_aliases,
    allow_vendor_name=False
):
    queue_indices = [
        idx for idx in df.sort_values("date").index
        if df.loc[idx, "category"] == queue_name
    ]

    if not queue_indices:
        print(f"\nNo transactions found in {queue_name}.")
        return df

    for idx in queue_indices:
        row = df.loc[idx]
        if str(row["category"]) != queue_name:
            continue

        statement_date = pd.to_datetime(row["date"]).strftime("%Y-%m-%d")
        desc = str(row["description"])
        amount = float(row["amount"])

        print_header(statement_header, statement_date)
        print(f"Queue:        {queue_name}")
        print(f"Description:  {desc}")
        print(f"Amount:       {format_currency(amount)}")
        print()

        selected = choose_category(category_list, "Assign category:")

        if selected == "__MENU__":
            print("Returning to review menu.")
            break

        if selected == "__SKIP__":
            continue

        df.at[idx, "category"] = str(selected)

        canonical_vendor = ""
        if allow_vendor_name:
            inferred = infer_vendor_name_from_description(desc)
            inferred = canonicalize_vendor(inferred, vendor_aliases)

            prompt = f"Vendor / customer name [default: {inferred if inferred else 'none'}]: "
            entered = input(prompt).strip()

            custom_vendor = entered if entered else inferred
            canonical_vendor = canonicalize_vendor(custom_vendor, vendor_aliases)

            if canonical_vendor:
                df.at[idx, "counterparty"] = canonical_vendor

        print(f"Assigned category: {selected}")

        if allow_vendor_name and canonical_vendor:
            suggest_vendor_rule(df, canonical_vendor, selected, rules, rules_path)

        maybe_add_vendor_rule(
            desc,
            selected,
            rules,
            rules_path,
            custom_vendor=canonical_vendor if canonical_vendor else None
        )

    return df


def review_transactions(df, rules, rules_path, account_map, statement_header, vendor_aliases):
    income_categories, expense_categories, bs_categories = get_category_lists(account_map)

    while True:
        income_count = int((df["category"] == "Uncategorized Income").sum())
        expense_count = int((df["category"] == "Uncategorized Expense").sum())
        bs_count = int((df["category"] == "Balance Sheet Adjustment").sum())

        unresolved_total = income_count + expense_count + bs_count

        if unresolved_total == 0:
            print("\nNo unresolved transactions remain.")
            return df

        statement_date = pd.to_datetime(df["date"]).min().strftime("%Y-%m-%d")
        print_header(statement_header, statement_date)
        print("Select review action:")
        print("  1. Uncategorized Income")
        print("  2. Uncategorized Expense")
        print("  3. Balance Sheet Adjustment")
        print("  9. Exit review")

        top = input("Choose option [default 9]: ").strip()
        if top == "":
            top = "9"

        if top == "9":
            print("Exiting review.")
            break

        if top == "1":
            df = process_queue(
                df,
                "Uncategorized Income",
                income_categories,
                rules,
                rules_path,
                statement_header,
                vendor_aliases,
                allow_vendor_name=True,
            )

        elif top == "2":
            df = process_queue(
                df,
                "Uncategorized Expense",
                expense_categories,
                rules,
                rules_path,
                statement_header,
                vendor_aliases,
                allow_vendor_name=False,
            )

        elif top == "3":
            unresolved_mask = df["category"].isin(["Uncategorized Income", "Uncategorized Expense"])
            if unresolved_mask.any():
                move = input(
                    "Move currently unresolved transactions into Balance Sheet Adjustment queue? [y/N]: "
                ).strip().lower()
                if move == "y":
                    df.loc[unresolved_mask, "category"] = "Balance Sheet Adjustment"

            df = process_queue(
                df,
                "Balance Sheet Adjustment",
                bs_categories,
                rules,
                rules_path,
                statement_header,
                vendor_aliases,
                allow_vendor_name=False,
            )

        else:
            print("Invalid choice.")

    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--rules", required=True)
    parser.add_argument("--map", required=True)
    parser.add_argument("--stmt", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Force text columns to string/object so user-entered values work reliably
    for col in ["description", "category", "counterparty", "account", "memo"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str)

    # Normalize numeric/date columns
    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    rules = load_rules(args.rules)
    account_map = load_account_map(args.map)
    statement_header = parse_statement_header(args.stmt)
    vendor_aliases = load_vendor_aliases()

    df = review_transactions(
        df,
        rules,
        args.rules,
        account_map,
        statement_header,
        vendor_aliases
    )

    save_transactions(df, args.output)

    print(f"\nSaved reviewed transactions to {args.output}")
    print("\nFinal category counts:")
    print(df["category"].value_counts().to_string())


if __name__ == "__main__":
    main()