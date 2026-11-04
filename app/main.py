import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.papers import router as papers_router
from app.services.document_deletion_service import (
    process_pending_deletion_jobs,
)
from app.api.chat import router as chat_router


async def deletion_retry_worker():
    """Retry unfinished deletion jobs periodically."""

    while True:
        await asyncio.sleep(30)

        try:
            results = await asyncio.to_thread(
                process_pending_deletion_jobs
            )

            if results:
                print("Deletion retry results:", results)

        except Exception as exc:
            print("Background deletion worker error:", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):

    print("Starting AI Research Assistant...")

    # Recover unfinished jobs on startup
    try:
        results = await asyncio.to_thread(
            process_pending_deletion_jobs
        )
        print("Startup deletion recovery:", results)

    except Exception as exc:
        print("Startup recovery failed:", exc)

    # Start periodic background worker
    worker_task = asyncio.create_task(
        deletion_retry_worker()
    )

    yield

    # Stop worker gracefully during shutdown
    worker_task.cancel()

    try:
        await worker_task
    except asyncio.CancelledError:
        print("Deletion retry worker stopped.")

    print("Shutting down AI Research Assistant...")


app = FastAPI(
    title="AI Research Assistance API",
    description="Upload documents and ask questions using AI.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
def root():
    return {
        "message": "AI Assistant Running",
        "status": "healthy",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(papers_router)
app.include_router(chat_router)