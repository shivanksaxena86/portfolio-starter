# Key Design Decisions (KDD) - Statement-Sentry

## KDD 01: Hybrid Data Extraction Strategy
* **Decision:** Use a deterministic Regex-based parser for core extraction, with a reserved path for LLM-based "Agentic" cleaning.
* **Context:** Standard PDF table extractors failed on HDFC Regalia's non-grid layout.
* **Alternative Considered:** Sending full PDFs to an LLM (OpenAI/Claude).
* **Reason for Pivot:** Privacy and Cost. Financial data is sensitive; local regex parsing is 100% private, free, and faster for structured transaction rows. LLMs will be used only for high-level "categorization" later.

## KDD 02: Local-First Persistence (SQLite)
* **Decision:** Use SQLite as the primary data vault.
* **Context:** Need a way to store transactions across sessions without cloud fees.
* **Reasoning:** SQLite is a "zero-config" database that lives as a single file in the repo. It ensures "Privacy by Design" because the data never leaves the user's D: drive.

## KDD 03: Idempotency via Transaction Hashing
* **Decision:** Implementation of a `UNIQUE` constraint on a composite hash (`date_description_amount`).
* **Context:** Risk of duplicate entries when re-running the parser on the same file during development or monthly updates.
* **Reasoning:** Ensures that the system can be run "n" times while maintaining a "Single Source of Truth" without data bloat.

## KDD 04: ISO 8601 Date Normalization
* **Decision:** Force-convert all bank date formats (DD/MM/YYYY, DD Mon, YYYY) to `YYYY-MM-DD`.
* **Reasoning:** Essential for database indexing, chronological sorting in the UI, and compatibility with external tools like PowerBI or Excel.

## KDD 05: Heuristic "Line-by-Line" Parsing vs. Table Extraction
* [cite_start]**Decision:** Replaced `pdfplumber.extract_table()` with a custom regex line-scanner. 
* [cite_start]**Context:** Standard table extractors failed to find any transactions (0 rows found) because HDFC Regalia PDFs use non-standard grid lines. 
* [cite_start]**Reasoning:** Line-scanning is more resilient to the specific "floating text" layout of bank statements where data is visually aligned but not programmatically "in a box."