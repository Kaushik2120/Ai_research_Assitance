
import json
from uuid import uuid4
from datetime import datetime, timezone

from app.services.document_store import get_connection


def get_current_time():
    return datetime.now(timezone.utc).isoformat()


# 1. Create a new conversation
def create_conversation(title: str = "New Chat") -> dict:

    conversation_id = str(uuid4())
    now = get_current_time()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO conversations (
                conversation_id,
                title,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (conversation_id, title, now, now),
        )

    return {
        "conversation_id": conversation_id,
        "title": title,
        "created_at": now,
        "updated_at": now,
    }


# 2. Save a user or assistant message
def save_message(
    conversation_id: str,
    role: str,
    content: str,
    sources: list[dict] | None = None,
) -> dict:

    if role not in ("user", "assistant"):
        raise ValueError("Role must be user or assistant.")

    message_id = str(uuid4())
    now = get_current_time()

    with get_connection() as connection:

        # Check whether conversation exists
        conversation = connection.execute(
            """
            SELECT conversation_id
            FROM conversations
            WHERE conversation_id = ?
            """,
            (conversation_id,),
        ).fetchone()

        if conversation is None:
            raise ValueError("Conversation not found.")

        connection.execute(
            """
            INSERT INTO messages (
                message_id,
                conversation_id,
                role,
                content,
                sources,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                conversation_id,
                role,
                content,
                json.dumps(sources) if sources is not None else None,
                now,
            ),
        )

        connection.execute(
            """
            UPDATE conversations
            SET updated_at = ?
            WHERE conversation_id = ?
            """,
            (now, conversation_id),
        )

    return {
        "message_id": message_id,
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "sources": sources,
        "created_at": now,
    }


# 3. Retrieve conversation history
def get_conversation_history(
    conversation_id: str,
) -> list[dict]:

    with get_connection() as connection:

        rows = connection.execute(
            """
            SELECT *
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC, rowid ASC
            """,
            (conversation_id,),
        ).fetchall()

    messages = []

    for row in rows:
        message = dict(row)

        message["sources"] = (
            json.loads(message["sources"])
            if message["sources"]
            else []
        )

        messages.append(message)

    return messages


# 4. List all conversations
def list_conversations() -> list[dict]:

    with get_connection() as connection:

        rows = connection.execute(
            """
            SELECT
                c.conversation_id,
                c.title,
                c.created_at,
                c.updated_at,
                COUNT(m.message_id) AS message_count
            FROM conversations c
            LEFT JOIN messages m
                ON c.conversation_id = m.conversation_id
            GROUP BY c.conversation_id
            ORDER BY c.updated_at DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


# 5. Rename a conversation
def update_conversation_title(
    conversation_id: str,
    title: str,
) -> bool:

    now = get_current_time()

    with get_connection() as connection:

        cursor = connection.execute(
            """
            UPDATE conversations
            SET title = ?, updated_at = ?
            WHERE conversation_id = ?
            """,
            (title, now, conversation_id),
        )

        return cursor.rowcount > 0


# 6. Link an uploaded document to a conversation
def link_document_to_conversation(
    conversation_id: str,
    document_id: str,
) -> None:

    with get_connection() as connection:

        connection.execute(
            """
            INSERT OR IGNORE INTO conversation_documents (
                conversation_id,
                document_id
            )
            VALUES (?, ?)
            """,
            (conversation_id, document_id),
        )

def delete_conversation(conversation_id: str) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM conversations
            WHERE conversation_id = ?
            """,
            (conversation_id,),
        )

        return cursor.rowcount > 0