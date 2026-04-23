import os
import sys
from typing import List
from collections import defaultdict
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from rank_bm25 import BM25Okapi

# --- Path Optimization ---
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.abspath(os.path.join(_CURRENT_DIR, "..", ".."))

if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from services.helper_functions import generate_reasoning, MODEL_NAME
from services.main_db import hosted_from_local

PERSIST_DIR = os.path.join(_ROOT_DIR, "models", "files_vector")

llm = ChatOllama(
    model=MODEL_NAME,
    temperature=0
)

embeddings = OllamaEmbeddings(model="nomic-embed-text:latest")

vector_store = Chroma(
    collection_name="smart_files",
    embedding_function=embeddings,
    persist_directory=PERSIST_DIR,
)


def rewrite_query(query: str) -> str:
    prompt = f"""
Rewrite the following query to make it more specific and optimized for document retrieval.
Do not change intent. Add relevant keywords if needed.

Query: {query}

Rewritten Query:
"""
    response = llm.invoke(prompt)
    return response.content.strip()


def load_all_documents():
    data = vector_store.get()

    docs = []
    for content, metadata in zip(data["documents"], data["metadatas"]):
        docs.append(Document(page_content=content, metadata=metadata))

    return docs


class BM25Retriever:
    def __init__(self, documents: List[Document]):
        self.documents = documents
        self.corpus = [doc.page_content.split() for doc in documents]
        self.bm25 = BM25Okapi(self.corpus)

    def search(self, query: str, k: int = 5):
        tokenized_query = query.split()
        scores = self.bm25.get_scores(tokenized_query)

        ranked = sorted(
            zip(self.documents, scores),
            key=lambda x: x[1],
            reverse=True
        )

        return [doc for doc, _ in ranked[:k]]


def hybrid_search(query: str, k: int = 3):
    # Vector search
    vector_results = vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={"k": k, "fetch_k": 20}
    ).invoke(query)

    all_docs = load_all_documents()

    if not all_docs:
        print("No documents in DB, skipping BM25")
        return vector_results

    bm25 = BM25Retriever(all_docs)
    bm25_results = bm25.search(query, k)

    # Combine
    combined = vector_results + bm25_results

    unique = {}
    for doc in combined:
        key = doc.page_content[:100]
        if key not in unique:
            unique[key] = doc

    return list(unique.values())[:k]


# ================== ✅ UPDATED FUNCTION ================== #
def suggest_files(query: str, k: int = 10):
    results = hybrid_search(query, k)

    # 🔹 Group by file_path
    grouped_data = defaultdict(lambda: {
        "file_type": None,
        "pages": set(),
        "contents": []
    })

    for doc in results:
        metadata = doc.metadata

        file_path = metadata.get("file_path")
        file_type = metadata.get("type", "unknown")
        page = metadata.get("page")

        if not file_path:
            continue

        grouped_data[file_path]["file_type"] = file_type

        if page is not None:
            grouped_data[file_path]["pages"].add(int(page))

        grouped_data[file_path]["contents"].append(doc.page_content)

    from concurrent.futures import ThreadPoolExecutor

    # 🔹 Build final JSON output concurrently
    final_output = []

    def process_file_data(file_path, data):
        file_name = os.path.basename(file_path)
        file_type = data["file_type"]
        hosted_link = hosted_from_local(file_path)
        contents = data["contents"]
        reasoning = generate_reasoning(
            query=query,
            file_path=file_path,
            file_type=file_type,
            pages_content=contents[:3]  # Limit to top 3 chunks for faster processing
        )
        return {
            "file_name": file_name,
            "file_type": file_type,
            "file_path": file_path,
            "hosted_link": hosted_link,
            "reasoning": reasoning
        }

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for file_path, data in grouped_data.items():
            futures.append(executor.submit(process_file_data, file_path, data))

        for f in futures:
            final_output.append(f.result())

    return final_output


    

# ================== MAIN ================== #
if __name__ == "__main__":
    query = "pipeline of stock watchlist assistant?"

    files = suggest_files(query)

    print("\nFILE SUGGESTIONS\n")
    for f in files:
        print(f)


# {'file_name': '2306.08161.pdf', 'file_type': 'pdf', 'file_path': 'app/data/documents/2306.08161.pdf', 'hosted_link': 'https://drive.google.com/file/d/1Wi-ZqO0Xxx5EribGm2GB-Q2wISr6GtL0/view?usp=drive_link', 'reasoning': 'This document is relevant because the text details the development of H2OLLM Data Studio, a tool used for data preparation for LLM fine-tuning, and highlights the use of Open Source strategies for AI benefits. On page 2, it explains the data preparation process, including dataset creation and transformation steps, specifically focusing on text summarization and addressing potential issues like profanity.  The document also introduces H2OGPT by H2O.ai, emphasizing its role as a democratizing effort for large language models. On page 3, it describes the model architecture and LoRA adapters used for causal language modeling, referencing the RWForCausalLM model.'}
# {'file_name': 'CA3-25070149025.pdf', 'file_type': 'pdf', 'file_path': 'app/data/documents/CA3-25070149025.pdf', 'hosted_link': 's3://stock-watchlist-assistant/CA3-25070149025.pdf', 'reasoning': 'This document is relevant because the query asks for a recommendation regarding stock watchlist assistant, specifically focusing on the synthesis of technical indicators and news sentiment. The document details a two-path pipeline for generating explainable signals, utilizing FinBERT and ESF for analysis. It highlights limitations of existing tools and proposes a two-stage process – daily digest and live analysis – to provide a clear, concise explanation linked to a user’s objective. The document also details the API endpoints for data retrieval and analysis, including the caching of results in localStorage.  Therefore, a buy recommendation is suggested: wait for RSI < 50, as it aligns with the current data flow and potential for a profitable trade.'}