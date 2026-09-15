"""API request and response schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class QueryRequest(BaseModel):
    """Query request schema."""
    query: str = Field(..., description="User's natural language query")
    model_id: Optional[str] = Field(None, description="Model ID to use")
    include_viz: bool = Field(True, description="Include visualization")
    max_retries: int = Field(2, ge=0, le=5, description="Max retry attempts")


class QueryResponse(BaseModel):
    """Query response schema."""
    query_id: str = Field(..., description="Unique query ID")
    sql: str = Field(..., description="Generated SQL query")
    data: List[Dict[str, Any]] = Field(..., description="Query results")
    visualization: Optional[Dict[str, Any]] = Field(None, description="Vega-Lite specification")
    intent: Dict[str, Any] = Field(..., description="Extracted intent")
    metadata: Dict[str, Any] = Field(..., description="Query metadata")


class TrainRequest(BaseModel):
    """Training request schema."""
    database_url: str = Field(..., description="Database connection URL")
    business_docs: List[str] = Field(..., description="Business rule document paths")
    model_name: str = Field("Qwen/Qwen2.5-Coder-7B", description="Base model name")
    config: Optional[Dict[str, Any]] = Field(None, description="Training configuration")


class TrainResponse(BaseModel):
    """Training response schema."""
    model_id: str = Field(..., description="Model ID")
    status: str = Field(..., description="Training status")
    metrics: Dict[str, Any] = Field(..., description="Training metrics")


class ModelInfo(BaseModel):
    """Model information schema."""
    id: str = Field(..., description="Model ID")
    name: str = Field(..., description="Model name")
    version: str = Field(..., description="Model version")
    created_at: datetime = Field(..., description="Creation timestamp")
    path: str = Field(..., description="Model path")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Overall status")
    timestamp: datetime = Field(..., description="Check timestamp")
    services: Dict[str, str] = Field(..., description="Service statuses")