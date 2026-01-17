"""
Pydantic schemas for API request/response models.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class TaskStatus(str, Enum):
    """Task status states."""
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class ConvertResponse(BaseModel):
    """Response model for conversion endpoint."""
    task_id: str
    status: TaskStatus
    message: str
    cached: bool = False


class TaskStatusResponse(BaseModel):
    """Response model for task status endpoint."""
    task_id: str
    status: TaskStatus
    title: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    markdown_ready: bool = False
