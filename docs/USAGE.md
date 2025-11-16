# Frontend Usage & Best Practices

This file explains how to use the frontend and how to write effective queries for chart generation.

Serving the frontend

- Serve the repository root using a static server (recommended to avoid CORS issues):

```powershell
cd E:\chart-generator-backend
python -m http.server 8080
# Open http://localhost:8080/index.html
```

Basic workflow

1. Upload your dataset in CSV / JSON / XLSX form using the upload card.
2. Describe the chart you want in plain English in the textarea (examples below).
3. Click "Generate Chart" and wait for the model to parse and the chart to be created.
4. Download as PNG/JPG/PDF or copy the JSON of the generated chart.

Tips for better natural-language queries

- Be explicit about the axes and aggregation: "Bar chart of average salary by department".
- For filters, state them clearly: "... for company_location = 'US' and salary_in_usd > 50000".
- If you want color grouping: "Color by department" or "group by department".
- Avoid overly ambiguous terms like "distribution" without specifying whether you want a histogram or box plot.

Sample queries

- "Show a bar chart of average closing price for each stock symbol"
- "Create a scatter plot of salary_in_usd vs experience_years filtered to company_location = 'US'"
- "Display a histogram of salary_in_usd with 30 bins"
- "Plot a line chart of daily sales over time grouped by region"

Troubleshooting

- CORS: If the browser blocks requests, add the frontend origin to the backend's allowed origins in `config.py` (for example `http://localhost:8080`).
- Large files: The frontend enforces a 50MB upload limit. If you need larger uploads, modify the frontend limit and ensure the backend can accept larger request bodies.
- Unexpected LLM outputs: The backend normalizes many LLM response variations but you may still see parsing issues. Inspect server logs (or enable extra logging in `services/llm_handler.py`) to view raw LLM responses.
