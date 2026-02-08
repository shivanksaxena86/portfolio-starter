import os
import re
from datetime import datetime

import pdfplumber
from database import init_db, save_transactions


def normalize_date(date_str):
    """Converts various date formats to ISO YYYY-MM-DD."""
    date_str = date_str.strip()
    # Handle DD/MM/YYYY (e.g., 20/12/2025)
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        pass

    # Handle DD Mon, YYYY (e.g., 10 Feb, 2026)
    try:
        # Remove common ordinal suffixes if they exist
        clean_date = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_str)
        return datetime.strptime(clean_date, "%d %b, %Y").strftime("%Y-%m-%d")
    except ValueError:
        pass

    return date_str  # Return as-is if all else fails


def clean_amount(amt_str):
    if not amt_str:
        return 0.0
    clean_str = re.sub(r"[^\d.-]", "", str(amt_str).replace(",", ""))
    try:
        return float(clean_str)
    except (ValueError, TypeError):
        return 0.0


def parse_hdfc_regalia(pdf_path):
    all_transactions = []
    summary_data = {
        "total_due": "Not Found",
        "min_due": "Not Found",
        "due_date": "Not Found",
        "credit_limit": "Not Found",
    }

    date_pattern = re.compile(r"(\d{2}/\d{2}/\d{4})")
    amount_pattern = re.compile(r"([0-9,]+\.\d{2})")

    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"

        # 1. Surgical Summary Extraction using split and lookahead
        # We search for the label and look at the immediate surrounding text
        summary_patterns = {
            "total_due": r"TOTAL AMOUNT DUE[\s\n]+([\d,.]+)",
            "min_due": r"MINIMUM DUE[\s\n]+([\d,.]+)",
            "due_date": r"DUE DATE[\s\n]+(\d{1,2}\s\w+,\s\d{4})",
            "credit_limit": r"TOTAL CREDIT LIMIT[\s\n]+([\d,.]+)",
        }

        for key, pattern in summary_patterns.items():
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                summary_data[key] = normalize_date(val) if key == "due_date" else val

        # 2. Transaction Extraction
        lines = full_text.split("\n")
        for line in lines:
            date_match = date_pattern.search(line)
            if date_match:
                raw_date = date_match.group(1)
                amounts = amount_pattern.findall(line)

                if amounts:
                    txn_amount = clean_amount(amounts[-1])
                    description = line.replace(raw_date, "").replace(amounts[-1], "").strip()
                    description = re.sub(r"\d{2}:\d{2}", "", description)  # Remove time
                    description = re.sub(r"\+\d+", "", description)  # Remove rewards
                    description = description.strip(" |")

                    all_transactions.append(
                        {
                            "date": normalize_date(raw_date),
                            "description": description or "Transaction",
                            "amount": txn_amount,
                            "currency": "USD" if "USD" in line.upper() else "INR",
                        }
                    )

    return summary_data, all_transactions


def run_parser():
    init_db()  # Ensure DB exists
    decrypted_dir = "projects/statement_sentry/data/decrypted_pdfs"
    filename = "unlocked_HDFC_REGALIA_831.pdf"
    test_file = os.path.join(decrypted_dir, filename)

    if os.path.exists(test_file):
        summary, txns = parse_hdfc_regalia(test_file)

        print("--- Statement Summary ---")
        for k, v in summary.items():
            print(f"{k.upper()}: {v}")

        # Save to Database
        new_rows = save_transactions(filename, txns)
        print(f"\n✅ Found {len(txns)} transactions. Added {new_rows} new rows to DB.")

        for i, t in enumerate(txns[:5]):
            print(f"{i+1}. {t['date']} | {t['amount']:>10.2f} | {t['description']}")
    else:
        print("File not found.")


if __name__ == "__main__":
    run_parser()
