
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