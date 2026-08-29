import tree_sitter_python as tspython
from tree_sitter import Language, Parser
import os

PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)

def find_code_units(node, code_bytes, file_path):
    """Walks the tree and pulls out every function AND class."""
    units = []

    if node.type in ("function_definition", "class_definition"):
        start_byte = node.start_byte
        end_byte = node.end_byte
        unit_code = code_bytes[start_byte:end_byte].decode("utf8")

        name_node = node.child_by_field_name("name")
        unit_name = name_node.text.decode("utf8") if name_node else "unknown"

        units.append({
            "type": "function" if node.type == "function_definition" else "class",
            "name": unit_name,
            "code": unit_code,
            "file": file_path,
            "start_line": node.start_point[0] + 1,
            "end_line": node.end_point[0] + 1
        })

    for child in node.children:
        units.extend(find_code_units(child, code_bytes, file_path))

    return units


def process_repo(repo_path):
    """Goes through every .py file in the repo and extracts all functions/classes."""
    all_units = []

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__']]

        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)

                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        code = f.read()

                    code_bytes = bytes(code, "utf8")
                    tree = parser.parse(code_bytes)

                    units = find_code_units(tree.root_node, code_bytes, full_path)
                    all_units.extend(units)

                except Exception as e:
                    # Some files might fail to read/parse - just skip and note it
                    print(f"Skipped {full_path}: {e}")

    return all_units


# Run it on our already-cloned repo
all_units = process_repo("temp_repo")

print(f"\nTotal code units found across whole repo: {len(all_units)}")

# Count how many functions vs classes
functions = [u for u in all_units if u["type"] == "function"]
classes = [u for u in all_units if u["type"] == "class"]
print(f"  Functions: {len(functions)}")
print(f"  Classes: {len(classes)}")

# Show a few examples
print("\n--- Sample of what we found ---")
for unit in all_units[:5]:
    print(f"[{unit['type']}] {unit['name']}  ({unit['file']}, lines {unit['start_line']}-{unit['end_line']})")