from app.services.document_store import list_documents

documents = list_documents()

print("Total documents:", len(documents))

for document in documents:
    print(
        "ID:", document["document_id"],
        "| Filename:", document["filename"]
    )