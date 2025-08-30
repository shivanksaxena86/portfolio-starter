
# Run inside a cloned repo (PowerShell)
param(
  [string]$PythonExe = "python"
)

Write-Host "==> Creating virtual environment..." -ForegroundColor Cyan
$venvPath = ".venv"
& $PythonExe -m venv $venvPath

if ($IsWindows) {
  $activate = ".\.venv\Scripts\Activate.ps1"
} else {
  $activate = ". .venv/bin/activate"
}

Write-Host "==> Activating venv and installing Poetry deps..." -ForegroundColor Cyan
# PowerShell: dot-source activate
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install poetry pre-commit
poetry install

Write-Host "==> Installing pre-commit hooks..." -ForegroundColor Cyan
pre-commit install

Write-Host "==> Sanity checks (ruff/black/mypy/pytest)..." -ForegroundColor Cyan
poetry run ruff .
poetry run black --check .
poetry run mypy .
poetry run pytest -q

Write-Host "==> Done. To run demos:" -ForegroundColor Green
Write-Host "streamlit run app/streamlit_app.py"
Write-Host "uvicorn fastapi_app.main:app --reload"
