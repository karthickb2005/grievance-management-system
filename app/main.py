"""
Grievance Router - FastAPI Application Entry Point
Multilingual AI civic complaint triage platform
"""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings
from app.database import engine, Base
from app.api import complaints, issues, geo, alerts

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Grievance Router",
    description="Multilingual AI civic complaint triage platform for Bangalore BBMP",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(complaints.router)
app.include_router(issues.router)
app.include_router(geo.router)
app.include_router(alerts.router)

# Mount static files for frontend (optional)
frontend_path = settings.FRONTEND_DIR
static_path = frontend_path / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Health check
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "model": settings.EMBEDDING_MODEL
    }

# Root endpoint - serve frontend
@app.get("/")
def read_root():
    index_file = frontend_path / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Grievance Router API", "docs": "/docs"}

# Serve frontend pages
@app.get("/command-map")
def command_map():
    return FileResponse(str(frontend_path / "command-map.html"))

@app.get("/portal")
def citizen_portal():
    return FileResponse(str(frontend_path / "portal.html"))

@app.get("/track")
def track_complaint():
    return FileResponse(str(frontend_path / "track.html"))

if __name__ == "__main__":
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║         GRIEVANCE ROUTER - Starting Server                ║
╠═══════════════════════════════════════════════════════════╣
║  API:          http://localhost:{settings.PORT}                       ║
║  Frontend:     http://localhost:{settings.PORT}                       ║
║  Docs:         http://localhost:{settings.PORT}/docs                   ║
║  Environment:  {settings.ENVIRONMENT}                             ║
╚═══════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )
