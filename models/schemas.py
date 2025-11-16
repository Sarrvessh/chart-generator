from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum

class ChartType(str, Enum):
    """Supported chart types"""
    BAR = "bar"
    LINE = "line"
    SCATTER = "scatter"
    PIE = "pie"
    HEATMAP = "heatmap"
    AREA = "area"
    HISTOGRAM = "histogram"
    BOX = "box"

class Aggregation(str, Enum):
    """Supported aggregations"""
    SUM = "sum"
    MEAN = "mean"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    NONE = "none"

class ColorScheme(str, Enum):
    """Available color schemes"""
    DEFAULT = "default"
    VIRIDIS = "viridis"
    PLASMA = "plasma"
    COOLWARM = "coolwarm"

class DataMetadata(BaseModel):
    """Metadata about uploaded data"""
    columns: List[str]
    dtypes: Dict[str, str]
    numerical_columns: List[str]
    categorical_columns: List[str]
    datetime_columns: List[str]
    row_count: int
    summary_stats: Dict[str, Any]

class FilterSpec(BaseModel):
    """Single filter specification"""
    column: str
    operator: str = Field(..., description="==, >, <, >=, <=, !=")
    value: Any

class Customization(BaseModel):
    """Chart customization options"""
    color_scheme: ColorScheme = ColorScheme.DEFAULT
    show_legend: bool = True
    data_labels: bool = False

class ChartSpecification(BaseModel):
    """Complete chart specification"""
    chart_type: ChartType
    x_axis: str
    y_axis: Optional[str] = None
    color_by: Optional[str] = None
    aggregation: Optional[Aggregation] = Aggregation.NONE
    filters: Optional[List[FilterSpec]] = None
    title: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    customization: Optional[Customization] = None

    @validator('x_axis')
    def x_axis_required(cls, v):
        if not v:
            raise ValueError('x_axis is required')
        return v

class ChartGenerationRequest(BaseModel):
    """Request to generate chart from natural language"""
    user_query: str = Field(..., min_length=10, max_length=1000)
    include_spec: bool = True

class UploadResponse(BaseModel):
    """Response after file upload"""
    session_id: str
    filename: str
    row_count: int
    column_count: int
    columns: List[str]
    metadata: DataMetadata

class ChartResponse(BaseModel):
    """Response with generated chart"""
    chart_spec: ChartSpecification
    chart_html: str
    chart_json: Dict[str, Any]
