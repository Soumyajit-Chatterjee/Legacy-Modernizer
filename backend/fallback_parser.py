import re
from pathlib import Path

def _build_target_patterns(target_function: str) -> list[re.Pattern]:
    """
    Build a small set of tolerant regex patterns for COBOL paragraphs/sections.
    We intentionally avoid `\b` word-boundaries because COBOL names often end with punctuation
    and include non-word characters (e.g., `-`, `.`, etc.).
    """
    tf = (target_function or "").strip()
    if not tf:
        return []

    # Try a few normalized variants to match common COBOL formatting.
    candidates: list[str] = [
        tf,
        tf.rstrip(".,;:"),
        tf.rstrip(".").rstrip(".,;:"),
    ]
    # Collapse internal whitespace differences.
    candidates.append(re.sub(r"\s+", r"\\s+", tf))

    seen: set[str] = set()
    patterns: list[re.Pattern] = []
    for c in candidates:
        if c in seen or not c:
            continue
        seen.add(c)
        # Escape everything except we already injected `\\s+` into one candidate.
        # If the candidate contains `\\s+`, treat it as a regex.
        if "\\s+" in c:
            patterns.append(re.compile(c, re.IGNORECASE))
        else:
            patterns.append(re.compile(re.escape(c), re.IGNORECASE))

    return patterns


def _slice_around_match(content: str, match_start: int, match_end: int, budget: int) -> str:
    # budget is total remaining budget we can spend for this slice.
    # We slice roughly around the match to preserve relevance.
    if budget <= 0:
        return ""
    # Aim to keep half before and half after.
    half = max(0, budget // 2)
    start = max(0, match_start - half)
    end = min(len(content), match_end + half)
    return content[start:end]


def build_fallback_context(target_function: str, file_paths: list[str], max_chars: int = 30000) -> dict:
    """
    Regex-based context builder for COBOL or languages without strict AST support.
    Searches across provided files for the target function/paragraph and bounds the extraction 
    tightly within the 30k token character limit.
    """
    extracted_text = ""
    found = False
    patterns = _build_target_patterns(target_function)
    if not patterns:
        raise ValueError("Target function is empty.")

    for f_path in file_paths:
        try:
            with open(f_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Find the earliest match across all patterns in this file.
            best_match = None
            for pat in patterns:
                m = pat.search(content)
                if not m:
                    continue
                if best_match is None or m.start() < best_match.start():
                    best_match = m

            if best_match:
                found = True
                
                budget_left = max_chars - len(extracted_text)
                # Append around the first match; do not append whole files (too large/irrelevant).
                slice_text = _slice_around_match(
                    content=content,
                    match_start=best_match.start(),
                    match_end=best_match.end(),
                    budget=budget_left,
                )
                if slice_text:
                    extracted_text += f"\n--- File: {Path(f_path).name} ---\n{slice_text}\n"
                else:
                    # We cannot add more context.
                    break  # Reached total character capacity

                if len(extracted_text) >= max_chars:
                    break
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


def build_fallback_context_from_text(target_function: str, content: str, max_chars: int = 30000) -> dict:
    """
    Fallback context builder for cases where the client pastes legacy code directly
    into the API (no file paths).
    """
    patterns = _build_target_patterns(target_function)
    if not patterns:
        raise ValueError("Target function is empty.")
    if not content:
        raise ValueError("Legacy code is empty.")

    best_match = None
    for pat in patterns:
        m = pat.search(content)
        if not m:
            continue
        if best_match is None or m.start() < best_match.start():
            best_match = m

    if not best_match:
        raise ValueError(f"Target logic '{target_function}' could not be located in the provided code.")

    # Use the full budget for the pasted content slice.
    slice_text = _slice_around_match(
        content=content,
        match_start=best_match.start(),
        match_end=best_match.end(),
        budget=max_chars,
    )

    return {
        "target_function": target_function,
        "target_code_stripped": slice_text.strip(),
        "dependencies": [],
        "is_fallback": True,
    }
