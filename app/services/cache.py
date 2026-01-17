"""
Database service for caching conversion results and managing tasks.
Uses SQLite with aiosqlite for async operations.
"""

import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import Optional

DATABASE_PATH = Path(__file__).parent.parent.parent / "cache.db"


async def init_db() -> None:
    """Initialize database tables."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Cache table - stores completed conversions by title
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                format TEXT NOT NULL,
                output_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(title, format)
            )
        """)
        
        # Tasks table - stores conversion task status
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'pending',
                format TEXT NOT NULL,
                title TEXT,
                output_path TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        
        await db.commit()


# ============== Cache Operations ==============

async def get_cache_by_title(title: str, format: str) -> Optional[dict]:
    """Get cached conversion result by PDF title and format."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM cache WHERE title = ? AND format = ?",
            (title, format)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None


async def create_cache(title: str, format: str, output_path: str) -> int:
    """Create a cache entry for a conversion result."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            INSERT OR REPLACE INTO cache (title, format, output_path, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (title, format, output_path, datetime.now())
        )
        await db.commit()
        return cursor.lastrowid


# ============== Task Operations ==============

async def create_task(task_id: str, format: str) -> None:
    """Create a new conversion task."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            INSERT INTO tasks (id, status, format, created_at)
            VALUES (?, 'pending', ?, ?)
            """,
            (task_id, format, datetime.now())
        )
        await db.commit()


async def get_task(task_id: str) -> Optional[dict]:
    """Get task by ID."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None


async def update_task_status(
    task_id: str,
    status: str,
    title: Optional[str] = None,
    output_path: Optional[str] = None,
    error_message: Optional[str] = None
) -> None:
    """Update task status and related fields."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        if status in ("done", "error"):
            await db.execute(
                """
                UPDATE tasks
                SET status = ?, title = ?, output_path = ?, error_message = ?, completed_at = ?
                WHERE id = ?
                """,
                (status, title, output_path, error_message, datetime.now(), task_id)
            )
        else:
            await db.execute(
                """
                UPDATE tasks
                SET status = ?, title = ?
                WHERE id = ?
                """,
                (status, title, task_id)
            )
        await db.commit()


async def delete_old_tasks(days: int = 7) -> int:
    """Delete tasks older than specified days."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            DELETE FROM tasks
            WHERE created_at < datetime('now', ? || ' days')
            """,
            (f"-{days}",)
        )
        await db.commit()
        return cursor.rowcount
