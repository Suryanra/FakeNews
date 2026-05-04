from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from contextlib import asynccontextmanager

from models import NewsQuery, AnalysisResponse, SourceDocument, AddNewsRequest
from rag_pipeline import initialize_rag, analyze_news, add_news_to_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize RAG on startup (loads model, builds/loads vector DB)
    print("Initializing RAG pipeline...")
    initialize_rag()
    yield
    print("Shutting down RAG pipeline...")

app = FastAPI(title="Fake News Detection API", lifespan=lifespan)

# Allow CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_endpoint(query: NewsQuery):
    try:
        # Call RAG pipeline
        result = analyze_news(query.text)
        
        # Parse result
        assessment = result.get("result", "Unable to generate assessment.")
        source_docs = result.get("source_documents", [])
        
        sources = []
        for doc in source_docs:
            # Safely extract title and publication info if they exist in metadata
            meta = doc.metadata
            content = doc.page_content[:300] + "..." # Truncate for display
            sources.append(SourceDocument(content=content, metadata=meta))
            
        return AnalysisResponse(assessment=assessment, sources=sources)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/add-news")
async def add_news_endpoint(req: AddNewsRequest):
    try:
        add_news_to_db(req.text, req.title, req.subject)
        return {"status": "success", "message": "News added successfully to the knowledge base"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def health_check():
    return {"status": "Backend is running"}
