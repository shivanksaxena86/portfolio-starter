
# AI Hub: Master Context (State Sync)
**Last Updated:** 2026-02-07
**Current Version:** v2.0 (Multi-threaded Persistence)

## 1. Project Overview
A unified AI Cockpit using Streamlit and LiteLLM to aggregate OpenAI, Google Gemini, xAI (Grok), and Hugging Face.

## 2. Technical Stack
- **Language:** Python 3.11+
- **Frontend:** Streamlit
- **Orchestration:** LiteLLM (Universal Remote)
- **Environment:** Poetry, Windows 10, .venv
- **Security:** .env (Secrets), Password Gate (UI)

## 3. Core Architecture
- `projects/ai_hub/app.py`: Main UI, Thread Management, and State logic.
- `projects/ai_hub/core/provider_logic.py`: API wrappers for Text (LiteLLM) and Image (Custom + LiteLLM).
- `projects/ai_hub/core/safety.py`: Regex-based prompt firewall.
- `projects/ai_hub/config/models.yaml`: Registry of models and providers.
- `projects/ai_hub/chat_history.json`: Local persistence for conversation threads.

## 4. Current State & Known Hurdles
- **Persistence:** Threads are saved to JSON. Compatibility check prevents cross-provider context errors.
- **Git:** .gitignore is set to exclude `**/token.json`, `.env`, and `chat_history.json`.
- **Latency:** Current synchronous calls cause 20-25s delays.

## 5. Active Roadmap
- **Immediate Next Step:** Implement real-time word-by-word streaming for text responses.
- **Upcoming:** Image-to-Text (Vision) analysis using Grok-3 and Gemini.
- **Upcoming:** Multi-image "In-painting" and editing.

# last session updates
# Stable Features: Multi-threaded Chat, JSON Persistence, Streaming Text, Password Gate, Image Download, Chronological Sorting.
# Fixed Bugs: Cross-model prompt bleeding, navigation lock-up from Archive, Raw model filtering, Boot latency via Deferred Imports.
# Open Issues / Next Actions:
Image Gallery: Images currently disappear on refresh (need to save to assets/ and link in JSON).
Vision Integration: Prepare Gemini-Pro-Vision logic for Phase 3.0.
Multi-Model Comparison: Side-by-side text generation.