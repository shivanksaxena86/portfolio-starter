import os
import sqlite3

DB_PATH = "projects/statement_sentry/data/processed/statements.db"


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Table for tracking which files we have already processed
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS processed_files (
            filename TEXT PRIMARY KEY,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Table for the actual transactions
    # We create a 'tx_hash' to prevent duplicates: date + description + amount
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            date TEXT,
            description TEXT,
            amount REAL,
            currency TEXT,
            category TEXT DEFAULT 'Uncategorized',
            tx_hash TEXT UNIQUE,
            FOREIGN KEY (filename) REFERENCES processed_files (filename)
        )
    """
    )

    conn.commit()
    conn.close()


def save_transactions(filename, transactions):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Track the file
    cursor.execute("INSERT OR IGNORE INTO processed_files (filename) VALUES (?)", (filename,))

    count = 0
    for tx in transactions:
        # Create a unique hash to prevent duplicate rows from the same or different files
        tx_hash = f"{tx['date']}_{tx['description']}_{tx['amount']}"
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO transactions 
                (filename, date, description, amount, currency, tx_hash) 
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (filename, tx["date"], tx["description"], tx["amount"], tx["currency"], tx_hash),
            )
            if cursor.rowcount > 0:
                count += 1
        except sqlite3.Error:
            continue

    conn.commit()
    conn.close()
    return count


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
