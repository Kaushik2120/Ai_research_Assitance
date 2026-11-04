from app.services.document_store import list_documents
from app.services.vector_store import collection

# Get valid SQLite document IDs
sqlite_documents = list_documents()

sqlite_ids = {
    document["document_id"]
    for document in sqlite_documents
}

# Get all ChromaDB records
chroma_results = collection.get(
    include=["metadatas"]
)

# Identify orphaned chunk IDs
orphaned_chunk_ids = []

for chunk_id, metadata in zip(
    chroma_results["ids"],
    chroma_results["metadatas"]
):
    if metadata["document_id"] not in sqlite_ids:
        orphaned_chunk_ids.append(chunk_id)

print("Orphaned chunks found:", len(orphaned_chunk_ids))

# Require explicit confirmation
confirmation = input(
    "Type DELETE to permanently remove orphaned vectors: "
)

if confirmation == "DELETE":
    collection.delete(ids=orphaned_chunk_ids)
    print(f"Successfully deleted {len(orphaned_chunk_ids)} orphaned chunks.")
else:
    print("Deletion cancelled.")

print("Remaining ChromaDB chunks:", collection.count())