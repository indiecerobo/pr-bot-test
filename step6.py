import os
import json
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer
import chromadb

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

model = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="codebase")


def search_codebase(query, n_results=3):
    """The actual search function - same logic as before."""
    query_embedding = model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=n_results)

    formatted_results = []
    for i in range(len(results['ids'][0])):
        metadata = results['metadatas'][0][i]
        code = results['documents'][0][i]
        formatted_results.append({
            "file": metadata['file'],
            "type": metadata['type'],
            "name": metadata['name'],
            "code": code
        })
    return formatted_results


# 1. Describe our tool to the AI - this is a "schema" telling it
# what the tool is called, what it does, and what arguments it needs
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_codebase",
            "description": "Search the codebase for functions or classes related to a given topic or concept. Use this when you need more context about how something is implemented elsewhere in the project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A description of what you're looking for, e.g. 'password hashing' or 'session management'"
                    }
                },
                "required": ["query"]
            }
        }
    }
]


def agentic_review(new_code, max_turns=8):
    """The agent loop: the AI can call search_codebase as many times as it needs,
    then produces a final review."""

    messages = [
        {
            "role": "user",
            "content": f"""You are an expert code reviewer with access to a tool that searches the existing codebase.

Review this NEW CODE:

{new_code}

Use the search_codebase tool to look up any related existing code that would help you give a better review (e.g. how similar things are done elsewhere, whether this duplicates existing logic, whether it matches the codebase's patterns).

IMPORTANT: You should search AT MOST 3 times. After that, or as soon as you have enough context, you MUST stop searching and give your final review as a list of specific, actionable points. Do not keep searching indefinitely — prioritize the most important things to check first."""
        }
    ]

    for turn in range(max_turns):
        print(f"--- Turn {turn + 1} ---")

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            max_tokens=1500,
            messages=messages,
            tools=tools
        )

        ai_message = response.choices[0].message

        # 2. Check: did the AI decide to call a tool, or is it done?
        if ai_message.tool_calls:
            # The AI wants to search - let's honor that
            messages.append(ai_message)  # record the AI's decision in the conversation

            for tool_call in ai_message.tool_calls:
                if tool_call.function.name == "search_codebase":
                    # Extract the query the AI decided to search for
                    args = json.loads(tool_call.function.arguments)
                    query = args["query"]

                    print(f"AI is searching for: '{query}'")

                    # Actually run the search
                    results = search_codebase(query)

                    # Format results as text to send back to the AI
                    results_text = "\n\n".join([
                        f"[{r['type']}] {r['name']} ({r['file']}):\n{r['code']}"
                        for r in results
                    ])

                    # 3. Send the search results back to the AI as a "tool" message
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": results_text
                    })

            # Loop continues - AI will see the results and decide what to do next
            continue

        else:
            # 4. No tool call means the AI is done and gave its final answer
            print("AI finished reviewing.\n")
            return ai_message.content

    # Fallback: force a final answer using whatever context was gathered so far
    print("Max turns reached — forcing a final answer with current context...")
    messages.append({
        "role": "user",
        "content": "You've gathered enough context. Please give your final review now, as a list of specific, actionable points."
    })
    final_response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        max_tokens=1500,
        messages=messages
        # note: no `tools` param here, so it can't search again, just must answer
    )
    return final_response.choices[0].message.content

# Test it
test_code = '''
def user_login(username, password):
    user = User.query.filter_by(username=username).first()
    if user.password == password:
        session['user_id'] = user.id
        return True
    return False
'''

print("=" * 60)
print("AGENTIC REVIEW OF:")
print(test_code)
print("=" * 60)

review = agentic_review(test_code)

print("FINAL REVIEW:")
print(review)