from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
import hashlib

from app.services.pdf_services import extract_text_from_pdf
from app.services.document_store import (
    save_document,
    list_documents,
    get_document,
    find_document_by_hash,
    delete_document,
)
from app.services.chunking_service import chunk_pages
from app.services.embedding_service import generate_embeddings
from app.services.vector_store import add_chunks, search_chunks,delete_chunks
from app.services.answer_service import generate_answer
from app.services.docx_services import extract_text_from_docx

router = APIRouter(prefix="/papers", tags=["Papers"])

MAX_FILE_SIZE = 20 * 1024 * 1024

class SearchRequest(BaseModel):
        query:str = Field(min_length=1,max_length=2000)
        document_id: str| None = None
        top_k:int = Field(default=5,ge=1,le=10)

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    filename = (file.filename or "").strip().lower()
    
    if not filename.endswith((".pdf", ".docx")):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF or DOCX file.",
    )

    content = await file.read(MAX_FILE_SIZE + 1)
    

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "PDF exceeds the 20 MB limit.")
    
    file_hash = hashlib.sha256(content).hexdigest()
        
    existing_document = find_document_by_hash(file_hash)
        
    if existing_document:
            return{
                **existing_document,
                "total_chunks":None,
                "duplicate":True,
                "message":"this pdf has already been uploaded,",
            }

    try:
        if filename.endswith(".pdf"):
            pages = extract_text_from_pdf(content)
        else:
            pages = extract_text_from_docx(content)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid or unreadable PDF/DOCX file.",
    )

    if not any(page["text"].strip() for page in pages):
        raise HTTPException(
            422,
            "No selectable text found. OCR support is needed for scanned PDFs.",
        )
        

    # 1. Split extracted text into chunks
    chunks = chunk_pages(pages)

    if not chunks:
        raise HTTPException(
            422,
            "No readable text found in the PDF."
        )

    # 2. Generate embeddings
    embeddings = generate_embeddings(
        [chunk["text"] for chunk in chunks]
    )

    # 3. Save document details
    document = save_document(file.filename, 
                             pages,
                             file_hash=file_hash,
                            )

    # 4. Store chunks and embeddings in ChromaDB
    add_chunks(
        document["document_id"],
        chunks,
        embeddings,
    )

    # 5. Return document details
    document["total_chunks"] = len(chunks)

    return document

@router.post("/search")
def search_papers(request: SearchRequest):
    query = request.query.strip()

    if not query:
        raise HTTPException(400, "Search query cannot be empty.")

    query_embedding = generate_embeddings([query])[0]

    results = search_chunks(
        query_embedding=query_embedding,
        n_results=request.top_k,
        document_id=request.document_id,
    )

    matches = []

    if results.get("documents") and results["documents"][0]:
        for i, text in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i]

            matches.append({
                "text": text,
                "document_id": metadata["document_id"],
                "page_number": metadata["page_number"],
                "distance": distance,
            })

    return {
        "query": query,
        "total_results": len(matches),
        "results": matches,
    }


@router.get("/")
def get_all_documents():
    return {"documents": list_documents()}


@router.get("/{document_id}")
def get_document_by_id(document_id: str):
    document = get_document(document_id)

    if document is None:
        raise HTTPException(404, "Document not found.")

    return document

@router.delete("/{document_id}")
def delete_paper(document_id: str):

    # 1. Check whether document exists in SQLite
    document = get_document(document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    # 2. Delete vectors from ChromaDB
    try:
        deleted_chunks = delete_chunks(document_id)

    except Exception as exc:
        print(f"ChromaDB deletion error: {exc}")

        raise HTTPException(
            status_code=500,
            detail="Failed to delete document vectors."
        )

    # 3. Delete document from SQLite
    try:
        deleted = delete_document(document_id)

        if not deleted:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete document metadata."
            )

    except HTTPException:
        raise

    except Exception as exc:
        print(f"SQLite deletion error: {exc}")

        raise HTTPException(
            status_code=500,
            detail="Failed to delete document metadata."
        )

    return {
        "message": "Document deleted successfully.",
        "document_id": document_id,
        "deleted_chunks": deleted_chunks,
    }

class AskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    document_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=10)
    
@router.post("/ask")
def ask_papers(request: AskRequest):
    query = request.query.strip()

    if not query:
        raise HTTPException(400, "Question cannot be empty.")

    query_embedding = generate_embeddings([query])[0]

    results = search_chunks(
        query_embedding=query_embedding,
        n_results=request.top_k,
        document_id=request.document_id,
    )

    passages = []

    if results.get("documents") and results["documents"][0]:
        for i, text in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i]
            passages.append({
                "text": text,
                "document_id": metadata["document_id"],
                "page_number": metadata["page_number"],
            })

    try:
        answer = generate_answer(query, passages)
    except ValueError as exc:
        raise HTTPException(500, str(exc))
    except Exception as exc:
        print(f"Answer generation error: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=502,
            detail="Answer generation failed. Check the backend terminal for details.",
        )
    return {
        "question": query,
        "answer": answer,
        "sources": [
            {
                "document_id": p["document_id"],
                "page_number": p["page_number"],
                "text": p["text"],
            }
            for p in passages
        ],
    }