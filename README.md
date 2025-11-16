# Chart Generator (AI-powered)

A small FastAPI backend + minimal frontend that uses an LLM to convert natural language requests into Plotly charts. Upload a dataset, ask a question (e.g. "Show a scatter of salary vs experience for US employees"), and the backend generates a Plotly figure which you can view and download.

Features

- Upload CSV / JSON / XLSX datasets (session-scoped)
- Natural-language -> chart specification via an LLM (server-side)
- Plotly charts rendered in the browser
- Download PNG / JPG / PDF (PDF produced client-side by embedding a PNG)
- Robust parsing for LLM outputs and normalized filters

Quick start (development)

1. Create a virtual environment and install dependencies:

```powershell
cd E:\chart-generator-backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run the backend (development):

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

3. Serve the frontend (recommended to avoid file:// CORS issues):

```powershell
# from the project root
python -m http.server 8080
# open http://localhost:8080/index.html in your browser
```

API overview

- POST `/api/data/upload/{session_id}`

  - Form field: `file` (CSV / JSON / XLSX)
  - Returns: `row_count`, `column_count`, `columns`, `metadata`

- POST `/api/charts/generate/{session_id}`
  - JSON body: `{ "user_query": "<natural language query>" }`
  - Returns: `chart_json` (Plotly figure dictionary), `chart_spec` (normalized spec)

Notes & troubleshooting

- Frontend should be served over HTTP/HTTPS (avoid file://). Use `python -m http.server` or any static server.
- If CORS errors appear, ensure `config.py` includes the frontend origin (e.g., `http://localhost:8080`).
- If PDF downloads fail in some browsers, try the PNG/JPG option — the PDF flow embeds a rasterized PNG in a PDF (good cross-browser reliability).

Extending

- The LLM integration lives in `services/llm_handler.py`. The implementation normalizes returned JSON and filters before Pydantic validation.
- Chart creation logic is in `services/chart_generator.py` and uses helper functions to safely prepare and aggregate data.

Development tips

- Keep the backend running with `--reload` while you update the server files.
- For debugging LLM outputs, add temporary logging in `services/llm_handler.py` to view the raw text and parsed JSON.

License

- Add your preferred license here.
