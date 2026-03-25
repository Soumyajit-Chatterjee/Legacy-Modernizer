from dotenv import load_dotenv
load_dotenv(".env.local")
load_dotenv()

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import FileResponse
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


# ---- Frontend (Vite/React) static hosting ----
# When deployed with the built frontend present at `frontend/dist`,
# serve it from the same Render service as the API.
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"


@app.get("/", include_in_schema=False)
def serve_frontend_root():
    index_path = FRONTEND_DIST_DIR / "index.html"
    if not index_path.is_file():
        raise HTTPException(
            status_code=503,
            detail="Frontend not built. Run `npm run build --prefix frontend`.",
        )
    return FileResponse(index_path)


@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend_assets_and_spa(full_path: str):
    # Preserve FastAPI routes (/docs, /openapi.json, etc.) and API endpoints.
    if full_path.startswith("api/") or full_path in {"docs", "redoc", "openapi.json"}:
        raise HTTPException(status_code=404, detail="Not Found")

    # If the requested file exists in the built frontend, serve it.
    requested_path = FRONTEND_DIST_DIR / full_path
    if requested_path.is_file():
        return FileResponse(requested_path)

    # SPA fallback: serve index.html for routes handled client-side.
    index_path = FRONTEND_DIST_DIR / "index.html"
    if index_path.is_file():
        return FileResponse(index_path)

    raise HTTPException(
        status_code=503,
        detail="Frontend not built. Run `npm run build --prefix frontend`.",
    )
