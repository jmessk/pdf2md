"""
Local file storage service for converted documents and images.
"""

import shutil
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Optional

STORAGE_DIR = Path(__file__).parent.parent.parent / "storage" / "output"


def ensure_storage_dir() -> None:
    """Ensure storage directory exists."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def get_task_dir(task_id: str) -> Path:
    """Get the directory for a specific task."""
    return STORAGE_DIR / task_id


def create_task_dir(task_id: str) -> Path:
    """Create a directory for a task and return its path."""
    task_dir = get_task_dir(task_id)
    task_dir.mkdir(parents=True, exist_ok=True)
    return task_dir


def save_markdown(task_id: str, content: str) -> Path:
    """Save Markdown content to task directory."""
    task_dir = get_task_dir(task_id)
    md_path = task_dir / "output.md"
    md_path.write_text(content, encoding="utf-8")
    return md_path


def get_markdown(task_id: str) -> Optional[str]:
    """Get Markdown content for a task."""
    md_path = get_task_dir(task_id) / "output.md"
    if md_path.exists():
        return md_path.read_text(encoding="utf-8")
    return None


def get_image_path(task_id: str, filename: str) -> Optional[Path]:
    """Get path to an image file.
    
    Images are stored in 'output_artifacts/' directory by Docling.
    """
    task_dir = get_task_dir(task_id)
    
    # Docling saves images to output_artifacts/
    image_path = task_dir / "output_artifacts" / filename
    if image_path.exists():
        return image_path
    
    return None


def create_markdown_zip(task_id: str) -> Optional[BytesIO]:
    """Create a zip file containing Markdown and images."""
    task_dir = get_task_dir(task_id)
    md_path = task_dir / "output.md"
    
    if not md_path.exists():
        return None
    
    # Read markdown and fix image paths for local use
    md_content = md_path.read_text(encoding="utf-8")
    # Replace API paths with local paths for the zip
    import re
    md_content = re.sub(
        r'!\[([^\]]*)\]\(/api/images/[^/]+/([^)]+)\)',
        r'![\1](images/\2)',
        md_content
    )
    
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add markdown file with fixed paths
        zf.writestr("output.md", md_content)
        
        # Add images from output_artifacts (where Docling saves them)
        artifacts_dir = task_dir / "output_artifacts"
        if artifacts_dir.exists():
            for image_file in artifacts_dir.iterdir():
                if image_file.is_file() and image_file.suffix.lower() in ('.png', '.jpg', '.jpeg', '.gif', '.webp'):
                    zf.write(image_file, f"images/{image_file.name}")
    
    zip_buffer.seek(0)
    return zip_buffer


def delete_task_files(task_id: str) -> bool:
    """Delete all files for a task."""
    task_dir = get_task_dir(task_id)
    if task_dir.exists():
        shutil.rmtree(task_dir)
        return True
    return False


def task_has_markdown(task_id: str) -> bool:
    """Check if markdown file exists for a task."""
    md_path = get_task_dir(task_id) / "output.md"
    return md_path.exists()
