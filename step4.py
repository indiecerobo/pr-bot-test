from sentence_transformers import SentenceTransformer
import chromadb

# 1. Load the same embedding model we used to build the database
# (important: you must always search using the SAME model you used to store things,
# otherwise the numbers won't be comparable)
model = SentenceTransformer('all-MiniLM-L6-v2')

# 2. Connect to our existing database (not creating a new one - loading the one from step3)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="codebase")

def search_codebase(query, n_results=5):
    """Takes a plain English question and returns the most relevant code chunks."""
    
    # Turn the question into an embedding, same way we did for the code
    query_embedding = model.encode([query]).tolist()
    
    # Ask ChromaDB: "find the closest matches to this embedding"
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results
    )
    
    return results

# 3. Try it out with a real question
query = "where do we handle user login"
print(f"Searching for: '{query}'\n")

results = search_codebase(query)

# 4. Print results nicely
for i in range(len(results['ids'][0])):
    metadata = results['metadatas'][0][i]
    distance = results['distances'][0][i]  # lower = more similar
    code_snippet = results['documents'][0][i][:150]  # first 150 chars
    
    print(f"Match {i+1} (similarity distance: {distance:.3f})")
    print(f"  {metadata['type']}: {metadata['name']}")
    print(f"  File: {metadata['file']} (lines {metadata['start_line']}-{metadata['end_line']})")
    print(f"  Preview: {code_snippet}...")
    print()