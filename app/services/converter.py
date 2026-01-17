"""
PDF to Markdown conversion service using Docling.
"""

import logging
import re
from io import BytesIO
from typing import Optional, Tuple

from docling.datamodel.base_models import InputFormat, DocumentStream
from docling.datamodel.pipeline_options import AcceleratorDevice, AcceleratorOptions, PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import ImageRefMode

from app.storage import local

_log = logging.getLogger(__name__)

# Image resolution scale (1.0 = 72 DPI, 2.0 = 144 DPI)
IMAGE_RESOLUTION_SCALE = 2.0


def _get_converter() -> DocumentConverter:
    """Create and configure DocumentConverter with image support."""
    # Force CPU to avoid CUDA compatibility issues
    accelerator_options = AcceleratorOptions(
        num_threads=4,
        device=AcceleratorDevice.CPU,
    )
    
    pipeline_options = PdfPipelineOptions()
    pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
    pipeline_options.generate_page_images = False
    pipeline_options.generate_picture_images = True
    pipeline_options.accelerator_options = accelerator_options
    
    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )


def get_pdf_title(pdf_bytes: bytes) -> Optional[str]:
    """
    Extract title from PDF without full conversion.
    Uses pypdf for fast metadata extraction.
    """
    try:
        import pypdf
        buf = BytesIO(pdf_bytes)
        reader = pypdf.PdfReader(buf)
        metadata = reader.metadata
        if metadata and metadata.title:
            title = metadata.title.strip()
            if title:
                _log.info(f"Extracted PDF title from metadata: {title}")
                return title
        _log.info("No title in PDF metadata")
        return None
    except Exception as e:
        _log.warning(f"Failed to extract PDF title: {e}")
        return None


def get_pdf_hash(pdf_bytes: bytes) -> str:
    """
    Calculate hash of PDF content for cache lookup.
    """
    import hashlib
    return hashlib.sha256(pdf_bytes).hexdigest()[:16]


def convert_pdf_to_markdown(task_id: str, pdf_bytes: bytes) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Convert PDF to Markdown with images.
    
    Args:
        task_id: Unique task identifier
        pdf_bytes: PDF file content as bytes
    
    Returns:
        Tuple of (success, title, error_message)
    """
    try:
        # Create task directory
        task_dir = local.create_task_dir(task_id)
        
        # Convert PDF
        converter = _get_converter()
        buf = BytesIO(pdf_bytes)
        source = DocumentStream(name="document.pdf", stream=buf)
        result = converter.convert(source)
        
        doc = result.document
        title = doc.name if doc.name else "Untitled"
        
        # Export Markdown with referenced images
        # Docling automatically saves images to output_artifacts/ directory
        md_path = task_dir / "output.md"
        doc.save_as_markdown(md_path, image_mode=ImageRefMode.REFERENCED)
        
        # Fix image paths in Markdown to point to our API
        # Docling saves images to output_artifacts/ with absolute paths
        md_content = md_path.read_text(encoding="utf-8")
        
        # Replace absolute paths like /home/.../output_artifacts/image_xxx.png
        # with /api/images/{task_id}/image_xxx.png
        def replace_image_path(match):
            full_path = match.group(1)
            # Extract just the filename
            filename = full_path.split('/')[-1]
            return f'](/api/images/{task_id}/{filename})'
        
        md_content = re.sub(
            r'\]\(([^)]+/output_artifacts/[^)]+)\)',
            replace_image_path,
            md_content
        )
        md_path.write_text(md_content, encoding="utf-8")
        
        _log.info(f"Successfully converted PDF to Markdown: {title}")
        return True, title, None
        
    except Exception as e:
        _log.error(f"Error converting PDF to Markdown: {e}")
        return False, None, str(e)
