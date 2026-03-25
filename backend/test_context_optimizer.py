import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.parser import parser, find_method_declarations
from backend.context_optimizer import build_optimized_context, get_method_name

def create_mock_nodes(files):
    all_method_nodes = {}
    for code_bytes in files:
        tree = parser.parse(code_bytes)
        methods = find_method_declarations(tree.root_node)
        for m in methods:
            name = get_method_name(m, code_bytes)
            all_method_nodes[name] = (m, code_bytes)
    return all_method_nodes

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
    
    all_method_nodes = create_mock_nodes([file1, file2])
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
    print("test_optimization passed!")

def test_bfs_dependencies():
    file1 = b'''
    class Main {
        public void rootFunction() {
            levelOneFunction();
        }
    }
    '''
    
    file2 = b'''
    class Dep1 {
        public void levelOneFunction() {
            levelTwoFunction();
        }
    }
    '''
    
    file3 = b'''
    class Dep2 {
        public void levelTwoFunction() {
            System.out.println("Deeply nested");
        }
    }
    '''
    
    all_method_nodes = create_mock_nodes([file1, file2, file3])
    context = build_optimized_context("rootFunction", all_method_nodes)
    
    dep_names = [d["name"] for d in context["dependencies"]]
    assert "levelOneFunction" in dep_names, "BFS failed to find first level dependency"
    assert "levelTwoFunction" in dep_names, "BFS failed to traverse to second level dependency"
    print("test_bfs_dependencies passed!")

def test_max_context_length():
    file1 = b'''
    class Main {
        public void root() {
            bigDependency();
            smallDependency();
        }
        
        public void smallDependency() {
            int a = 1;
        }
        
        public void bigDependency() {
            String b = "This is a very very long string that will push us over the limit. This is a very very long string that will push us over the limit.";
        }
    }
    '''
    
    all_method_nodes = create_mock_nodes([file1])
    # The root code stripped length + bigDependency length might be large.
    # Let's see lengths:
    # root stripped: ~60 chars
    # smallDependency: ~40 chars
    # bigDependency: ~100 chars
    context = build_optimized_context("root", all_method_nodes, max_context_length=250)
    
    dep_names = [d["name"] for d in context["dependencies"]]
    print(f"DEBUG: dep_names = {dep_names}")
    # We expect smallDependency to be included? Wait.
    # The BFS logic iterates over invocations in order. In root, bigDependency is called first.
    # root ~ 60, bigDependency ~ 100 -> 160 > 150.
    # So bigDependency will be skipped!
    # smallDependency ~ 40 -> 60 + 40 = 100 < 150. smallDependency will be included.
    assert "smallDependency" in dep_names, "smallDependency should fit within the context length."
    assert "bigDependency" not in dep_names, "bigDependency should have been skipped."
    print("test_max_context_length passed!")

if __name__ == "__main__":
    test_optimization()
    test_bfs_dependencies()
    test_max_context_length()
    print("All tests passed!")
