import tree_sitter_java as tsjava
from tree_sitter import Language, Parser, Node

# Initialize the Tree-sitter parser for Java
JAVA_LANGUAGE = Language(tsjava.language())
parser = Parser(JAVA_LANGUAGE)

def parse_code(code: bytes):
    """Parses Java code and returns the root Node of the AST."""
    tree = parser.parse(code)
    return tree.root_node

def find_method_declarations(root_node: Node) -> list[Node]:
    """Finds all method declarations in the Java AST."""
    method_nodes = []
    def traverse(node):
        if node.type == "method_declaration":
            method_nodes.append(node)
        for child in node.children:
            traverse(child)
    traverse(root_node)
    return method_nodes

def find_method_invocations(root_node: Node) -> list[Node]:
    """Finds all method invocations in the Java AST."""
    call_nodes = []
    def traverse(node):
        if node.type == "method_invocation":
            call_nodes.append(node)
        for child in node.children:
            traverse(child)
    traverse(root_node)
    return call_nodes

def get_node_text(node: Node, source_code: bytes) -> str:
    """Extracts the exact text spanning the given node."""
    return source_code[node.start_byte:node.end_byte].decode("utf-8")
