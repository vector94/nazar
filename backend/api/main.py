from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import FastAPI, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared import get_session, Metric
from .schemas import MetricCreate, MetricResponse

app = FastAPI(
    title="Nazar API",
    description="Performance monitoring platform API",
    version="0.1.0"
)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/metrics")
async def ingest_metric(metric: MetricCreate, session: AsyncSession = Depends(get_session)):
    db_metric = Metric(
        timestamp=metric.timestamp or datetime.now(timezone.utc),
        host=metric.host,
        cpu_percent=metric.cpu_percent,
        memory_percent=metric.memory_percent,
        disk_percent=metric.disk_percent,
        network_in=metric.network_in,
        network_out=metric.network_out,
    )
    session.add(db_metric)
    await session.commit()
    return {"status": "ok"}


@app.get("/metrics", response_model=list[MetricResponse])
async def get_metrics(
    host: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = Query(default=100, le=1000),
    session: AsyncSession = Depends(get_session),
):
    query = select(Metric).order_by(Metric.timestamp.desc()).limit(limit)

    if host:
        query = query.where(Metric.host == host)
    if start:
        query = query.where(Metric.timestamp >= start)
    if end:
        query = query.where(Metric.timestamp <= end)

    result = await session.execute(query)
    return result.scalars().all()
