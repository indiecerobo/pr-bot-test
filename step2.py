import tree_sitter_python as tspython
from tree_sitter import Language, Parser

# 1. Set up the parser for Python specifically
PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)

# 2. Pick a file to test on (using one from the repo we already cloned)
file_path = "temp_repo/examples/tutorial/flaskr/auth.py"

with open(file_path, 'r', encoding='utf-8') as f:
    code = f.read()

# 3. Parse the code into a tree structure
# tree-sitter needs the code as bytes, not a normal string, so we convert it
tree = parser.parse(bytes(code, "utf8"))

root_node = tree.root_node

# 4. Walk through the tree and find all function definitions
def find_functions(node, code_bytes):
    functions = []
    
    # If this node IS a function definition, grab it
    if node.type == "function_definition":
        start_byte = node.start_byte
        end_byte = node.end_byte
        function_code = code_bytes[start_byte:end_byte].decode("utf8")
        
        # Try to get the function's name too
        name_node = node.child_by_field_name("name")
        function_name = name_node.text.decode("utf8") if name_node else "unknown"
        
        functions.append({
            "name": function_name,
            "code": function_code,
            "start_line": node.start_point[0] + 1,
            "end_line": node.end_point[0] + 1
        })
    
    # Keep looking inside this node's children too (functions can be nested)
    for child in node.children:
        functions.extend(find_functions(child, code_bytes))
    
    return functions

code_bytes = bytes(code, "utf8")
functions = find_functions(root_node, code_bytes)

# 5. Show what we found
print(f"Found {len(functions)} functions in {file_path}\n")

for func in functions:
    print(f"Function: {func['name']}  (lines {func['start_line']}-{func['end_line']})")
    print("---")
    print(func['code'][:200])  # first 200 chars so it's not overwhelming
    print("===\n")