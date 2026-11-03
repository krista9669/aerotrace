from fastapi import FastAPI

app = FastAPI(
    title="AeroTrace API",
    description="Aircraft Component Lifecycle and Traceability Platform",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AeroTrace API",
        "version": "0.1.0",
    }