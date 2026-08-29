import git
import os

# 1. This is the repo we want to "read"
repo_url = "https://github.com/pallets/flask"  # example repo - you can change this
local_path = "temp_repo"  # where we'll save it on your computer

# 2. Download (clone) the repo if we haven't already
if not os.path.exists(local_path):
    print("Cloning the repo... this might take a moment")
    git.Repo.clone_from(repo_url, local_path)
    print("Done cloning!")
else:
    print("Repo already exists, skipping clone")

# 3. Walk through every file in the repo
code_files = []

for root, dirs, files in os.walk(local_path):
    # Skip folders we don't care about
    dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__']]
    
    for file in files:
        if file.endswith('.py'):  # only Python files for now
            full_path = os.path.join(root, file)
            code_files.append(full_path)

# 4. Show what we found
print(f"\nFound {len(code_files)} Python files:")
for f in code_files[:10]:  # just show first 10 so it's not overwhelming
    print(f)
    
# 5. Let's actually read the content of one file, to see what we're working with
sample_file = code_files[0]  # just grab the first one

with open(sample_file, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"\n--- Reading: {sample_file} ---")
print(content[:500])  # only print first 500 characters so it's not a wall of text
print("--- (truncated) ---")