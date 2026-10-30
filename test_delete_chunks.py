from app.services.vector_store import delete_chunks, collection

document_id = "c79b8238-6f4e-4add-bb3c-33e4c33c4f36"

print("Before deletion:")

before = collection.get(
    where={"document_id": document_id},
    include=[]
)

print("Chunks:", len(before["ids"]))

deleted_count = delete_chunks(document_id)

print("Deleted chunks:", deleted_count)

after = collection.get(
    where={"document_id": document_id},
    include=[]
)

print("After deletion:", len(after["ids"]))