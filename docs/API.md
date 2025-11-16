# API Documentation

This file documents the server endpoints used by the frontend.

Base URL

- Default: `http://localhost:8000`

Endpoints

1. POST /api/data/upload/{session_id}

- Purpose: Upload dataset for a session
- Path parameter: `session_id` (string)
- Body: multipart/form-data with `file` field (CSV, JSON, or XLSX)
- Response (200):
  {
  "row_count": 123,
  "column_count": 5,
  "columns": ["col1","col2",...],
  "metadata": { /_ optional _/ }
  }

Errors:

- 400/422 may be returned for invalid file types or parsing errors.

2. POST /api/charts/generate/{session_id}

- Purpose: Generate a Plotly chart for the uploaded dataset for this session
- Body (JSON): `{ "user_query": "<natural language request>" }`
- Response (200):
  {
  "chart_json": { /_ Plotly JSON with `data` and `layout` _/ },
  "chart_spec": { /_ normalized chart specification used to build the chart _/ }
  }

Notes

- The service expects clients to upload a dataset first, then call `/generate` using the same `session_id`.
- `chart_spec` is validated with Pydantic and will contain normalized `filters` in the shape: `[{"column": ..., "operator": ..., "value": ...}, ...]`.

Examples

Upload (curl):

```bash
curl -X POST "http://localhost:8000/api/data/upload/frontend-123456" \
  -F "file=@/path/to/data.csv"
```

Generate (curl):

```bash
curl -X POST "http://localhost:8000/api/charts/generate/frontend-123456" \
  -H "Content-Type: application/json" \
  -d '{"user_query":"Create a scatter of salary_in_usd vs remote_ratio for company_location US"}'
```

Return values are JSON. If using the provided `index.html`, it handles the Plotly rendering client-side using the `chart_json` object.

If you need example contracts for `chart_spec` or `chart_json` shapes, tell me and I can add a small schema section here.
