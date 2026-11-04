
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.conversation_service import (
    save_message,
    get_conversation_history,
    list_conversations,
    update_conversation_title,
    delete_conversation,
)
from app.services.document_store import get_connection, DB_PATH
from app.services.embedding_service import generate_embeddings
from app.services.vector_store import search_chunks
from app.services.answer_service import generate_answer

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    conversation_id: str
    message: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=10)

class RenameConversationRequest(BaseModel):
    title: str = Field(min_length = 1,max_length=150)
    

def get_conversation_documents(conversation_id: str) -> list[str]:
    """Get all document IDs linked to a conversation."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT document_id
            FROM conversation_documents
            WHERE conversation_id = ?
            """,
            (conversation_id,),
        ).fetchall()

    return [row["document_id"] for row in rows]

@router.get("/")
def get_all_conversations():
    try:
        conversations = list_conversations()

        return {
            "total_conversations": len(conversations),
            "conversations": conversations,
        }

    except Exception as exc:
        print("Conversation listing error:", exc)
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve conversations.",
        )
        
@router.get("/{conversation_id}")
def get_chat_history(conversation_id: str):

    # Check whether conversation exists
    with get_connection() as connection:
        conversation = connection.execute(
            """
            SELECT conversation_id, title, created_at, updated_at
            FROM conversations
            WHERE conversation_id = ?
            """,
            (conversation_id,),
        ).fetchone()

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    # Retrieve all messages
    messages = get_conversation_history(conversation_id)

    return {
        "conversation": dict(conversation),
        "total_messages": len(messages),
        "messages": messages,
    }

@router.patch("/{conversation_id}")
def rename_conversation(
    conversation_id: str,
    request: RenameConversationRequest,
):
    title = request.title.strip()

    if not title:
        raise HTTPException(
            status_code=400,
            detail="Conversation title cannot be empty.",
        )

    updated = update_conversation_title(
        conversation_id,
        title,
    )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    return {
        "message": "Conversation renamed successfully.",
        "conversation_id": conversation_id,
        "title": title,
    }

@router.delete("/{conversation_id}")
def remove_conversation(conversation_id: str):

    deleted = delete_conversation(conversation_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    return {
        "message": "Conversation deleted successfully.",
        "conversation_id": conversation_id,
    }

@router.post("/message")
def send_message(request: ChatRequest):

    message = request.message.strip()
    

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    # Retrieve previous conversation messages
    history = get_conversation_history(request.conversation_id)
    
    # 1. Verify that the conversation exists
    with get_connection() as connection:
        conversation = connection.execute(
            """
            SELECT conversation_id
            FROM conversations
            WHERE conversation_id = ?
            """,
            (request.conversation_id,),
        ).fetchone()

    # Temporary debugging information
    print("\n========== CHAT DEBUG ==========")
    print("Received ID:", repr(request.conversation_id))
    print("Database path:", DB_PATH)
    print("Database exists:", DB_PATH.exists())
    print("Conversation found:", conversation is not None)

    with get_connection() as connection:
        rows = connection.execute(
            "SELECT conversation_id FROM conversations"
        ).fetchall()

    print(
        "Available IDs:",
        [row["conversation_id"] for row in rows],
    )
    print("================================\n")

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    # 2. Find documents linked to this conversation
    document_ids = get_conversation_documents(
        request.conversation_id
    )

    if not document_ids:
        raise HTTPException(
            status_code=400,
            detail="No documents are linked to this conversation.",
        )

    # 3. Generate query embedding and search document
    try:
        query_embedding = generate_embeddings([message])[0]

        # Initially search the first linked document.
        results = search_chunks(
            query_embedding=query_embedding,
            n_results=request.top_k,
            document_id=document_ids[0],
        )

    except Exception as exc:
        print("Document search error:", exc)

        raise HTTPException(
            status_code=500,
            detail="Could not search the uploaded document.",
        )

    # 4. Prepare relevant passages
    passages = []

    if results.get("documents") and results["documents"][0]:
        for i, text in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i]

            passages.append({
                "text": text,
                "document_id": metadata["document_id"],
                "page_number": metadata["page_number"],
            })

    # 5. Save the user's message
    try:
        save_message(
            conversation_id=request.conversation_id,
            role="user",
            content=message,
        )
    except Exception as exc:
        print("User message save error:", exc)
        raise HTTPException(
            status_code=500,
            detail="Could not save your message.",
        )

    # 6. Generate answer using document passages
    try:
        answer = generate_answer(
            question=message,
            passages=passages,
            history=history,
)
    except Exception as exc:
        print("Chat answer generation error:", exc)

        raise HTTPException(
            status_code=502,
            detail="Could not generate an answer.",
        )

    # 7. Prepare source references
    sources = [
        {
            "document_id": passage["document_id"],
            "page_number": passage["page_number"],
            "text": passage["text"],
        }
        for passage in passages
    ]

    # 8. Save assistant response
    try:
        save_message(
            conversation_id=request.conversation_id,
            role="assistant",
            content=answer,
            sources=sources,
        )

    except Exception as exc:
        print("Assistant message save error:", exc)

        raise HTTPException(
            status_code=500,
            detail="Answer generated, but could not save it.",
        )

    # 9. Return response
    return {
        "conversation_id": request.conversation_id,
        "question": message,
        "answer": answer,
        "sources": sources,
    }
