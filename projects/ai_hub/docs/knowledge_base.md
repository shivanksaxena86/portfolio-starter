
# AI Hub: Knowledge Base & Troubleshooting Log

## 1. Environmental & Setup Learnings
### The .env Refresh Trap
* **Problem:** Changes to API keys in `.env` weren't reflecting in the app.
* **Cause:** Streamlit/Python only reads `.env` once at startup.
* **Fix:** Perform a "Hard Restart" (Ctrl+C and re-run `streamlit run`) whenever `.env` or `models.yaml` changes.

## 2. API & Integration Challenges
### Google "Limit 0" Error
* **Problem:** `RateLimitError: limit: 0` for Gemini models.
* **Cause:** New Google Cloud projects often have zero quota for "Pro" models until a Billing Account is linked.
* **Fix:** Linked a credit card to the project; limits instantly moved from 0 to 15 RPM.

### xAI "400 Bad Request" (Image Size)
* **Problem:** Grok Imagine returned 400 errors for 512x512 requests.
* **Cause:** Many 2026 generation models are optimized for 1024x1024 (1:1) or specific aspect ratios.
* **Fix:** Hard-coded the `aspect_ratio: "1:1"` parameter in the backend logic.

### Hugging Face "410 Gone"
* **Problem:** API calls to `api-inference.huggingface.co` failed.
* **Cause:** Endpoint deprecation.
* **Fix:** Updated the logic to use the new 2026 router: `router.huggingface.co`.

## 3. UI & State Management
### The "Goldfish Memory" Bug
* **Problem:** Switching models caused the previous response to disappear.
* **Cause:** Streamlit re-renders from top-to-bottom; if the new model didn't have the history, it vanished.
* **Fix:** Implemented `st.session_state.threads` to separate "Visual History" from "API Context."

### Race Conditions in Rendering
* **Problem:** User prompt appeared but AI response was "invisible" until a second click.
* **Cause:** The script ended before the UI could refresh with the new data.
* **Fix:** Added `st.rerun()` immediately after the AI response is appended to the message list.


## 4. Git & Repository Management
### The "Secret Scanning" Block
* **Problem:** GitHub rejected a push with `remote rejected ... push declined due to repository rule violations`.
* **Cause:** `token.json` was accidentally staged. GitHub detected a Google OAuth secret in the commit history.
* **Fix:** 1. Performed `git reset --soft HEAD~1` to undo the commit while keeping code changes.
    2. Updated `.gitignore` to specifically exclude `**/token.json`.
    3. Used `git reset` on the specific secret file and performed a clean `git add projects/ai_hub/`.
* **Learning:** Always run `git status` before `git commit`. A "Monorepo" requires surgical `git add` commands rather than a blanket `git add .`.

### Pre-commit Hook Failures (Black/Ruff)
* **Problem:** Commit failed because files were modified or linting errors were found.
* **Cause:** Black reformatted code (changing the file state), and Ruff found "Code Smells" (nested `if` statements and unchained exceptions).
* **Fix:** 1. Re-added files after Black's automatic formatting.
    2. Combined nested `if` statements using `and`.
    3. Used `raise ... from e` for better error chaining.

### The "Pre-Commit Catch-22" (Formatting & Linting)
* **Problem:** `git commit` fails with "files were modified by this hook" or "SIM102 Use a single if statement."
* **Cause:** 1. **Black:** It reformats your code to meet standards. Because the file changed *after* you staged it, Git blocks the commit to make sure you approve the changes.
    2. **Ruff (SIM102):** Python best practices suggest "Flat is better than nested." Combining two `if` statements into one using `and` makes the code more readable and efficient.
* **Fix:** 1. Resolve the linting error in the code (combine the `if` statements).
    2. Run `git add .` again to stage the new formatting and fixes.
    3. Run `git commit` again.


A. AI Product Manager Skill: "State vs. Reality"
The Learning: Just because data is in the database (JSON) doesn't mean it's on the screen (UI).

The Problem: We found that navigating tabs destroyed the "Active Input" because Streamlit clears widgets that aren't rendered.

The Solution: Using Session State Redirection. We learned to force the UI back to the specific tab (page_nav) whenever a background change happens.

B. Bug Log: The "Context Ghost"
Problem: Prompts from one chat appearing in another.

Cause: Standardized widget names in a loop.

Technical Fix: Implementation of Dynamic Keys. Every input widget must have a unique identifier (key=f"input_{cid}") to isolate memory.

C. Roadblock: API Latency & Perceived Speed
Problem: 25-second wait for a "Hi" message.

Concept: TTFT (Time To First Token).

Solution: Moved from Synchronous calls to Streaming Response. By using Python Generators and st.empty placeholders, we reduced the perceived wait time from 25s to <2s.