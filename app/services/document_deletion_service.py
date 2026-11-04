from app.services.document_store import (
    get_document,
    delete_document,
    create_deletion_job,
    get_pending_deletion_jobs,
    update_deletion_job,
)

from app.services.vector_store import delete_chunks


def process_deletion_job(job: dict) -> dict:
    """
    Process one deletion job.
    Safe to retry if a previous attempt partially succeeded.
    """

    job_id = job["job_id"]
    document_id = job["document_id"]

    try:
        # 1. Delete vectors from ChromaDB
        deleted_chunks = delete_chunks(document_id)

        # 2. Delete SQLite record.
        # It may already be deleted by an earlier attempt.
        delete_document(document_id)

        # 3. Mark job completed
        update_deletion_job(
            job_id,
            status="COMPLETED",
        )

        return {
            "success": True,
            "document_id": document_id,
            "deleted_chunks": deleted_chunks,
        }

    except Exception as exc:
        # Keep the job for another attempt
        update_deletion_job(
            job_id,
            status="FAILED",
            error=str(exc),
        )

        return {
            "success": False,
            "document_id": document_id,
            "error": str(exc),
        }


def process_pending_deletion_jobs() -> list[dict]:
    """
    Process all pending and failed deletion jobs.
    """

    jobs = get_pending_deletion_jobs()

    results = []

    for job in jobs:
        result = process_deletion_job(job)
        results.append(result)

    return results


def delete_document_completely(document_id: str) -> dict:
    """
    Create a persistent deletion job and process it.
    """

    document = get_document(document_id)

    if document is None:
        return {
            "success": False,
            "message": "Document not found.",
        }

    # 1. Persist the job before deleting anything
    job_id = create_deletion_job(document_id)

    # 2. Process the job
    result = process_deletion_job({
        "job_id": job_id,
        "document_id": document_id,
    })

    if not result["success"]:
        return {
            **result,
            "message": "Deletion is pending retry.",
            "job_id": job_id,
        }

    return {
        **result,
        "message": "Document deleted successfully.",
        "job_id": job_id,
    }