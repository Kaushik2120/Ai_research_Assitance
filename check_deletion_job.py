from app.services.document_store import get_pending_deletion_jobs

jobs = get_pending_deletion_jobs()

print("Pending deletion jobs:", len(jobs))

for job in jobs:
    print(job)