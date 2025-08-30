from fastapi import FastAPI
app = FastAPI(title="Portfolio Starter API")
@app.get("/health")
def health():
    return {"status": "ok"}
