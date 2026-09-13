import os
import sys
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# 1. Ensure API Key is loaded
if not os.environ.get("GOOGLE_API_KEY"):
    print("Error: GOOGLE_API_KEY environment variable is not set.")
    sys.exit(1)

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-2",
    output_dimensionality=768,  # Optional: customize embedding vector dimension
)

# 3. Test single query embedding
print("\n--- Test 1: Single Query Embedding ---")
query_text = "What is Retrieval-Augmented Generation?"
query_vector = embeddings.embed_query(query_text)
print(f"Query: '{query_text}'")
print(f"Embedding dimensions: {len(query_vector)}")
print(f"Sample vector values: {query_vector[:5]}")

# 4. Test document batch embedding
print("\n--- Test 2: Batch Document Embedding ---")
documents = [
    "LangChain simplifies building application context pipelines with LLMs.",
    "Google Gemini offers high-throughput embedding models like text-embedding-004.",
    "PGVector is a PostgreSQL extension for vector similarity search.",
]
doc_vectors = embeddings.embed_documents(documents)
print(f"Successfully generated {len(doc_vectors)} document embeddings.")

# 5. Test integration with a LangChain Vector Store
print("\n--- Test 3: InMemoryVectorStore Search ---")
vector_store = InMemoryVectorStore.from_texts(
    texts=documents, embedding=embeddings
)

search_query = "Tell me about vector databases"
retrieved_docs = vector_store.similarity_search(search_query, k=1)

print(f"Search Query: '{search_query}'")
print(f"Most Relevant Result: '{retrieved_docs[0].page_content}'")

print("\n All tests passed successfully!")