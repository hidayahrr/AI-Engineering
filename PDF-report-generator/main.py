from fastapi import FastAPI

app = FastAPI(title="PDF Report Generator")


@app.get("/health")
def health_check():
    """Health check endpoint to verify server status."""
    return {"status": "ok"}