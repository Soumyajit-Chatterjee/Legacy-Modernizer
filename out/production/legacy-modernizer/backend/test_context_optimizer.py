import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.parser import parser, find_method_declarations
from backend.context_optimizer import build_optimized_context, get_method_name

def test_optimization():
    file1 = b'''
    class File1 {
        public void targetMethod() {
            helperMethod1();
            helperMethod2();
            helperMethod1(); // duplicate call to test deduplication
        }
    }
    '''
    
    file2 = b'''
    class File2 {
        public void helperMethod1() {
            // some comment
            int x = 1;
        }
        public void helperMethod2() {
            int y = 2;
        }
        public void unusedMethod() {
            int z = 3;
        }
    }
    '''
    
    tree1 = parser.parse(file1)
    tree2 = parser.parse(file2)
    
    all_method_nodes = {}
    for tree, code in [(tree1, file1), (tree2, file2)]:
        methods = find_method_declarations(tree.root_node)
        for m in methods:
            name = get_method_name(m, code)
            all_method_nodes[name] = (m, code)
            
    context = build_optimized_context("targetMethod", all_method_nodes)
    
    assert context["target_function"] == "targetMethod"
    assert len(context["dependencies"]) == 2, f"Expected 2 dependencies, got {len(context['dependencies'])}"
    
    dep_names = [d["name"] for d in context["dependencies"]]
    assert "helperMethod1" in dep_names
    assert "helperMethod2" in dep_names
    assert "unusedMethod" not in dep_names
    
    # check that comments are stripped from helperMethod1
    h1 = next(d for d in context["dependencies"] if d["name"] == "helperMethod1")
    assert "some comment" not in h1["code_stripped"]
    
    print("All tests passed!")

if __name__ == "__main__":
    test_optimization()
