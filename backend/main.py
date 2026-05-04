from pathlib import Path

from dotenv import load_dotenv

# Load env before RAG: optional repo .env, then backend/.env (override wins for local dev)
_backend_dir = Path(__file__).resolve().parent
load_dotenv(_backend_dir.parent / ".env")
load_dotenv(_backend_dir / ".env", override=True)

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from contextlib import asynccontextmanager

from models import NewsQuery, AnalysisResponse, SourceDocument, AddNewsRequest, LoginRequest
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
        
        # Parse result (key name varies by LangChain version: "result" vs "answer")
        assessment = result.get("result") or result.get("answer")
        if not assessment:
            assessment = "Unable to generate assessment."
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

# Hardcoded admin credentials for simple auth
ADMIN_USERNAME = "surya@123"
ADMIN_PASSWORD = "12345"
ADMIN_TOKEN = "admin-secret-token"

def verify_token(authorization: str = Header(None)):
    if not authorization or authorization != f"Bearer {ADMIN_TOKEN}":
        raise HTTPException(status_code=401, detail="Invalid or missing authentication token")
    return authorization

@app.post("/api/login")
async def login(req: LoginRequest):
    if req.username == ADMIN_USERNAME and req.password == ADMIN_PASSWORD:
        return {"status": "success", "token": ADMIN_TOKEN}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")

@app.post("/api/add-news")
async def add_news_endpoint(req: AddNewsRequest, token: str = Depends(verify_token)):
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
