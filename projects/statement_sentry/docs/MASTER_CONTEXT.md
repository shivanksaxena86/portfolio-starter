
# MASTER_CONTEXT: Project Statement-Sentry

## Project Overview
**Name:** Statement-Sentry
**Path:** `projects/statement_sentry/`
**Goal:** Local-first financial aggregator using Gmail API, Python, and local LLMs.

## Current Status (As of 6-Feb 2026)
- **Phase 1 (Ingestion) is 90% complete.**
- Successfully established Gmail Handshake (`handshake.py`).
- Developed `config.py` to manage settings for 7 different credit cards (HDFC, ICICI, YES, OneCard).
- Developed `collector.py` which can search, filter, and download PDF statements or extract text from email bodies.

- **Phase 2 (parsing) still developing**
Successfully parsed 47 transactions from HDFC Regalia, including International (USD) transactions. 
Extracted Statement Summary (Total Due, Min Due, Due Date). 
Next Step: Data Persistence (SQLite).

8-Feb-2026
- **Phase 1 (Collector):** Complete. Handles 7 cards via `config.py`.
- **Phase 2 (Parser/Vault):** Complete for HDFC Regalia. 
    - Decryption working via `processor.py`.
    - Robust Regex parsing (47 transactions) and Statement Summary extraction working.
    - SQLite Database (`statements.db`) implemented with Idempotency (Unique Hashing).
    - Date Normalization (ISO format) implemented.
- **Documentation:** PRD, Knowledge Base, KDD, and Master Context updated.


## Technical Context
- **Environment:** Windows 10, Python 3.11, Poetry.
- **Virtual Env:** Active at `.venv/`.
- **Secrets:** `credentials.json` and `token.json` are present but git-ignored.
- **Data:** Raw PDFs are stored in `data/raw_pdfs/` (git-ignored).

## Immediate Next Steps
1. **Develop `processor.py`**: Loop through `data/raw_pdfs/`, use passwords from `config.py` to decrypt files via `pikepdf`.
2. **Text Extraction**: Use `pdfplumber` to pull transaction rows from the decrypted PDFs.
3. **Database Schema**: Design the SQLite table structure to hold transactions.

## How to use this file
When starting a new session, provide this file to the AI and say: "Here is my MASTER_CONTEXT.md. We are working on Statement-Sentry. Pick up from Phase 2: The Parser."