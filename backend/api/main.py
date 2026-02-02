from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared import get_session, Metric, Alert, publish_metric
from .schemas import MetricCreate, MetricResponse, AlertResponse, AlertUpdate

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
    await publish_metric(db_metric.host, db_metric.timestamp.isoformat())
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


@app.get("/alerts", response_model=list[AlertResponse])
async def get_alerts(
    host: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    session: AsyncSession = Depends(get_session),
):
    query = select(Alert).order_by(Alert.timestamp.desc()).limit(limit)

    if host:
        query = query.where(Alert.host == host)
    if severity:
        query = query.where(Alert.severity == severity)
    if status:
        query = query.where(Alert.status == status)

    result = await session.execute(query)
    return result.scalars().all()


@app.patch("/alerts/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    update: AlertUpdate,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = update.status
    await session.commit()
    await session.refresh(alert)
    return alert
