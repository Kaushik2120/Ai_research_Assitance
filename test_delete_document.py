from app.services.document_store import (
    get_document,
    delete_document,
)

document_id = "3ae792de-0135-4580-b8b7-8fb69e9490ae"

print("Before deletion:", get_document(document_id) is not None)

deleted = delete_document(document_id)

print("Deleted:", deleted)

print("After deletion:", get_document(document_id) is not None)