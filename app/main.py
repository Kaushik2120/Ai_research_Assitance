from fastapi import FastAPI
from app.api.papers import router as papers_router

app = FastAPI(
    title = "Ai Research Assitance API",
    description = "An AI Domain where users can upload their docs/pdfs and ask qns to the AI ",
    version = "1.0.0",
)

@app.get("/")
def root():
    return {
        "message":"Ai Assitant Running",
        "status":"healthy",
    }
    
@app.get("/health")
def health_check():
    return {"status" :"ok"}        
app.include_router(papers_router)