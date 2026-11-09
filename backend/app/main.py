from fastapi import FastAPI

from app.api.routes.components import router as components_router
from app.api.routes.lifecycle_events import router as lifecycle_events_router
from app.api.routes.organisations import router as organisations_router

app = FastAPI(
    title="AeroTrace API",
    description="Aircraft Component Lifecycle and Traceability Platform",
    version="0.1.0",
)

app.include_router(components_router)
app.include_router(organisations_router)
app.include_router(lifecycle_events_router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AeroTrace API",
        "version": "0.1.0",
    }
