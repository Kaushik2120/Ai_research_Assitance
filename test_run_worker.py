from app.services.document_deletion_service import (
    process_pending_deletion_jobs,
)

results = process_pending_deletion_jobs()

print("Worker results:", results)