from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.document_loaders import DirectoryLoader, PDFPlumberLoader
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

PERSIST_DIR = "models/chroma_langchain_db"
COLLECTION_NAME = "example_collection"

embeddings = OllamaEmbeddings(model="nomic-embed-text:latest")

model = ChatOllama(
    model="gpt-oss:20b-cloud",
    temperature=0,
)

# Load the persisted vector store first
vector_store = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embeddings,
    persist_directory=PERSIST_DIR,
)

# Only embed & add documents if the collection is empty (avoids re-embedding on every run)
existing_count = vector_store._collection.count()
print(f"Existing documents in vector store: {existing_count}")

if existing_count == 0:
    print("Vector store is empty — loading and embedding documents...")

    text_loader = DirectoryLoader(path="data", glob="*.txt")
    text_docs = text_loader.load()
    csv_loader = DirectoryLoader(path="data", glob="*.csv")
    csv_docs = csv_loader.load()
    pdf_loader = PDFPlumberLoader("data/Leave Policy.pdf")
    pdf_docs = pdf_loader.load()

    docs = text_docs + csv_docs + pdf_docs
    print(f"Loaded {len(docs)} documents total.")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    all_splits = text_splitter.split_documents(docs)
    print(f"Split into {len(all_splits)} chunks. Embedding now (this may take a while)...")

    document_ids = vector_store.add_documents(documents=all_splits)
    print(f"Added {len(document_ids)} chunks to vector store.")
else:
    print("Vector store already populated — skipping embedding step.")

print("-" * 20)

# Note that providers implement different scores; the score here
# is a distance metric that varies inversely with similarity.
# results = vector_store.similarity_search_with_score("Find me a file with h20gpt research paper", k=3)
# doc, score = results[0]
# file = doc.metadata
# print(file['source'])

def rag_pipeline(query, k=3):
    results = vector_store.similarity_search_with_score(query, k=k)
    
    docs = [doc.page_content for doc, _ in results]
    context = "\n\n".join(docs)

    prompt = f"""
    Answer the question using ONLY the context below.
    
    Context:
    {context}

    Question:
    {query}
    """

    response = model.invoke(prompt)
    
    return {
        "query": query,
        "answer": response.content,
        "contexts": docs
    }
result = rag_pipeline("Find me a document that mentions holiday i can get")

print("Query:", result["query"])
print("\nAnswer:", result["answer"])
print("\nRetrieved Contexts:")
for i, ctx in enumerate(result["contexts"]):
    print(f"\n--- Context {i+1} ---")
    print(ctx[:300])