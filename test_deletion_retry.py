from app.services.document_store import (
    create_deletion_job,
    get_pending_deletion_jobs,
)

# Dummy ID — not linked to any real document
document_id = "dummy-retry-test-001"

job_id = create_deletion_job(document_id)

print("Test deletion job created!")
print("Job ID:", job_id)

jobs = get_pending_deletion_jobs()

print("\nPending jobs:")

for job in jobs:
    print(job)