import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.analysis import router as analysis_router

app = FastAPI(
    title="Nyayalay API",
    version="0.1.0",
    description="API layer for the Nyayalay legal-information assistant.",
)

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")


@app.get("/")
def root():
    return {"name": "Nyayalay API", "status": "running"}
