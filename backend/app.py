from dotenv import load_dotenv
load_dotenv(".env.local")
load_dotenv()

from pathlib import Path
import os
import shutil
import subprocess

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import FileResponse
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
    
    context = None
    java_exc: Exception | None = None
    try:
        # Import Java parsing components lazily so COBOL fallback can work even
        # if tree-sitter Java dependencies are missing.
        from backend.parser import parse_code, find_method_declarations
        from backend.context_optimizer import build_optimized_context, get_method_name

        root_node = parse_code(code_bytes)
        methods = find_method_declarations(root_node)
        all_method_nodes = {}
        for m in methods:
            name = get_method_name(m, code_bytes)
            all_method_nodes[name] = (m, code_bytes)

        context = build_optimized_context(request.target_function, all_method_nodes)
    except Exception as e:
        java_exc = e

    # If Java path didn't produce a context, attempt COBOL/regex fallback.
    if context is None:
        from backend.fallback_parser import build_fallback_context_from_text

        try:
            context = build_fallback_context_from_text(
                target_function=request.target_function,
                content=request.legacy_code,
            )
        except ValueError as fallback_err:
            # Prefer fallback error (usually "target not found in provided code"),
            # but include the Java parsing reason for debugging.
            detail = str(fallback_err)
            if java_exc is not None:
                detail = f"{detail}. (Java parse error: {java_exc})"
            raise HTTPException(status_code=400, detail=detail)
        except Exception as fallback_exc:
            raise HTTPException(
                status_code=500,
                detail=f"Java parse failed and fallback failed: {java_exc}; fallback error: {fallback_exc}",
            )
        
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

def _frontend_index_path() -> Path:
    return FRONTEND_DIST_DIR / "index.html"


def ensure_frontend_built() -> None:
    """
    Ensure the Vite production bundle exists.

    In a correctly configured Docker build, this should already be present.
    If the service was deployed without building the frontend, we try to build
    it on-demand (only if `npm` is available).
    """
    if _frontend_index_path().is_file():
        return

    npm_path = shutil.which("npm")
    if not npm_path:
        raise RuntimeError("Frontend not built and `npm` is not available in this environment.")

    frontend_dir = BASE_DIR / "frontend"
    if not (frontend_dir / "package.json").is_file():
        raise RuntimeError("Frontend source not found in expected location.")

    # Build frontend bundle in place.
    # Note: this is best-effort; if it fails, we surface a clear 503 message.
    subprocess.run(
        ["npm", "ci"],
        cwd=str(frontend_dir),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    subprocess.run(
        ["npm", "run", "build"],
        cwd=str(frontend_dir),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


@app.get("/", include_in_schema=False)
def serve_frontend_root():
    index_path = FRONTEND_DIST_DIR / "index.html"
    if not index_path.is_file():
        try:
            ensure_frontend_built()
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))
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

    try:
        ensure_frontend_built()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

    # After build, index.html should exist.
    if index_path.is_file():
        return FileResponse(index_path)

    raise HTTPException(status_code=503, detail="Frontend build completed but index.html is still missing.")
