# AI Hub: Product Requirements Document (PRD)

## 1. Vision & Purpose
To provide a unified, provider-agnostic "AI Cockpit" that grants users full control over the world's most advanced GenAI models (Text, Image, and eventually Video) without the limitations or UI-lock of consumer applications.

## 2. Target User Persona
**The AI Power-User / Developer-in-Training:** Needs a sandbox to compare model logic, test "raw" vs "safe" outputs, and manage specific parameters (Temperature, Tokens) that are usually hidden.

## 3. The Problem
* **Platform Fragmentation:** Users must switch between 4+ tabs (OpenAI, Gemini, Grok, Claude) to compare outputs.
* **Lack of Control:** Consumer UIs often "dumb down" parameters like Temperature or System Prompts.
* **Context Bleed:** Switching models in a single thread often leads to hallucinations or API errors.

## 4. The Solution (Architecture)
* **Frontend:** Streamlit (Python) for rapid, cross-platform UI.
* **Orchestration:** LiteLLM as the "Universal Remote" for API routing.
* **Persistence:** JSON-based local storage (`chat_history.json`) for session recovery.
* **Registry:** `models.yaml` for a decoupled "Model Garden."

## 5. Evolution Log (Version History)
### v1.0: The Unified Chat (MVP)
* Basic text integration with Gemini 2.0.
* Password gate for personal security.

### v1.5: The Multi-Modal Garden
* **Image Studio:** Integrated DALL-E 3, Imagen 3, Grok Imagine, and Hugging Face.
* **Safety Controls:** Implemented a Regex-based "Firewall" and "System Prompt" guardrails.

### v2.0: Multi-Threaded Persistence (Current)
* **Thread Registry:** Moved from single-stream to a multi-chat thread system.
* **Context Isolation:** Threads are "locked" to a provider to prevent cross-model errors.
* **Storage:** Implemented JSON persistence to prevent history loss on restart.

## 6. Feature Roadmap
- [ ] **v2.5: Performance & Streaming:** Implement word-by-word streaming to fix UI latency.
- [ ] **v3.0: Vision & Analysis:** Allow image uploads for "Image-to-Text" analysis.
- [ ] **v4.0: Cost Analytics:** Real-time ₹ tracking per provider.