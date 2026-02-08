
# Product Requirements Document (PRD): Statement-Sentry

## 1. Vision & Value Proposition
**Statement-Sentry** is a local-first, privacy-centric financial aggregator. It automates the tedious task of collecting credit card statements from multiple banks, decrypting them, and providing a unified dashboard for expense analysis. 

**Value Case:** - **Privacy First:** Sensitive financial data never leaves the user's local machine.
- **Automation:** Eliminates manual login to multiple bank portals.
- **Insights:** Uses GenAI to categorize expenses more accurately than standard banking apps.

## 2. Tech Stack
- **Language:** Python 3.11 (Managed by Poetry)
- **APIs:** Google Gmail API (OAuth2)
- **PDF Processing:** `pikepdf` (Decryption), `pdfplumber` (Extraction)
- **Database:** SQLite (Local relational storage)
- **AI/ML:** Ollama (Local LLM - Llama3/Mistral) for Agentic tagging.
- **Frontend:** Streamlit

## 3. System Architecture
1. **Collector:** Gmail API fetches emails based on pre-defined search queries.
2. **Vault:** Local storage for raw (encrypted) and processed (decrypted) PDFs.
3. **Processor:** Python scripts to unlock PDFs and convert tabular data to structured JSON/SQL.
4. **Insights Engine:** Local LLM categorizes transactions into broad/sub-categories.
5. **Dashboard:** Streamlit UI for filtering, aggregation, and visualization.

## 4. Product Roadmap
### Phase 1: The Collector (Current)
- [x] Gmail API Integration & OAuth Handshake.
- [x] Multi-bank search query configuration.
- [x] Automated download of PDF attachments.
- [x] Text extraction for non-PDF statements (OneCard).

### Phase 2: The Parser & Vault
- [ ] Automated PDF decryption using card-specific password logic.
- [ ] Table extraction from PDFs to SQLite database.
- [ ] Security Scrubbing: Masking PII (Personal Identifiable Information) in logs.

### Phase 3: GenAI & Agentic Workflows
- [ ] Integration with Ollama for local transaction tagging.
- [ ] "Agentic" reconciliation: AI asks user for clarification on unknown merchants.
- [ ] Rewards/Points tracking module.

### Phase 4: Visualization
- [ ] Streamlit Dashboard with date range, card, and category filters.
- [ ] Export to Excel/PowerBI functionality.