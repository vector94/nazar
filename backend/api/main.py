from datetime import datetime, timezone
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared import get_session, Metric
from .schemas import MetricCreate

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
