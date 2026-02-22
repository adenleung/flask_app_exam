import hashlib
import sqlite3
from datetime import datetime
from typing import Optional

# Schema
def init_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            avatar TEXT NOT NULL,
            location TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            sender TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL,
            edited_at TEXT,
            is_deleted INTEGER NOT NULL DEFAULT 0,
            deleted_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS profanities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL UNIQUE,
            level TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT NOT NULL UNIQUE,
            report_type TEXT NOT NULL,
            reporter TEXT NOT NULL,
            status TEXT NOT NULL,
            summary TEXT,
            user_a TEXT,
            user_b TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_matches_match_id ON matches(match_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_profanities_level ON profanities(level)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status)"
    )
    ensure_column(conn, "reports", "user_a", "TEXT")
    ensure_column(conn, "reports", "user_b", "TEXT")
    conn.commit()
    conn.close()

# Add column
def ensure_column(conn: sqlite3.Connection, table: str, column: str, column_type: str) -> None:
    columns = [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")

# DB connect
def connect_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Timestamp
def utc_now_iso() -> str:
    return datetime.utcnow().isoformat()

# Password hash
def hash_password(raw_password: str) -> str:
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()

# Users
def create_user(
    conn: sqlite3.Connection,
    name: str,
    email: str,
    password_hash: str,
    role: str,
    is_admin: bool,
):
    conn.execute(
        """
        INSERT INTO users (name, email, password_hash, role, is_admin, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name, email, password_hash, role, 1 if is_admin else 0, utc_now_iso()),
    )
    conn.commit()
    return conn.execute(
        """
        SELECT id, name, email, role, is_admin, created_at
        FROM users
        WHERE id = last_insert_rowid()
        """
    ).fetchone()

# Email lookup
def get_user_by_email(conn: sqlite3.Connection, email: str):
    return conn.execute(
        """
        SELECT id, name, email, password_hash, role, is_admin, created_at
        FROM users
        WHERE email = ?
        """,
        (email,),
    ).fetchone()

# ID lookup
def get_user_by_id(conn: sqlite3.Connection, user_id: int):
    return conn.execute(
        """
        SELECT id, name, email, role, is_admin, created_at
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    ).fetchone()

# Matches
def list_matches(conn: sqlite3.Connection):
    return conn.execute(
        """
        SELECT match_id, name, avatar, location, created_at
        FROM matches
        ORDER BY created_at DESC
        """
    ).fetchall()

def get_match(conn: sqlite3.Connection, match_id: str):
    return conn.execute(
        """
        SELECT match_id, name, avatar, location, created_at
        FROM matches
        WHERE match_id = ?
        """,
        (match_id,),
    ).fetchone()

def create_match(
    conn: sqlite3.Connection,
    match_id: str,
    name: str,
    avatar: str,
    location: Optional[str],
):
    conn.execute(
        """
        INSERT INTO matches (match_id, name, avatar, location, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (match_id, name, avatar, location, utc_now_iso()),
    )
    conn.commit()
    return get_match(conn, match_id)

# Delete match
def delete_match(conn: sqlite3.Connection, match_id: str) -> None:
    conn.execute("DELETE FROM messages WHERE chat_id = ?", (match_id,))
    conn.execute("DELETE FROM matches WHERE match_id = ?", (match_id,))
    conn.commit()

# Clear matches
def clear_matches(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM messages")
    conn.execute("DELETE FROM matches")
    conn.commit()

# Messages
def list_messages(conn: sqlite3.Connection, chat_id: str):
    return conn.execute(
        """
        SELECT id, chat_id, sender, text, created_at, edited_at, is_deleted, deleted_at
        FROM messages
        WHERE chat_id = ?
        ORDER BY created_at ASC
        """,
        (chat_id,),
    ).fetchall()

def get_message(conn: sqlite3.Connection, message_id: int):
    return conn.execute(
        """
        SELECT id, chat_id, sender, text, created_at, edited_at, is_deleted, deleted_at
        FROM messages
        WHERE id = ?
        """,
        (message_id,),
    ).fetchone()

def create_message(conn: sqlite3.Connection, chat_id: str, sender: str, text: str):
    conn.execute(
        """
        INSERT INTO messages (chat_id, sender, text, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (chat_id, sender, text, utc_now_iso()),
    )
    conn.commit()
    return conn.execute(
        """
        SELECT id, chat_id, sender, text, created_at, edited_at, is_deleted, deleted_at
        FROM messages
        WHERE id = last_insert_rowid()
        """
    ).fetchone()

# Edit message
def update_message_text(conn: sqlite3.Connection, message_id: int, text: str):
    conn.execute(
        "UPDATE messages SET text = ?, edited_at = ? WHERE id = ?",
        (text, utc_now_iso(), message_id),
    )
    conn.commit()
    return get_message(conn, message_id)

# Soft delete
def delete_message(conn: sqlite3.Connection, message_id: int):
    conn.execute(
        "UPDATE messages SET is_deleted = 1, deleted_at = ? WHERE id = ?",
        (utc_now_iso(), message_id),
    )
    conn.commit()
    return get_message(conn, message_id)

# Restore
def restore_message(conn: sqlite3.Connection, message_id: int):
    conn.execute(
        "UPDATE messages SET is_deleted = 0, deleted_at = NULL WHERE id = ?",
        (message_id,),
    )
    conn.commit()
    return get_message(conn, message_id)

# Profanities
def list_profanities(conn: sqlite3.Connection, level: Optional[str] = None):
    if level:
        return conn.execute(
            """
            SELECT id, word, level, created_at, updated_at
            FROM profanities
            WHERE level = ?
            ORDER BY word ASC
            """,
            (level,),
        ).fetchall()
    return conn.execute(
        """
        SELECT id, word, level, created_at, updated_at
        FROM profanities
        ORDER BY word ASC
        """
    ).fetchall()

def get_profanity(conn: sqlite3.Connection, profanity_id: int):
    return conn.execute(
        """
        SELECT id, word, level, created_at, updated_at
        FROM profanities
        WHERE id = ?
        """,
        (profanity_id,),
    ).fetchone()

def create_profanity(conn: sqlite3.Connection, word: str, level: str):
    conn.execute(
        """
        INSERT INTO profanities (word, level, created_at)
        VALUES (?, ?, ?)
        """,
        (word, level, utc_now_iso()),
    )
    conn.commit()
    return conn.execute(
        """
        SELECT id, word, level, created_at, updated_at
        FROM profanities
        WHERE id = last_insert_rowid()
        """
    ).fetchone()

def update_profanity(conn: sqlite3.Connection, profanity_id: int, word: str, level: str):
    conn.execute(
        """
        UPDATE profanities
        SET word = ?, level = ?, updated_at = ?
        WHERE id = ?
        """,
        (word, level, utc_now_iso(), profanity_id),
    )
    conn.commit()
    return get_profanity(conn, profanity_id)

def delete_profanity(conn: sqlite3.Connection, profanity_id: int) -> None:
    conn.execute("DELETE FROM profanities WHERE id = ?", (profanity_id,))
    conn.commit()

# Reports
def list_reports(conn: sqlite3.Connection, status: str | None = None):
    if status:
        return conn.execute(
            """
            SELECT id, case_id, report_type, reporter, status, summary, user_a, user_b, created_at, updated_at
            FROM reports
            WHERE status = ?
            ORDER BY created_at DESC
            """,
            (status,),
        ).fetchall()
    return conn.execute(
        """
        SELECT id, case_id, report_type, reporter, status, summary, user_a, user_b, created_at, updated_at
        FROM reports
        ORDER BY created_at DESC
        """
    ).fetchall()

def get_report(conn: sqlite3.Connection, report_id: int):
    return conn.execute(
        """
        SELECT id, case_id, report_type, reporter, status, summary, user_a, user_b, created_at, updated_at
        FROM reports
        WHERE id = ?
        """,
        (report_id,),
    ).fetchone()

def create_report(
    conn: sqlite3.Connection,
    case_id: str,
    report_type: str,
    reporter: str,
    status: str,
    summary: Optional[str],
    user_a: Optional[str] = None,
    user_b: Optional[str] = None,
):
    conn.execute(
        """
        INSERT INTO reports (case_id, report_type, reporter, status, summary, user_a, user_b, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (case_id, report_type, reporter, status, summary, user_a, user_b, utc_now_iso()),
    )
    conn.commit()
    return conn.execute(
        """
        SELECT id, case_id, report_type, reporter, status, summary, user_a, user_b, created_at, updated_at
        FROM reports
        WHERE id = last_insert_rowid()
        """
    ).fetchone()

# Partial update
def update_report(
    conn: sqlite3.Connection,
    report_id: int,
    status: Optional[str] = None,
    summary: Optional[str] = None,
    user_a: Optional[str] = None,
    user_b: Optional[str] = None,
):
    existing = get_report(conn, report_id)
    if not existing:
        return None
    new_status = status if status is not None else existing["status"]
    new_summary = summary if summary is not None else existing["summary"]
    new_user_a = user_a if user_a is not None else existing["user_a"]
    new_user_b = user_b if user_b is not None else existing["user_b"]
    conn.execute(
        """
        UPDATE reports
        SET status = ?, summary = ?, user_a = ?, user_b = ?, updated_at = ?
        WHERE id = ?
        """,
        (new_status, new_summary, new_user_a, new_user_b, utc_now_iso(), report_id),
    )
    conn.commit()
    return get_report(conn, report_id)

def delete_report(conn: sqlite3.Connection, report_id: int) -> None:
    conn.execute("DELETE FROM reports WHERE id = ?", (report_id,))
    conn.commit()
