from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class MessageResponse(BaseModel):
    role: str
    content: str


class MessageCreate(BaseModel):
    session_id: str
    history: list[MessageResponse]
    role: str  # user|assistant
    content: str


# Chart data schemas
class ChartData(BaseModel):
    labels: List[str]
    datasets: List[Dict[str, Any]]


class ChartConfig(BaseModel):
    type: str  # 'bar', 'line', 'pie', 'scatter', 'doughnut'
    title: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


class ChartResponse(BaseModel):
    chart_data: ChartData
    chart_config: ChartConfig
    description: Optional[str] = None

