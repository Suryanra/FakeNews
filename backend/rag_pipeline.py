import os
import pandas as pd
from langchain_community.document_loaders import DataFrameLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_classic.chains import RetrievalQA

# Configuration
CHROMA_DB_DIR = "./chroma_db"
DATASET_PATH = r"C:\Users\91840\Desktop\8th sem\Fake news\dataset\News _dataset\True.csv"

# Initialize Embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Initialize LLM via Ollama
# Ensure Ollama is running and has llama3 installed (e.g., `ollama run llama3`)
llm = Ollama(model="tinyllama")

vectorstore = None
qa_chain = None

def initialize_rag():
    global vectorstore, qa_chain
    
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
    You are an expert fact-checker and journalist. You have been asked to evaluate the following news claim or article.
    Use ONLY the provided verified facts (Context) to assess whether the news claim is likely True, Fake, or Unverifiable.
    Provide a clear assessment starting with one of those three words, followed by your explanation based on the facts.
    
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
    
    qa_chain = RetrievalQA.from_chain_type(
        llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True,
        chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
    )

def analyze_news(text: str):
    if not qa_chain:
        initialize_rag()
        
    result = qa_chain.invoke({"query": text})
    return result

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
