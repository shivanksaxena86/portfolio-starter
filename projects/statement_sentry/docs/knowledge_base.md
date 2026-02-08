
# Knowledge Base & Troubleshooting Log

## Issue 1: Poetry Command Not Recognized
- **Problem:** Running `poetry add` resulted in `CommandNotFoundException` in Windows PowerShell.
- **Cause:** The `pipx` binary folder was not in the system's PATH variable in the specific terminal session.
- **Fix:** Activated the `.venv` specifically. Realized that in VS Code, restarting the terminal after environment setup allows the shell to correctly inherit the PATH and the active virtual environment.

## Issue 2: Empty Notebook Commit Failure
- **Problem:** Pre-commit hooks failed when trying to commit an empty `.ipynb` file.
- **Cause:** `nbqa` and other hooks expect a valid JSON structure for Jupyter Notebooks; a 0-byte file is invalid.
- **Fix:** Created the notebook through the VS Code UI (which generates the metadata) and added a placeholder cell before committing.

## Issue 3: Google API "Unverified App" Warning
- **Problem:** During the OAuth handshake, Google blocked the login with a security warning.
- **Cause:** The Google Cloud project is in "Testing" mode, and the user email wasn't added as a "Test User."
- **Fix:** Added the specific Gmail address to the "Test Users" section in the Google Cloud Console OAuth Consent screen.

## Issue 4: Diverse Bank Statement Formats
- **Problem:** Some banks send PDFs, while others (OneCard) send data in the email body.
- **Strategy Change:** Moved from a single-script approach to a `config.py` driven architecture to handle different "Ingestion Types" (PDF vs. Email_Body).


Challenge: Filename patterns from banks are inconsistent and don't match our initial prefix logic. Fix: Implemented a get_card_key_from_filename helper function using keyword searching (e.g., "AMAZON", "5522") to map files to configs dynamically.
## Issue 5: PDF Decryption Failures due to Filename Mismatches
- **Problem:** The `processor.py` script skipped all files, reporting "No password config found."
- **Cause:** Initial logic expected files to have a clean prefix (e.g., `HDFC_REGALIA_...`). However, bank filenames are inconsistent and often start with card numbers or internal IDs (e.g., `5522XXXX...`).
- **Fix:** Developed a robust mapping function `get_card_key_from_filename()`. This uses keyword detection (searching for "AMAZON", "TATA", or specific card digits) within the filename to dynamically link the file to its correct password in `config.py`. 
- **Learning:** Don't assume external data (filenames) will follow your internal naming conventions; build "translation" logic to handle the real world.

## Issue 6: Table Extraction Returns Zero Rows
- **Problem:** `parser.py` reported "Found 0 transactions" despite the PDF clearly containing data.
- **Cause:** Heuristic Mismatch. The initial script looked for a date in `row[0]`. In the actual HDFC PDF, the first column contains both "DATE & TIME" (stacked vertically), and the table headers or sub-headers (like "Domestic Transactions") interfere with simple row detection.
- **Fix:** Switched to a more flexible "Keyword-based" row detection. Instead of checking only the first column, we now look for any row containing a date pattern (DD/MM/YYYY) and specifically handle multi-bank table variations.


## Issue 7: Partial Data Extraction & Mixed Summary/Table Data
- **Problem:** `parser.py` found only 27 transactions (missing Page 1 and Page 3) and failed to extract descriptions or amounts correctly (returning 0.0).
- [cite_start]**Cause:** 1. Page 1 and Page 3 use different headers ("DATE & TIME" vs "Domestic Transactions"). 
    2. [cite_start]Column alignment: The script looked for amounts in the last column, but sometimes the "Reward Points" column or "PI Indicator" shifted the indexes[cite: 81, 101, 104].
    3. [cite_start]Heuristics: Summary data like "Total Amount Due" is outside the main table and requires targeted text searching[cite: 30, 31].
- **Fix:** Implemented a two-pass parser:
    1. [cite_start]**Summary Pass:** Uses RegEx on the raw text of Page 1 to find specific billing labels[cite: 30, 38, 40].
    2. [cite_start]**Transaction Pass:** Uses a more flexible column-search that prioritizes columns containing decimal numbers for "Amount".

    ## Issue 8: IndexError during Row Parsing
- **Problem:** Script crashed with `IndexError: list index out of range` on HDFC Regalia PDF.
- **Cause:** The parser assumed every row with a date would have at least two columns. Some PDF rows were "broken" or "short," leading to an empty `row[1]` access.
- **Fix:** Added a guard clause `if len(clean_row) < 2: continue` to skip malformed rows and used `clean_row` to ensure all `None` values are handled before indexing.


## Issue 9: Table Extractor Failure on Floating Text
- **Problem:** `extract_tables()` returned 0 rows despite data being visible in the text dump.
- [cite_start]**Cause:** HDFC Regalia PDFs often use "invisible" tables or complex overlapping structures that standard library heuristics fail to detect as structured grids.
- [cite_start]**Fix:** Switched to a "Universal Heuristic Parser" that ignores table structures and instead scans every line of text in the PDF using Regular Expressions to identify dates, amounts, and summary labels[cite: 81, 110].


## Issue 10: Regex Grouping and Multi-Line Summary Extraction
- [cite_start]**Problem:** Summary values (Total Due) returned "Not Found" because labels and values were on different lines or separated by dynamic whitespace. 
- **Fix:** Switched to a `full_text` search across the entire document string rather than line-by-line for summary fields. 
- **Learning:** Context matters. For tables, line-by-line is great; for "floating" summary data, searching the entire page's text stream is more reliable.

## Issue 11: Idempotency and Data Integrity Design
- **Problem:** Frequent re-runs of the parser during development risked duplicating 47+ transactions in the database every time the script was executed.
- **Solution (Idempotency):** 1. Implemented a `UNIQUE` constraint on a `tx_hash` (composite of Date + Description + Amount).
    2. [cite_start]Used `INSERT OR IGNORE` logic in SQL to ensure that even if the same file is processed twice, no duplicate data is created. [cite: 81]
- **Design Decision (Strategy):** Chose a **Hybrid Architecture** for extraction. We use a deterministic RegEx parser for 90% of the work and reserved a `category` column in the schema for future Agentic AI enrichment. This avoids "Design Debt" by planning for AI integration from Day 1.
- **Technical Skill:** Date Normalization. [cite_start]Converted fragmented bank date formats (DD/MM/YYYY and DD Mon, YYYY) into ISO 8601 (YYYY-MM-DD) to ensure chronological sorting and future dashboard compatibility. [cite: 18, 101, 158]

## Strategy: Managing Design Debt
- **Insight:** "Design Debt" occurs when quick fixes (like hardcoding a single bank's format) make it impossible to scale later.
- **Fix:** We moved from a single script to a `config.py` architecture early. This allows us to add any of the 7 credit cards by simply adding a dictionary entry rather than rewriting the code.
- **PM Learning:** Thinking about the "8th card" while building the "1st card" is the difference between a prototype and a product.


## Issue 12: Branch Mismanagement & Context Switching
- **Problem:** Significant project work was accidentally performed on a generic branch (`ai-hub-base`) instead of the dedicated project branch (`feat/statement-sentry-setup`).
- **Solution:** Used `git checkout` and `git merge` to move features to the correct branch, ensuring a clean, logical commit history for the specific "Statement Sentry" feature.
- **PM Learning:** Clean repository hygiene is essential for collaboration. Every major feature should live in its own branch to prevent "code pollution" and simplify the Pull Request (PR) review process.


## Issue 13: Overly Broad GitIgnore Rules
- **Problem:** The `.gitignore` contained a global `**/*.json` rule.
- **Risk:** While it protected secrets, it also prevented legitimate configuration files (like `package.json` or project metadata) from being tracked in the repository.
- **Fix:** Refined the ignore rules to target specific secret filenames (`credentials.json`, `token.json`) while allowing standard JSON files to be staged.
- **PM Learning:** Security is a balance. Over-restricting your environment can lead to "missing file" bugs for other developers, while under-restricting leads to data leaks.

## Issue 14: Decoupling Workspace Changes from Branch Context
- **Problem:** Significant development was performed while the local repository was pointed at an unrelated branch (`ai-hub-base`).
- **Discovery:** Learned that uncommitted changes live in the "Working Directory" and are not tied to a specific branch until the `git commit` command is executed.
- **Fix:** Performed a `git checkout` to the intended project branch before committing, effectively "moving" the uncommitted work to the correct logical path.
- **PM Learning:** Understanding the "Staging Area" prevents accidental code pollution in multi-feature environments. It allows for flexibility if a developer starts working on the wrong branch.


## Issue 15: Checkout Aborted due to .gitignore Conflicts
- **Problem:** Attempting to switch branches resulted in an error stating local changes would be overwritten by checkout.
- **Cause:** Modifications made to `.gitignore` while on the current branch conflicted with the version of the file on the destination branch. Git prevents the switch to avoid data loss.
- **Fix:** Employed the `git stash` command to move uncommitted changes into a temporary storage area, performed the `git checkout`, and then used `git stash pop` to re-apply the changes to the correct branch.
- **PM Learning:** Git Stashing is an essential tool for "Context Switching." It allows a developer to pause work on one feature and move to another without the risk of losing progress or polluting branch histories.


## Issue 16: Merge Conflict during Stash Pop
- **Problem:** Running `git stash pop` resulted in a `CONFLICT (content): Merge conflict in .gitignore`.
- **Cause:** The `.gitignore` file had different, non-trivial changes on the current branch and the stashed state. Git could not automatically determine which lines to prioritize.
- **Fix:** Manually edited the file in VS Code to remove Git conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) and reconciled the differing exclusion rules into a single, clean configuration.
- **PM Learning:** Conflicts are not "errors" but "checkpoints." They ensure that a developer consciously decides which version of the logic survives, preventing accidental data loss or regression.