import re
from pathlib import Path

def build_fallback_context(target_function: str, file_paths: list[str], max_chars: int = 30000) -> dict:
    """
    Regex-based context builder for COBOL or languages without strict AST support.
    Searches across provided files for the target function/paragraph and bounds the extraction 
    tightly within the 30k token character limit.
    """
    extracted_text = ""
    found = False
    
    # Matches COBOL section/paragraph names or general function names aggressively
    target_pattern = re.compile(rf'\b{re.escape(target_function)}\b', re.IGNORECASE)

    for f_path in file_paths:
        try:
            with open(f_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            match = target_pattern.search(content)
            if match:
                found = True
                
                # Append file content if we have room in the budget
                if len(extracted_text) + len(content) <= max_chars:
                    extracted_text += f"\n--- File: {Path(f_path).name} ---\n{content}\n"
                else:
                    # Truncate content securely around the match to fit context limits
                    budget = max_chars - len(extracted_text)
                    if budget > 1000:
                        start = max(0, match.start() - (budget // 2))
                        end = min(len(content), match.start() + (budget // 2))
                        extracted_text += f"\n--- File: {Path(f_path).name} (Truncated to fit LLM budget) ---\n" + content[start:end]
                    break # Reached total character capacity
        except Exception as e:
            print(f"Error reading {f_path}: {e}")
            continue
            
    if not found:
        raise ValueError(f"Target logic '{target_function}' could not be located in the COBOL repository.")
        
    return {
        "target_function": target_function,
        "target_code_stripped": extracted_text.strip(),
        "dependencies": [], # Empty list since AST BFS mapping isn't active
        "is_fallback": True
    }
