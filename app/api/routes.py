"""
API routes for PDF conversion service.
"""

import uuid
import asyncio
import logging

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse, PlainTextResponse

from app.models.schemas import (
    ConvertResponse,
    TaskStatusResponse,
    TaskStatus,
)
from app.services import cache
from app.services import converter
from app.storage import local

_log = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["conversion"])


async def _process_conversion(task_id: str, pdf_bytes: bytes, content_hash: str):
    """Background task to convert PDF to Markdown."""
    try:
        await cache.update_task_status(task_id, "processing")
        
        # Run conversion in thread pool (docling is CPU-bound)
        loop = asyncio.get_event_loop()
        success, title, error = await loop.run_in_executor(
            None, converter.convert_pdf_to_markdown, task_id, pdf_bytes
        )
        
        if success:
            title = title or "Untitled"
            await cache.update_task_status(
                task_id, "done", title=title, output_path=str(local.get_task_dir(task_id))
            )
            # Cache by title
            await cache.create_cache(title, "markdown", task_id)
            # Also cache by content hash
            await cache.create_cache(f"hash:{content_hash}", "markdown", task_id)
            _log.info(f"Conversion completed for task {task_id}, title: {title}, hash: {content_hash}")
        else:
            await cache.update_task_status(task_id, "error", error_message=error)
            _log.error(f"Conversion failed for task {task_id}: {error}")
            
    except Exception as e:
        _log.error(f"Error in conversion task {task_id}: {e}")
        await cache.update_task_status(task_id, "error", error_message=str(e))


@router.post("/convert", response_model=ConvertResponse)
async def convert_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Upload and convert a PDF file to Markdown.
    
    If a PDF with the same title or content hash was already converted, returns the cached result.
    Returns a task_id to check conversion status.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    # Read PDF content
    pdf_bytes = await file.read()
    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    
    # Try to get PDF title for cache lookup
    title = converter.get_pdf_title(pdf_bytes)
    _log.info(f"PDF title from metadata: {title}")
    
    # Check cache by title first
    if title:
        cached = await cache.get_cache_by_title(title, "markdown")
        if cached:
            cached_task_id = cached["output_path"]
            if local.task_has_markdown(cached_task_id):
                _log.info(f"Cache hit by title: {title}, task_id: {cached_task_id}")
                return ConvertResponse(
                    task_id=cached_task_id,
                    status=TaskStatus.DONE,
                    message="Found cached conversion result",
                    cached=True,
                )
    
    # Check cache by content hash as fallback
    content_hash = converter.get_pdf_hash(pdf_bytes)
    _log.info(f"PDF content hash: {content_hash}")
    
    cached = await cache.get_cache_by_title(f"hash:{content_hash}", "markdown")
    if cached:
        cached_task_id = cached["output_path"]
        if local.task_has_markdown(cached_task_id):
            _log.info(f"Cache hit by hash: {content_hash}, task_id: {cached_task_id}")
            return ConvertResponse(
                task_id=cached_task_id,
                status=TaskStatus.DONE,
                message="Found cached conversion result",
                cached=True,
            )
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Create task in database
    await cache.create_task(task_id, "markdown")
    
    # Start conversion in background (pass hash for caching)
    background_tasks.add_task(_process_conversion, task_id, pdf_bytes, content_hash)
    
    return ConvertResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        message="Conversion started. Check status with /api/status/{task_id}",
        cached=False,
    )


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get the status of a conversion task."""
    task = await cache.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    markdown_ready = local.task_has_markdown(task_id)
    
    return TaskStatusResponse(
        task_id=task_id,
        status=TaskStatus(task["status"]),
        title=task.get("title"),
        error_message=task.get("error_message"),
        created_at=task.get("created_at"),
        completed_at=task.get("completed_at"),
        markdown_ready=markdown_ready,
    )


@router.get("/markdown/{task_id}", response_class=PlainTextResponse)
async def get_markdown(task_id: str):
    """Get the converted Markdown content."""
    task = await cache.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] != "done":
        raise HTTPException(status_code=400, detail="Conversion not completed")
    
    md_content = local.get_markdown(task_id)
    if not md_content:
        raise HTTPException(status_code=404, detail="Markdown file not found")
    
    return PlainTextResponse(content=md_content, media_type="text/markdown; charset=utf-8")


@router.get("/download/{task_id}")
async def download_markdown(task_id: str):
    """Download markdown and images as a zip file."""
    task = await cache.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if not local.task_has_markdown(task_id):
        raise HTTPException(status_code=400, detail="Markdown not available")
    
    zip_buffer = local.create_markdown_zip(task_id)
    if not zip_buffer:
        raise HTTPException(status_code=500, detail="Failed to create zip file")
    
    title = task.get("title", "document")
    filename = f"{title}.zip"
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/images/{task_id}/{filename}")
async def get_image(task_id: str, filename: str):
    """Serve an image file from the conversion output."""
    image_path = local.get_image_path(task_id, filename)
    if not image_path:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Determine media type based on file extension
    suffix = image_path.suffix.lower()
    media_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
    }
    media_type = media_types.get(suffix, 'image/png')
    
    return FileResponse(image_path, media_type=media_type)
