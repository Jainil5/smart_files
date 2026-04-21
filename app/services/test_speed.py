import time
from main_search import hybrid_search, generate_reasoning, vector_store, BM25Retriever, rewrite_query

query = "stock watchlist assistant"
start = time.time()
vector_store.get()
print("vector_store.get() took", time.time() - start)

start = time.time()
rewrite_query(query)
print("rewrite_query took", time.time() - start)

docs = hybrid_search(query, k=2)
print("hybrid_search took", time.time() - start)

start = time.time()
for doc in docs:
    generate_reasoning(query, "doc", "pdf", [doc.page_content])
print("generate_reasoning (2 docs) took", time.time() - start)
