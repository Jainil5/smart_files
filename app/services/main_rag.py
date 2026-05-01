import os
import sys
from typing import List

# --- Path Optimization ---
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_APP_DIR = os.path.dirname(_CURRENT_DIR)
_ROOT_DIR = os.path.dirname(_APP_DIR)

if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from services.helper_functions import MODEL_NAME
from services.main_db import hosted_from_local, hosted_from_name
from services.config import MODELS_DIR

from services.monitoring import (
    start_run,
    log_config,
    log_latency,
    log_selected_file,
    log_rag_output,
    Timer
)

# ------------------ CONFIG ------------------ #
PERSIST_DIR = os.path.join(MODELS_DIR, "files_vector")

llm = ChatOllama(
    model=MODEL_NAME,
    temperature=0,
)

embeddings = OllamaEmbeddings(
    model="nomic-embed-text:latest"
)

vector_store = Chroma(
    collection_name="smart_files",
    embedding_function=embeddings,
    persist_directory=PERSIST_DIR,
)

# ------------------ MAIN FUNCTION ------------------ #
def rag_qna(query: str, k: int = 5):

    timer = Timer()

    with start_run("rag_query"):

        # 🔹 Log config
        log_config(
            embedding_model="nomic-embed-text",
            top_k=k
        )

        # 🔹 Step 1: Retrieve top-k chunks
        timer.start()
        docs: List[Document] = vector_store.similarity_search(query, k=k)
        retrieval_time = timer.stop()

        log_latency(retrieval_time=retrieval_time)

        if not docs:
            return {
                "response": "No relevant information found.",
                "sources": []
            }

        # 🔹 Step 2: Score files
        file_scores = {}

        for rank, doc in enumerate(docs):
            file_path = doc.metadata.get("file_path")
            if not file_path:
                continue

            file_scores[file_path] = file_scores.get(file_path, 0) + (1 / (rank + 1))

        # 🔹 Step 3: Pick best file
        best_file = max(file_scores, key=file_scores.get)
        file_name = os.path.basename(best_file)

        log_selected_file(file_name)

        # 🔹 Step 4: Collect chunks ONLY from best file
        same_file_docs = [
            doc for doc in docs
            if doc.metadata.get("file_path") == best_file
        ][:5]

        context = "\n".join([doc.page_content for doc in same_file_docs])

        # 🔹 Step 5: Prompt
        prompt = f"""
            You are a precise question-answering assistant.

            QUESTION:
            {query}

            CONTEXT:
            {context}

            INSTRUCTIONS:
            - Answer ONLY from context
            - Do NOT hallucinate
            - If answer is not found, say: "Not found in document"
            - Keep answer concise

            ANSWER:
            """

        # 🔹 Step 6: Generate answer
        timer.start()
        response = llm.invoke(prompt).content.strip()
        llm_time = timer.stop()
        file_type = os.path.splitext(file_name)[1].lower()
        log_latency(llm_time=llm_time)

        # 🔹 Save output
        log_rag_output(query, response, file_name)

        return {
            "response": response,
            "file_name": file_name,
            "file_type": file_type,
            "hosted_link": hosted_from_name(file_name),
        }


# ------------------ TEST ------------------ #
if __name__ == "__main__":
    query = "pipeline of stock watchlist assistant"
    result = rag_qna(query)
    print(result)