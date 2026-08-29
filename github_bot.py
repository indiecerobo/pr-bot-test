import os
from dotenv import load_dotenv
from github import Github

# Reuse everything from step 6 - the agentic review function
from agent import agentic_review

load_dotenv()

# 1. Connect to GitHub using our token
gh = Github(os.getenv("GITHUB_TOKEN"))

def get_pr_diff(owner, repo_name, pr_number):
    """Fetches a real PR's changed files and their code."""

    repo = gh.get_repo(f"{owner}/{repo_name}")
    pr = repo.get_pull(pr_number)

    print(f"PR Title: {pr.title}")
    print(f"PR Author: {pr.user.login}")
    print(f"Files changed: {pr.changed_files}")
    print()

    files_changed = []

    for file in pr.get_files():
        files_changed.append({
            "filename": file.filename,
            "status": file.status,
            "patch": file.patch,
            "additions": file.additions,
            "deletions": file.deletions
        })

    return pr, files_changed


def post_review_comment(pr, review_text, filename):
    """Posts the AI's review as a comment on the PR."""

    comment_body = f"""## 🤖 AI Code Review — `{filename}`

{review_text}

---
*This review was generated automatically by an AI agent with codebase context.*
"""

    pr.create_issue_comment(comment_body)
    print(f"Posted review comment to PR #{pr.number}")


def review_pr(owner, repo_name, pr_number, post_to_github=False):
    """Full pipeline: fetch a real PR, review each changed file, print results,
    and optionally post the review back to GitHub."""

    pr, files_changed = get_pr_diff(owner, repo_name, pr_number)

    if not files_changed:
        print("No files changed in this PR.")
        return

    for file in files_changed:
        print("=" * 60)
        print(f"FILE: {file['filename']} ({file['status']})")
        print(f"+{file['additions']} / -{file['deletions']}")
        print("=" * 60)

        if file['patch'] is None:
            print("(No text diff available for this file - possibly binary or too large)")
            continue

        print("Running agentic review...\n")
        review = agentic_review(file['patch'])

        print("\nREVIEW:")
        print(review)
        print()

        if post_to_github:
            post_review_comment(pr, review, file['filename'])


if __name__ == "__main__":
    # When running as a GitHub Action, these come from environment variables
    # automatically set by GitHub. When running locally, we fall back to
    # hardcoded test values.

    repo_full_name = os.getenv("GITHUB_REPOSITORY")  # e.g. "indiecerobo/pr-bot-test"
    pr_number_str = os.getenv("PR_NUMBER")

    if repo_full_name and pr_number_str:
        # Running inside GitHub Actions
        owner, repo_name = repo_full_name.split("/")
        pr_number = int(pr_number_str)
    else:
        # Running locally for testing
        owner, repo_name, pr_number = "indiecerobo", "pr-bot-test", 1

    review_pr(owner, repo_name, pr_number, post_to_github=True)