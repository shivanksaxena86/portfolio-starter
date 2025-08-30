# AI/ML Portfolio Starter (with LeetCode + Cert Prep)

A clean, reproducible template to organize:
- **AI/ML/LLM projects** (apps + libs)
- **LeetCode / Algorithms practice** (Python)
- **Certification prep** (DP-600, AI-102, etc.)

## Quickstart
```bash
python -m venv .venv && . .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install poetry
poetry install
pre-commit install

# run checks
ruff . && black --check . && mypy . && pytest -q

# demo apps
streamlit run app/streamlit_app.py
uvicorn fastapi_app.main:app --reload
```
## Structure
- `app/` Streamlit demo app
- `fastapi_app/` Minimal FastAPI service
- `src/portfolio_starter/` Your Python package
- `algorithms/` LeetCode-style problems (Python) with tests
- `certs/` Certification prep notes/templates (DP-600, AI-102)
- `cards/` Model & dataset cards
- `notebooks/` Jupyter notebooks (outputs stripped by pre-commit)
- CI: `.github/workflows/ci.yml` and `.pre-commit-config.yaml`
