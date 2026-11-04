from app.services.document_deletion_service import (
    delete_document_completely,
)

document_id =  "9ea73eb2-2878-49f8-89f3-71b7e5db6203"

result = delete_document_completely(document_id)

print(result)