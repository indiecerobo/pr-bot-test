# AI PR Reviewer

An autonomous code review agent that reads a Pull Request, searches the existing codebase for relevant context, and posts a structured review — automatically, via GitHub Actions.

Unlike simple "diff in, comment out" review bots, this project builds a **searchable, structure-aware index of the entire codebase first**, then gives the AI a **search tool** it can call on its own to decide what additional context it needs before writing a review — genuine agentic tool use, not a single prompt-and-response call.

![GitHub Action running successfully](./assets/example-review%20(2).png)

## How it works

![Bot comment appearing on the PR](./assets/example-review%20(3).png)
1. **Ingest** — clones the target repo and parses every file with `tree-sitter` to extract complete functions and classes (not naive text chunking, which breaks logic mid-function).
2. **Index** — embeds each function/class with `sentence-transformers` and stores them in a local `Chroma` vector database.
3. **Agent loop** — when a PR opens, the new code is handed to an LLM (via Groq, running Llama-class open models) with access to a `search_codebase` tool. The model decides for itself what to look up — e.g. "how is authentication handled elsewhere in this repo?" — before writing its review.
4. **Deliver** — the finished review is posted as a real comment on the PR via the GitHub API, triggered automatically by a GitHub Actions workflow on every `pull_request` event.

## Example

![AI review comment on a real PR](./assets/example-review%20(1).png)
On a PR adding a plaintext-password login function, the agent independently searched the codebase for the existing auth pattern and flagged:
- Missing password hashing (found the correct `check_password_hash` pattern already in use elsewhere)
- A crash risk on nonexistent users
- Inconsistent session handling vs. the rest of the codebase
- Duplicate logic vs. an existing helper

All without being told where to look — it found this by searching autonomously.

## Architecture


```
PR opened
   |
   v
GitHub Actions triggers workflow
   |
   v
Clone repo --> Parse with tree-sitter --> Embed with sentence-transformers --> Store in Chroma
   |
   v
Agent loop:
   AI reviews new code
   AI decides if it needs more context
   AI calls search_codebase(query) --> gets results --> repeats (bounded)
   AI writes final review
   |
   v
Review posted back to PR via GitHub API
```