from backend.parser import find_method_declarations, find_method_invocations, get_node_text, JAVA_LANGUAGE
from tree_sitter import Node
from collections import deque

def get_method_name(method_node: Node, source_code: bytes) -> str:
    """Extracts the method name from a method_declaration node."""
    for child in method_node.children:
        if child.type == "identifier":
            return get_node_text(child, source_code)
    return ""

def strip_comments(method_node: Node, source_code: bytes) -> str:
    """
    Strips line (`//`) and block (`/* ... */`) comments from the method node's text.
    For simplicity in this prototype, we'll exclude children of type `line_comment` or `block_comment`.
    """
    # Find all comments inside this method node
    comments = []
    def traverse(node):
        if node.type in ["line_comment", "block_comment"]:
            comments.append(node)
        for child in node.children:
            traverse(child)
    traverse(method_node)

    # Collect comment byte ranges
    comment_ranges = sorted([(c.start_byte, c.end_byte) for c in comments], key=lambda x: x[0])
    
    method_start = method_node.start_byte
    method_end = method_node.end_byte
    
    clean_code_parts = []
    current_byte = method_start
    
    for start, end in comment_ranges:
        if start >= current_byte and end <= method_end:
            clean_code_parts.append(source_code[current_byte:start])
            current_byte = end
            
    if current_byte < method_end:
        clean_code_parts.append(source_code[current_byte:method_end])
        
    return b"".join(clean_code_parts).decode("utf-8")

def build_optimized_context(target_function_name: str, all_method_nodes: dict, max_context_length: int = 30000) -> dict:
    """
    Finds the target function and its downstream dependencies (callees) from a global method registry using BFS.
    Returns a dictionary with stripped context, limited to max_context_length characters.
    all_method_nodes: mapping of method_name -> (Node, source_code_bytes)
    """
    if target_function_name not in all_method_nodes:
        raise ValueError(f"Function '{target_function_name}' not found in the source code.")
        
    target_node, target_source_code = all_method_nodes[target_function_name]

    stripped_target = strip_comments(target_node, target_source_code)
    current_length = len(stripped_target)

    context = {
        "target_function": target_function_name,
        "target_code_stripped": stripped_target,
        "dependencies": []
    }
    
    seen_dependencies = {target_function_name}
    queue = deque([(target_node, target_source_code)])
    
    while queue and current_length < max_context_length:
        current_node, current_source_code = queue.popleft()
        
        # Find downstream callees
        calls = find_method_invocations(current_node)
        for call in calls:
            # Extract invoked method name
            call_name = ""
            for child in call.children:
                if child.type == "identifier":
                    call_name = get_node_text(child, current_source_code)
                    break
                    
            # If the invoked method is in the global registry, add its code
            if call_name in all_method_nodes and call_name not in seen_dependencies:
                dep_node, dep_source_code = all_method_nodes[call_name]
                stripped_dep = strip_comments(dep_node, dep_source_code)
                
                # Check if adding this dependency exceeds the max length
                if current_length + len(stripped_dep) > max_context_length:
                    continue  # Skip this one, but queue might still have smaller ones
                    
                context["dependencies"].append({
                    "name": call_name,
                    "code_stripped": stripped_dep
                })
                seen_dependencies.add(call_name)
                current_length += len(stripped_dep)
                
                queue.append((dep_node, dep_source_code))
                
            if current_length >= max_context_length:
                break
            
    return context
