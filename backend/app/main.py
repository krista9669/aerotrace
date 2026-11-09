from fastapi import FastAPI

from app.api.routes.components import router as components_router

app = FastAPI(
    title="AeroTrace API",
    description="Aircraft Component Lifecycle and Traceability Platform",
    version="0.1.0",
)

app.include_router(components_router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AeroTrace API",
        "version": "0.1.0",
    }
