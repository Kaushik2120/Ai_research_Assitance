
import chromadb
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "chroma_db"

client = chromadb.PersistentClient(path=str(DB_PATH))

collection = client.get_or_create_collection(
    name="research_documents",
    metadata={"hnsw:space": "cosine"},
)


def add_chunks(
    document_id: str,
    chunks: list[dict],
    embeddings: list[list[float]],
) -> None:
    if len(chunks) != len(embeddings):
        raise ValueError("Chunks and embeddings must have equal lengths")

    if not chunks:
        return

    ids = [
        f"{document_id}_chunk_{i}"
        for i in range(len(chunks))
    ]

    collection.upsert(
        ids=ids,
        documents=[chunk["text"] for chunk in chunks],
        embeddings=embeddings,
        metadatas=[
            {
                "document_id": document_id,
                "page_number": int(chunk["page_number"]),
            }
            for chunk in chunks
        ],
    )


def search_chunks(
    query_embedding: list[float],
    n_results: int = 5,
    document_id: str | None = None,
) -> dict:
    if collection.count() == 0:
        return {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

    where = {"document_id": document_id} if document_id else None

    # Ask for extra candidates so duplicate text can be filtered out.
    candidate_count = min(
        max(n_results * 3, n_results),
        collection.count(),
    )

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=candidate_count,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    # Keep the best-ranked occurrence of each unique text passage.
    unique_results = {
        "ids": [[]],
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]],
    }
    seen_texts = set()

    if results.get("documents") and results["documents"][0]:
        for i, text in enumerate(results["documents"][0]):
            normalized_text = " ".join(text.split()).casefold()

            if normalized_text in seen_texts:
                continue

            seen_texts.add(normalized_text)
            unique_results["ids"][0].append(results["ids"][0][i])
            unique_results["documents"][0].append(text)
            unique_results["metadatas"][0].append(
                results["metadatas"][0][i]
            )
            unique_results["distances"][0].append(
                results["distances"][0][i]
            )

            if len(unique_results["documents"][0]) >= n_results:
                break

    return unique_results

def delete_chunks(document_id: str) -> int:
    """
    Delete all vector chunks belonging to a document.
    Returns the number of chunks deleted.
    """

    results = collection.get(
        where={"document_id": document_id},
        include=[],
    )

    chunk_ids = results.get("ids", [])

    if not chunk_ids:
        return 0

    collection.delete(ids=chunk_ids)

    return len(chunk_ids)
