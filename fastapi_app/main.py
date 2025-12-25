from typing import Any

from fastapi import FastAPI

app = FastAPI(title="Portfolio Starter API")


@app.get("/")
def read_root() -> dict[str, Any]:
    return {"status": "ok"}


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok"}
