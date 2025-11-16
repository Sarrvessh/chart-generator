from fastapi import APIRouter, HTTPException
from models.schemas import ChartGenerationRequest, ChartResponse
from services.data_handler import data_handler
from services.llm_handler import create_llm_handler
from services.chart_generator import chart_generator
from config import settings
from routes.data import active_sessions

router = APIRouter(prefix="/api/charts", tags=["charts"])

@router.post("/generate/{session_id}", response_model=ChartResponse)
async def generate_chart(session_id: str, request: ChartGenerationRequest):
    """Generate chart from natural language query"""

    # Validate session
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]
    df = session['dataframe']
    metadata = session['metadata']

    try:
        # Initialize LLM handler
        llm_handler = create_llm_handler(
            endpoint=settings.LLM_ENDPOINT,
            api_key=settings.LLM_API_KEY,
            model=settings.LLM_MODEL
        )

        # Parse user query and get chart specification
        chart_spec = await llm_handler.parse_user_request(request.user_query, metadata)

        # Validate specification against data
        for col_name in [chart_spec.get('x_axis'), chart_spec.get('y_axis'), chart_spec.get('color_by')]:
            if col_name and col_name not in df.columns:
                raise ValueError(f"Column '{col_name}' not found in data")

        # Generate the chart
        result = await chart_generator.generate_chart(df, chart_spec)

        # Validate/serialize into the Pydantic response model to ensure proper shape
        return ChartResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating chart: {str(e)}")

@router.get("/supported-types")
async def get_supported_chart_types():
    """Get list of supported chart types"""
    return {
        "chart_types": [
            "bar", "line", "scatter", "pie", "heatmap", "area", "histogram", "box"
        ],
        "aggregations": ["sum", "mean", "count", "min", "max", "none"],
        "color_schemes": ["default", "viridis", "plasma", "coolwarm"]
    }
