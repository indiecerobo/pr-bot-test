from sentence_transformers import SentenceTransformer
import chromadb
from step2_5 import process_repo  # reusing your function from before!

# 1. Load an embedding model (this downloads a small AI model the first time you run it)
print("Loading embedding model... (first time takes a minute to download)")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded!")

# 2. Set up a local vector database (Chroma will just create a folder to store everything)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="codebase")

# 3. Get all our code chunks from Step 2.5
print("Extracting code units from repo...")
all_units = process_repo("temp_repo")
print(f"Found {len(all_units)} code units")

# 4. Prepare data for embedding
# ChromaDB needs: unique ids, the text to embed, and metadata for each entry
ids = []
documents = []
metadatas = []

for i, unit in enumerate(all_units):
    ids.append(f"unit_{i}")  # every entry needs a unique ID
    documents.append(unit["code"])  # the actual code text we'll embed
    metadatas.append({
        "name": unit["name"],
        "type": unit["type"],
        "file": unit["file"],
        "start_line": unit["start_line"],
        "end_line": unit["end_line"]
    })

# 5. Add everything to the vector database
# ChromaDB will automatically use our model to embed each document as we add it
print("Embedding and storing all code units... (this may take a few minutes)")

# We do this in batches so it doesn't overload memory with 1600+ items at once
batch_size = 100
for i in range(0, len(documents), batch_size):
    batch_docs = documents[i:i+batch_size]
    batch_ids = ids[i:i+batch_size]
    batch_meta = metadatas[i:i+batch_size]
    
    # Generate embeddings for this batch using our model
    batch_embeddings = model.encode(batch_docs).tolist()
    
    collection.add(
        ids=batch_ids,
        embeddings=batch_embeddings,
        documents=batch_docs,
        metadatas=batch_meta
    )
    print(f"  Processed {min(i+batch_size, len(documents))}/{len(documents)}")

print("\nDone! All code units are now searchable.")
print(f"Total items in database: {collection.count()}")