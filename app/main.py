"""FastAPI application and startup/shutdown handlers."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.models import Base, engine
from app.config import settings

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Web Crawler with OpenSearch Indexing",
    description="Production-grade web crawler with UI for sitemap/PDF/DOCX indexing",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create storage directories
os.makedirs(settings.STORAGE_PATH, exist_ok=True)
os.makedirs(settings.COLLECTIONS_PATH, exist_ok=True)
os.makedirs(settings.LOGS_PATH, exist_ok=True)

# Import routes
from app.routes import auth, crawlers, jobs, search, admin

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(crawlers.router, prefix="/api/crawlers", tags=["crawlers"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'public')
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Web Crawler API",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info"
    )
