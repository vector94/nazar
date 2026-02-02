from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class MetricCreate(BaseModel):
    host: str
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    disk_percent: Optional[float] = None
    network_in: Optional[int] = None
    network_out: Optional[int] = None
    timestamp: Optional[datetime] = None


class MetricResponse(BaseModel):
    timestamp: datetime
    host: str
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    disk_percent: Optional[float] = None
    network_in: Optional[int] = None
    network_out: Optional[int] = None

    class Config:
        from_attributes = True

class AlertResponse(BaseModel):
    id: int
    timestamp: datetime
    host: str
    metric_type: str
    severity: str
    message: Optional[str] = None
    status: str

    class Config:
        from_attributes = True

