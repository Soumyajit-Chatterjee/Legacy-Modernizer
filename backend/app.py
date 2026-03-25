from dotenv import load_dotenv
load_dotenv(".env.local")
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.parser import parser, find_method_declarations
from backend.context_optimizer import build_optimized_context, get_method_name
from backend.llm_client import generate_modernized_code
from backend.orchestrator import orchestrate_github_modernization
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ModernizeRequest(BaseModel):
    legacy_code: str
    target_function: str
    target_lang: str

@app.post("/api/modernize")
def modernize(request: ModernizeRequest):
    code_bytes = request.legacy_code.encode("utf-8")
    
    try:
        tree = parser.parse(code_bytes)
        methods = find_method_declarations(tree.root_node)
        all_method_nodes = {}
        for m in methods:
            name = get_method_name(m, code_bytes)
            all_method_nodes[name] = (m, code_bytes)
            
        context = build_optimized_context(request.target_function, all_method_nodes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parsing error: {e}")
        
    try:
        response_text = generate_modernized_code(context, request.target_lang)
        clean_json = response_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        return {"modernized_code": data.get("modernized_code", ""), "unit_tests": data.get("unit_tests", "")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Error/Parsing JSON: {e}")

class GithubModernizeRequest(BaseModel):
    github_url: str
    target_function: str
    target_lang: str

@app.post("/api/modernize/github")
def modernize_from_github(request: GithubModernizeRequest):
    try:
        data = orchestrate_github_modernization(request.github_url, request.target_lang, request.target_function)
        return {"modernized_code": data.get("modernized_code", ""), "unit_tests": data.get("unit_tests", "")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
