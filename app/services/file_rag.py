import os
import shutil
import sys
import uuid
import tempfile
from typing import List

from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
    PythonLoader,
    CSVLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ------------------ PATH FIX ------------------ #
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_APP_DIR = os.path.dirname(_CURRENT_DIR)
_ROOT_DIR = os.path.dirname(_APP_DIR)

if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

from services.main_db import hosted_from_local

# ------------------ CONFIG ------------------ #
MODEL_NAME = "gpt-oss:20b-cloud"

llm = ChatOllama(
    model=MODEL_NAME,
    temperature=0.1,
)

embeddings = OllamaEmbeddings(
    model="nomic-embed-text:latest"
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150
)

# ------------------ TEMP DIR ------------------ #
def get_temp_persist_dir():
    # OS temp directory → auto-isolated + safe
    return os.path.join(tempfile.gettempdir(), f"rag_{uuid.uuid4().hex}")

# ------------------ LOAD DOCUMENT ------------------ #
def load_document(filepath: str) -> List[Document]:

    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".pdf":
        loader = PyPDFLoader(filepath)

    elif ext == ".txt":
        loader = TextLoader(filepath)

    elif ext in [".docx", ".doc"]:
        loader = UnstructuredWordDocumentLoader(filepath)

    elif ext == ".py":
        loader = PythonLoader(filepath)

    elif ext == ".pptx":
        loader = UnstructuredPowerPointLoader(filepath)

    elif ext == ".csv":
        loader = CSVLoader(filepath)

    elif ext == ".xlsx":
        loader = UnstructuredExcelLoader(filepath)

    else:
        print(f"Unsupported file: {ext}")
        return []

    return loader.load()

# ------------------ MAIN FUNCTION ------------------ #
def run_rag(file_path: str, query: str):

    print(f"\nProcessing: {file_path}")

    persist_dir = get_temp_persist_dir()

    try:
        vector_store = Chroma(
            collection_name="single_file_rag",
            embedding_function=embeddings,
            persist_directory=persist_dir+"_single",
        )

        docs = load_document(file_path)

        if not docs:
            return {"response": "No valid documents found."}

        # 🔥 Split documents (critical for quality)
        split_docs = text_splitter.split_documents(docs)

        # Add metadata (optional but useful)
        for doc in split_docs:
            doc.metadata["file_path"] = file_path

        # 🔹 Store embeddings
        vector_store.add_documents(split_docs)

        # 🔹 Retrieve top results (Increase K for more comprehensive context)
        retrieved_docs = vector_store.similarity_search(query, k=10)

        if not retrieved_docs:
            return {"response": "No relevant information found in the document."}

        # 🔹 Build context with Source/Page info
        context_parts = []
        for i, doc in enumerate(retrieved_docs):
            page_info = f" [Page {doc.metadata.get('page', 'N/A')}]" if 'page' in doc.metadata else ""
            context_parts.append(f"--- Chunk {i+1}{page_info} ---\n{doc.page_content}")
        
        context = "\n\n".join(context_parts)

        # 🔹 Optimized Prompt for Smart Analysis
        prompt = f"""
        <start_of_turn>user
        You are an advanced Document Analyst. Your goal is to provide a highly accurate, smart, and comprehensive answer to the user's question based strictly on the provided document context.

        ### USER QUESTION:
        "{query}"

        ### DOCUMENT CONTEXT:
        {context}

        ### GUIDELINES:
        1. **Analyze Deeply**: Look for subtle details across different chunks to provide a complete answer.
        2. **Stay Factual**: Only use information provided in the context. Do not hallucinate.
        3. **Cite Sources**: If the context mentions page numbers (e.g., [Page 5]), include them in your answer to increase credibility.
        4. **Structure**: Use bullet points or numbered lists if the answer is complex.
        5. **Handle Missing Info**: If the context doesn't contain the answer, state: "I'm sorry, but that information is not available in the document."

        <end_of_turn>
        <start_of_turn>model
        """

        # 🔹 Generate response
        response = llm.invoke(prompt).content.strip()

        return {
            "response": response,
            "file_name": os.path.basename(file_path),
            "file_path": file_path,
            "hosted_link": hosted_from_local(file_path)
        }

    finally:
        try:
            shutil.rmtree(persist_dir)
        except Exception:
            pass


# ------------------ TEST ------------------ #
if __name__ == "__main__":

    file = "tests/aif-presentation (1).pptx"

    while True:
        query = input("Query: ")
        result = run_rag(file, query)
        print(result)