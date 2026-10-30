
import sqlite3
import json
from uuid import uuid4
from pathlib import Path

# Store SQLite database inside the backend directory.
DB_PATH = Path(__file__).resolve().parents[2] / "documents.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
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