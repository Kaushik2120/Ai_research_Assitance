
import sqlite3
import json
from uuid import uuid4
from pathlib import Path

# Store SQLite database inside the backend directory.
DB_PATH = Path(__file__).resolve().parents[2] / "documents.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    with get_connection() as connection:

        # Documents table
        connection.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_hash TEXT UNIQUE,
                total_pages INTEGER NOT NULL,
                total_characters INTEGER NOT NULL,
                pages TEXT NOT NULL
            )
        """)

        # Deletion jobs table
        connection.execute("""
            CREATE TABLE IF NOT EXISTS deletion_jobs (
                job_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING',
                attempts INTEGER NOT NULL DEFAULT 0,
                last_error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
                # Conversations table
        connection.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                title TEXT NOT NULL DEFAULT 'New Chat',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Messages table
        connection.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                sources TEXT,
                created_at TEXT NOT NULL,

                FOREIGN KEY (conversation_id)
                REFERENCES conversations(conversation_id)
                ON DELETE CASCADE
            )
        """)

        # Link conversations with uploaded documents
        connection.execute("""
            CREATE TABLE IF NOT EXISTS conversation_documents (
                conversation_id TEXT NOT NULL,
                document_id TEXT NOT NULL,

                PRIMARY KEY (conversation_id, document_id),

                FOREIGN KEY (conversation_id)
                REFERENCES conversations(conversation_id)
                ON DELETE CASCADE,

                FOREIGN KEY (document_id)
                REFERENCES documents(document_id)
                ON DELETE CASCADE
            )
        """)

        # Index for faster conversation history retrieval
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation
            ON messages(conversation_id, created_at)
        """)


# Create the table when this module is imported.
initialize_database()


def save_document(
    filename: str,
    pages: list[dict],
    file_hash: str | None = None,
) -> dict:

    document_id = str(uuid4())

    document = {
        "document_id": document_id,
        "filename": filename,
        "file_hash": file_hash,
        "total_pages": len(pages),
        "total_characters": sum(
            len(page.get("text", "")) for page in pages
        ),
        "pages": pages,
    }

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO documents (
                document_id,
                filename,
                file_hash,
                total_pages,
                total_characters,
                pages
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                filename,
                file_hash,
                document["total_pages"],
                document["total_characters"],
                json.dumps(pages),
            ),
        )

    return document


def find_document_by_hash(file_hash: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM documents WHERE file_hash = ?",
            (file_hash,),
        ).fetchone()

    if row is None:
        return None

    document = dict(row)
    document["pages"] = json.loads(document["pages"])
    return document


def list_documents() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT
                document_id,
                filename,
                total_pages,
                total_characters
            FROM documents
            ORDER BY rowid DESC
        """).fetchall()

    return [dict(row) for row in rows]


def get_document(document_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM documents WHERE document_id = ?",
            (document_id,),
        ).fetchone()

    if row is None:
        return None

    document = dict(row)
    document["pages"] = json.loads(document["pages"])
    return document

def delete_document(document_id: str) -> bool:
    """
    Delete a document and its extracted pages from SQLite.
    Returns True if the document existed and was deleted.
    """

    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM documents WHERE document_id = ?",
            (document_id,),
        )

        return cursor.rowcount > 0

from datetime import datetime, timezone


def create_deletion_job(document_id: str) -> str:
    job_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO deletion_jobs (
                job_id,
                document_id,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, 'PENDING', ?, ?)
            """,
            (job_id, document_id, now, now),
        )

    return job_id


def get_pending_deletion_jobs() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM deletion_jobs
            WHERE status IN ('PENDING', 'FAILED')
            ORDER BY created_at ASC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def update_deletion_job(
    job_id: str,
    status: str,
    error: str | None = None,
) -> None:

    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE deletion_jobs
            SET
                status = ?,
                attempts = attempts + 1,
                last_error = ?,
                updated_at = ?
            WHERE job_id = ?
            """,
            (status, error, now, job_id),
        )