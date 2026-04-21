import time
import sys
from services.main_search import hybrid_search, vector_store, rewrite_query
from services.helper_functions import generate_reasoning
from concurrent.futures import ThreadPoolExecutor

def main():
    query = "pipeline of stock watchlist assistant?"
    
    print("Testing vector_store.get()...")
    s = time.time()
    vector_store.get()
    print("->", time.time() - s)

    print("\nTesting rewrite_query()...")
    s = time.time()
    rewrite_query(query)
    print("->", time.time() - s)

    print("\nTesting generate_reasoning (sequential, 2 calls)...")
    s = time.time()
    generate_reasoning(query, "doc", "pdf", ["some text content"])
    generate_reasoning(query, "doc", "pdf", ["some text content"])
    print("->", time.time() - s)

    print("\nTesting generate_reasoning (parallel, 2 calls)...")
    s = time.time()
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = [
            ex.submit(generate_reasoning, query, "doc", "pdf", ["some text content"]),
            ex.submit(generate_reasoning, query, "doc", "pdf", ["some text content"])
        ]
        [f.result() for f in futures]
    print("->", time.time() - s)

if __name__ == "__main__":
    main()
