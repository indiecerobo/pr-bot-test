import os
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer
import chromadb

# 1. Load our secret API key from the .env file
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# 2. Load the same embedding model and database from before
model = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="codebase")

def search_codebase(query, n_results=3):
    """Same search function as Step 4."""
    query_embedding = model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=n_results)
    return results

def get_context_for_code(new_code, n_results=3):
    """Search the codebase using the new code itself as the query,
    to find related/similar existing code."""
    results = search_codebase(new_code, n_results=n_results)

    context_snippets = []
    for i in range(len(results['ids'][0])):
        metadata = results['metadatas'][0][i]
        code = results['documents'][0][i]
        context_snippets.append(
            f"From {metadata['file']} ({metadata['type']}: {metadata['name']}):\n{code}"
        )

    return "\n\n---\n\n".join(context_snippets)

def review_code(new_code):
    """The main function: takes new code, finds context, asks the LLM to review it."""

    # Step A: find related code from the rest of the codebase
    print("Searching codebase for related context...")
    context = get_context_for_code(new_code)

    # Step B: build the prompt
    prompt = f"""You are an expert code reviewer. Review the following NEW CODE that someone wants to add to a project.

Here is some RELATED CODE already in the codebase, for context (it may help you spot duplication, inconsistent patterns, or style mismatches):

{context}

---

Now review this NEW CODE:

{new_code}

Give your review as a short list of specific, actionable points. For each point, mention:
- What the issue is (or what's good, if nothing's wrong)
- Why it matters
- A suggested fix if applicable

Be concise and specific. Reference the related code above if relevant (e.g. "this duplicates the logic in X" or "this doesn't follow the pattern used in Y")."""

    # Step C: send it to the LLM (Groq, running Llama 3.3 70B)
    print("Asking the AI to review...\n")

    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    review = completion.choices[0].message.content
    return review


# 3. Test it with a sample "new" function
test_code = '''
def user_login(username, password):
    user = User.query.filter_by(username=username).first()
    if user.password == password:
        session['user_id'] = user.id
        return True
    return False
'''

print("=" * 60)
print("REVIEWING NEW CODE:")
print(test_code)
print("=" * 60)

review = review_code(test_code)

print("AI REVIEW:")
print(review)