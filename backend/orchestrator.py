import os
import json
from pathlib import Path
from backend.llm_client import generate_modernized_code
from backend.github_ingestor import GitHubIngestor

def orchestrate_modernization(input_dir: str, target_lang: str, target_function: str, output_dir: str = None):
    """
    Main flow:
    1. Find all Java files in `input_dir`
    2. Look for the `target_function` in those files to build a mapping
    3. Construct optimized context
    4. Call LLM to modernize
    5. Optionally write outputs, returns data dict
    """
    input_path = Path(input_dir)
    java_files = list(input_path.rglob("*.java"))
    cobol_files = list(input_path.rglob("*.cbl")) + list(input_path.rglob("*.cob")) + list(input_path.rglob("*.cpy"))
    
    if not java_files and not cobol_files:
        print(f"No Java or COBOL files found in {input_dir}")
        return

    context = None
    all_method_nodes = {}
    if java_files:
        # Lazily import Java parsing components so the backend can still serve COBOL-only use cases.
        try:
            from backend.parser import parse_code, find_method_declarations
            from backend.context_optimizer import get_method_name
            java_import_ok = True
        except Exception as import_exc:
            java_import_ok = False
            print(f"Java parser dependencies not available: {import_exc}")

        if java_import_ok:
            for j_file in java_files:
                try:
                    with open(j_file, 'rb') as f:
                        code_bytes = f.read()

                    root_node = parse_code(code_bytes)

                    print(f"Analyzing {j_file.name} to build method registry...")
                    methods = find_method_declarations(root_node)
                    for m in methods:
                        name = get_method_name(m, code_bytes)
                        all_method_nodes[name] = (m, code_bytes)

                except Exception as e:
                    print(f"Error parsing {j_file}: {e}")
            
    try:
        if java_files and all_method_nodes:
            from backend.context_optimizer import build_optimized_context
            try:
                context = build_optimized_context(target_function, all_method_nodes)
                print(f"Found '{target_function}' in repository. AST Context optimized.")
            except ValueError as e:
                print(e)
                if cobol_files:
                    from backend.fallback_parser import build_fallback_context
                    context = build_fallback_context(target_function, [str(f) for f in cobol_files])
                    print(f"Target not found in Java AST; using COBOL fallback.")
                else:
                    raise ValueError(f"Target function '{target_function}' not found in repository.")
            except Exception as e:
                # If tree-sitter parsing/graph building breaks for a mixed-language repo,
                # fall back to regex extraction from COBOL files when available.
                print(f"Java context build failed: {e}")
                if cobol_files:
                    from backend.fallback_parser import build_fallback_context
                    context = build_fallback_context(target_function, [str(f) for f in cobol_files])
                    print(f"Java context build failed; using COBOL fallback.")
                else:
                    raise
        elif cobol_files:
            from backend.fallback_parser import build_fallback_context
            context = build_fallback_context(target_function, [str(f) for f in cobol_files])
            print(f"Found '{target_function}' in COBOL repository. Fallback context bounded.")
            
    except ValueError as e:
        print(e)
        raise
        
    print(f"Dependencies mapped: {[d['name'] for d in context['dependencies']]}")
    print(f"Sending context to LLM for '{target_lang}' modernization...")
    
    response_text = generate_modernized_code(context, target_lang)
    
    # Process LLM response
    try:
        # Sometimes the LLM wraps JSON in markdown blocks
        clean_json = response_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        
        modern_code = data.get("modernized_code", "")
        tests = data.get("unit_tests", "")
        
        if output_dir:
            out_path = Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            
            ext = ".py" if target_lang.lower() == "python" else ".go"
            
            target_file = out_path / f"{target_function}_modern{ext}"
            tests_file = out_path / f"test_{target_function}{ext}"
            
            with open(target_file, "w") as f:
                f.write(modern_code)
                
            with open(tests_file, "w") as f:
                f.write(tests)
                
            print(f"Successfully wrote modernized code to {target_file}")
            print(f"Successfully wrote unit tests to {tests_file}")
            
        return data
        
    except json.JSONDecodeError:
        print("Failed to decode LLM response as JSON. Raw output:")
        print(response_text)
        
        # Dump RAW to file anyway
        if output_dir:
            raw_file = out_path / f"{target_function}_raw.txt"
            with open(raw_file, "w") as f:
                f.write(response_text)
            print(f"Dumped raw response to {raw_file}")
        raise ValueError("Failed to decode LLM response as JSON.")

def orchestrate_github_modernization(github_url: str, target_lang: str, target_function: str, output_dir: str = None):
    print(f"Ingesting GitHub URL: {github_url}")
    with GitHubIngestor(github_url) as repo_path:
        return orchestrate_modernization(repo_path, target_lang, target_function, output_dir)

