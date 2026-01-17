"""
FastAPI application entry point for PDF to Markdown converter.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.routes import router as api_router
from app.services.cache import init_db, get_task
from app.storage.local import ensure_storage_dir, task_has_markdown

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
_log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    _log.info("Starting PDF2MD application...")
    await init_db()
    ensure_storage_dir()
    _log.info("Database initialized and storage directory ready")
    
    yield
    
    # Shutdown
    _log.info("Shutting down PDF2MD application...")


app = FastAPI(
    title="PDF2MD",
    description="Convert PDF documents to Markdown using Docling",
    version="0.1.0",
    lifespan=lifespan,
)

# Include API routes
app.include_router(api_router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Serve the upload page."""
    return FileResponse("static/index.html")


@app.get("/view/{task_id}")
async def view_document(task_id: str):
    """Serve the document viewer page for a specific task."""
    # Verify task exists and is complete
    task = await get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if task["status"] != "done":
        raise HTTPException(status_code=400, detail="Document conversion not completed")
    
    if not task_has_markdown(task_id):
        raise HTTPException(status_code=404, detail="Document not found")
    
    return FileResponse("static/viewer.html")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
