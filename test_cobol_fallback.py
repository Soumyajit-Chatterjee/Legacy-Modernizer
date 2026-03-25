import asyncio
from backend.fallback_parser import build_fallback_context
import tempfile
from pathlib import Path

# Create a temporary dummy COBOL file
with tempfile.TemporaryDirectory() as temp_dir:
    cobol_file = Path(temp_dir) / "HELLO.cbl"
    cobol_file.write_text('''
       IDENTIFICATION DIVISION.
       PROGRAM-ID. HELLO-WORLD.
       PROCEDURE DIVISION.
       100-MAIN-LOGIC.
           DISPLAY "Starting main process".
           PERFORM 200-CALCULATE-TAX.
           STOP RUN.
           
       200-CALCULATE-TAX.
           DISPLAY "Calculating tax logic here".
           COMPUTE TOTAL-TAX = SUB-TOTAL * 0.15.
    ''')
    
    # Run the fallback builder looking for '200-CALCULATE-TAX'
    try:
        context = build_fallback_context('200-CALCULATE-TAX', [str(cobol_file)], max_chars=100)
        print("SUCCESS! Context extracted:")
        print(context['target_code_stripped'])
    except Exception as e:
        print(f"FAILED: {e}")
