import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import aiosqlite
from app.core.config import SETTINGS

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parents[4] / "data" / "his_rag.db"

# 覆盖配置文件中的路径（如果存在）
config_db_path = SETTINGS.get("database", {}).get("sqlite_path")
if config_db_path:
    DB_PATH = (Path(__file__).resolve().parents[3] / config_db_path).resolve()


async def init_db():
    """初始化 SQLite 数据库和表结构"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id   TEXT PRIMARY KEY,
                title        TEXT NOT NULL DEFAULT '',
                created_at   TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                message_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id   TEXT NOT NULL REFERENCES sessions(session_id),
                role         TEXT NOT NULL,
                content      TEXT NOT NULL,
                metadata     TEXT DEFAULT '{}',
                created_at   TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
            """
        )
        await db.commit()
    logger.info(f"Database initialized at {DB_PATH}")


async def create_session(session_id: str, title: str = "") -> None:
    """创建新会话"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO sessions (session_id, title) VALUES (?, ?)",
            (session_id, title),
        )
        await db.commit()


async def add_message(
    session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None
) -> None:
    """添加一条消息"""
    meta_str = json.dumps(metadata or {}, ensure_ascii=False)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (session_id, role, content, metadata) VALUES (?, ?, ?, ?)",
            (session_id, role, content, meta_str),
        )
        # 如果是该会话的第一条用户消息，用作会话标题
        if role == "user":
            cursor = await db.execute(
                "SELECT COUNT(*) FROM messages WHERE session_id = ? AND role = 'user'",
                (session_id,),
            )
            row = await cursor.fetchone()
            if row and row[0] == 1:
                title = content[:30] + ("..." if len(content) > 30 else "")
                await db.execute(
                    "UPDATE sessions SET title = ? WHERE session_id = ?",
                    (title, session_id),
                )
        await db.commit()


async def list_sessions() -> List[Dict[str, Any]]:
    """列出所有会话（按时间倒序）"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT session_id, title, created_at FROM sessions ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def list_messages(session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """列出指定会话的消息"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT role, content, metadata, created_at FROM messages WHERE session_id = ? ORDER BY message_id ASC LIMIT ?",
            (session_id, limit),
        )
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            msg = dict(row)
            msg["metadata"] = json.loads(msg["metadata"])
            result.append(msg)
        return result


async def delete_session(session_id: str) -> None:
    """删除指定会话及其所有消息"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        await db.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        await db.commit()
