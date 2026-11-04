import sqlite3
from app.services.document_store import DB_PATH

job_id = "291c1d16-dbe7-44f5-8615-21cb46e083ef"

with sqlite3.connect(DB_PATH) as conn:
    result = conn.execute(
        """
        SELECT job_id, document_id, status, attempts, last_error
        FROM deletion_jobs
        WHERE job_id = ?
        """,
        (job_id,)
    ).fetchone()

print(result)