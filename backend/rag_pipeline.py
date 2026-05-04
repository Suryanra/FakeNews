import os
from pathlib import Path

from dotenv import load_dotenv

import pandas as pd
from langchain_community.document_loaders import DataFrameLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain_community.llms import Ollama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_classic.chains import RetrievalQA

# Configuration
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
# Optional repo-root .env, then backend/.env (override so GEMINI_API_KEY in .env wins over a bad system GOOGLE_API_KEY)
load_dotenv(Path(_BACKEND_DIR).parent / ".env")
load_dotenv(Path(_BACKEND_DIR) / ".env", override=True)
CHROMA_DB_DIR = os.path.join(_BACKEND_DIR, "chroma_db")
DATASET_PATH = os.path.join(_BACKEND_DIR, "..", "Dataset", "News _dataset", "True.csv")

# Initialize Embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Initialize LLM via Ollama
# Ensure Ollama is running and has llama3 installed (e.g., `ollama run llama3`)
# llm = Ollama(model="llama3.2:1b")

# Initialize LLM via Gemini. ChatGoogleGenerativeAI defaults to GOOGLE_API_KEY then
# GEMINI_API_KEY; a wrong system GOOGLE_API_KEY can mask backend/.env — we prefer
# GEMINI_API_KEY and pass api_key explicitly.
_gemini = os.environ.get("GEMINI_API_KEY", "").strip()
_google = os.environ.get("GOOGLE_API_KEY", "").strip()
_api_key = _gemini or _google
if not _api_key:
    raise RuntimeError(
        "No API key: set GEMINI_API_KEY in backend/.env (or GOOGLE_API_KEY as fallback)."
    )

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2,
    api_key=_api_key,
)

vectorstore = None
QA_CHAIN_PROMPT = None

def initialize_rag():
    global vectorstore, QA_CHAIN_PROMPT
    
    if os.path.exists(CHROMA_DB_DIR):
        print("Loading existing Chroma vector database...")
        vectorstore = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
    else:
        print(f"Creating new Chroma vector database from {DATASET_PATH}...")
        try:
            # Read a sample to avoid extremely long indexing times for the demo
            df = pd.read_csv(DATASET_PATH, nrows=1000)
            # Use 'text' column for documents, keep 'title' and 'subject' as metadata
            loader = DataFrameLoader(df, page_content_column="text")
            documents = loader.load()
            
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            texts = text_splitter.split_documents(documents)
            
            print(f"Indexing {len(texts)} chunks...")
            vectorstore = Chroma.from_documents(
                documents=texts,
                embedding=embeddings,
                persist_directory=CHROMA_DB_DIR
            )
            print("Vector database created and persisted.")
        except Exception as e:
            print(f"Error during database initialization: {e}")
            raise e
            
    # Define custom prompt for Fake News Detection
    template = """
    You are an expert fact-checker. Decide whether the "News Claim" is True, Fake, or Unverifiable using ONLY the "Context facts" below. Do not use general world knowledge beyond what appears in the context.

    RULES:
    1. If the context is empty, or the retrieved facts are clearly about a different topic than the claim (no meaningful overlap in people, places, or subject matter), respond with "Unverifiable".
    2. If the context covers the same topic as the claim and its statements agree with or confirm the main factual points of the claim, respond with "True".
    3. If the context covers the same topic but clearly contradicts a central factual assertion in the claim, respond with "Fake".
    4. If the context is related but too thin or ambiguous to confirm or refute the claim, respond with "Unverifiable".
    5. Paraphrases and the same story reported in different words still count as addressing the claim — you do not need word-for-word repetition of the headline.
    6. LONG CLAIMS / PARTIAL CONTEXT: The context is only a few excerpts from a vector database; the "News Claim" may be a full article split across many chunks. If the excerpts clearly continue the same wire-style story (same people, timeline, and narrative thread as the claim) and nothing in the excerpts contradicts the claim, respond with "True" — do NOT mark "Unverifiable" only because later sentences of the claim are not repeated verbatim in the excerpts.
    7. Your answer must START with exactly one of these words: True, Fake, or Unverifiable (then you may add a short explanation after that word).

    Context facts:
    {context}
    
    News Claim to evaluate:
    {question}
    
    Assessment:
    """
    
    QA_CHAIN_PROMPT = PromptTemplate(
        input_variables=["context", "question"],
        template=template,
    )

def analyze_news(text: str):
    """Uses dynamic retrieval: long pasted articles need many chunks; fixed small k misses later paragraphs."""
    global vectorstore, QA_CHAIN_PROMPT
    if not vectorstore or QA_CHAIN_PROMPT is None:
        initialize_rag()

    n = max(len(text), 1)
    # ~1000-char chunks in the DB; scale k so long queries pull spans across the full article
    k = min(32, max(8, n // 400))
    fetch_k = min(120, max(k * 4, 32))
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": k,
            "fetch_k": fetch_k,
            "lambda_mult": 0.55,
        },
    )
    chain = RetrievalQA.from_chain_type(
        llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": QA_CHAIN_PROMPT},
    )
    return chain.invoke({"query": text})

def add_news_to_db(text: str, title: str = "User Added Fact", subject: str = "User Submitted"):
    if not vectorstore:
        initialize_rag()
    
    # We create a single document or split it if it's long
    from langchain_core.documents import Document
    doc = Document(page_content=text, metadata={"title": title, "subject": subject})
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents([doc])
    
    vectorstore.add_documents(texts)
    # Chroma persists automatically in newer versions when add_documents is called, or you can call persist
    if hasattr(vectorstore, "persist"):
        vectorstore.persist()
    print(f"Added new fact to DB: {title}")
