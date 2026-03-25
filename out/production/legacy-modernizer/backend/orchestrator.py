import os
import json
from pathlib import Path
from backend.parser import parse_code, parser, find_method_declarations
from backend.context_optimizer import build_optimized_context, get_method_name
from backend.llm_client import generate_modernized_code

def orchestrate_modernization(input_dir: str, output_dir: str, target_lang: str, target_function: str):
    """
    Main flow:
    1. Find all Java files in `input_dir`
    2. Look for the `target_function` in those files to build a mapping
    3. Construct optimized context
    4. Call LLM to modernize
    5. Write outputs
    """
    input_path = Path(input_dir)
    java_files = list(input_path.rglob("*.java"))
    
    if not java_files:
        print(f"No Java files found in {input_dir}")
        return

    # Parse all Java files and build a global method registry
    all_method_nodes = {}
    for j_file in java_files:
        try:
            with open(j_file, 'rb') as f:
                code_bytes = f.read()
            
            tree = parser.parse(code_bytes)
            
            print(f"Analyzing {j_file.name} to build method registry...")
            methods = find_method_declarations(tree.root_node)
            for m in methods:
                name = get_method_name(m, code_bytes)
                all_method_nodes[name] = (m, code_bytes)
                
        except Exception as e:
            print(f"Error parsing {j_file}: {e}")
            
    try:
        context = build_optimized_context(target_function, all_method_nodes)
        print(f"Found '{target_function}' in repository. Context optimized.")
    except ValueError:
        print(f"Target function '{target_function}' could not be found in any parsed Java files.")
        return
        
    print(f"Dependencies mapped: {[d['name'] for d in context['dependencies']]}")
    print(f"Sending context to LLM for '{target_lang}' modernization...")
    
    response_text = generate_modernized_code(context, target_lang)
    
    # Process LLM response
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Sometimes the LLM wraps JSON in markdown blocks
        clean_json = response_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        
        modern_code = data.get("modernized_code", "")
        tests = data.get("unit_tests", "")
        
        ext = ".py" if target_lang.lower() == "python" else ".go"
        
        target_file = out_path / f"{target_function}_modern{ext}"
        tests_file = out_path / f"test_{target_function}{ext}"
        
        with open(target_file, "w") as f:
            f.write(modern_code)
            
        with open(tests_file, "w") as f:
            f.write(tests)
            
        print(f"Successfully wrote modernized code to {target_file}")
        print(f"Successfully wrote unit tests to {tests_file}")
        
    except json.JSONDecodeError:
        print("Failed to decode LLM response as JSON. Raw output:")
        print(response_text)
        
        # Dump RAW to file anyway
        raw_file = out_path / f"{target_function}_raw.txt"
        with open(raw_file, "w") as f:
            f.write(response_text)
        print(f"Dumped raw response to {raw_file}")
