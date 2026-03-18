import sqlite3
import json
import os
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "conversations.db"))


def _get_conn():
    """Get a SQLite connection with WAL mode for better concurrent access."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
    logger.info("Database initialized at %s", DB_PATH)


def get_conversation(conv_id):
    """Retrieve a conversation by ID. Returns the parsed data dict or None."""
    with _get_conn() as conn:
        row = conn.execute("SELECT data FROM conversations WHERE id = ?", (conv_id,)).fetchone()
    if row:
        return json.loads(row["data"])
    return None


def save_conversation(conv_id, data):
    """Insert or update a conversation."""
    now = datetime.now(timezone.utc).isoformat()
    data_json = json.dumps(data, default=str)
    with _get_conn() as conn:
        conn.execute("""
            INSERT INTO conversations (id, data, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at
        """, (conv_id, data_json, now, now))
        conn.commit()


def delete_conversation(conv_id):
    """Delete a conversation by ID."""
    with _get_conn() as conn:
        conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        conn.commit()


def conversation_exists(conv_id):
    """Check if a conversation exists."""
    with _get_conn() as conn:
        row = conn.execute("SELECT 1 FROM conversations WHERE id = ?", (conv_id,)).fetchone()
    return row is not None


def cleanup_expired(ttl_hours=24):
    """Delete conversations older than ttl_hours. Returns count of deleted rows."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=ttl_hours)).isoformat()
    with _get_conn() as conn:
        cursor = conn.execute("DELETE FROM conversations WHERE updated_at < ?", (cutoff,))
        conn.commit()
        count = cursor.rowcount
    if count > 0:
        logger.info("Cleaned up %d expired conversations (TTL: %dh)", count, ttl_hours)
    return count
