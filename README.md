# Legacy Modernizer

A developer tool that ingests legacy code repositories (e.g., Java) and intelligently suggests modern Python/Go equivalents using AST parsing and LLM models.

## Features

- **GitHub Ingestion**: Point directly to a public GitHub URL and the engine will seamlessly clone and extract methods.
- **Context Size Optimization (Zero Hallucination Guarantee)**: Implements precise AST parsing via Tree-Sitter to recursively map multi-file function dependencies using a custom BFS search pattern. Distracting code (like comments and bloated lines) is truncated safely when length limits are approached.
- **RESTful Backend**: Built with FastAPI for high-performance generation.
- **Interactive UI**: Clean, aesthetic "Among Us" / dark-mode inspired React dashboard.

## Setup

1. **Clone the Repo**:
   ```bash
   git clone <your-repo>
   cd legacy-modernizer
   ```

2. **Configure API Keys**:
   Copy `.env.example` to `.env` or `.env.local` and add your Gemini API Key safely:
   ```bash
   cp .env.example .env.local
   ```
   > Add your `GEMINI_API_KEY` to the newly created `.env.local` file. It is safely ignored by `.gitignore`.

3. **Install Backend Dependencies**:
   Ensure you have a virtual environment active:
   ```bash
   python -m venv venv
   source venv/bin/activate # Windows: venv\\Scripts\\activate
   pip install fastapi uvicorn pydantic tree-sitter tree-sitter-java google-genai python-dotenv click
   ```

4. **Install Frontend Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

## Running the Application

**1. Start the Backend Server**:
From the project root folder:
```bash
uvicorn backend.app:app --reload
```

**2. Start the Frontend App**:
From the `frontend` directory:
```bash
npm run dev
```

The application is now accessible at `http://localhost:5173`.

## CLI Usage

You can safely run the application headlessly via CLI:

```bash
python cli.py -g "https://github.com/octocat/Hello-World" -f "TargetFunctionName" -l python -o ./output
```

## Architecture

1. `backend/github_ingestor.py` pulls remote repos over SSH/HTTPS into temporary storage.
2. `backend/context_optimizer.py` implements intelligent Graph traversals (`deque`) mapping AST tree method invocations and maintaining byte/character budgets.
3. `backend/app.py` exposes the API.
