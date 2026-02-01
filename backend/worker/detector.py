from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared import Metric, Alert

THRESHOLDS = {
    "cpu_percent": {"warning": 70, "critical": 90},
    "memory_percent": {"warning": 75, "critical": 90},
    "disk_percent": {"warning": 80, "critical": 95},
}


async def check_thresholds(metric: Metric, session: AsyncSession) -> list[Alert]:
    alerts = []

    for metric_type, levels in THRESHOLDS.items():
        value = getattr(metric, metric_type)
        if value is None:
            continue

        severity = None
        if value >= levels["critical"]:
            severity = "critical"
        elif value >= levels["warning"]:
            severity = "warning"

        if severity:
            existing = await session.execute(
                select(Alert)
                .where(Alert.host == metric.host)
                .where(Alert.metric_type == metric_type)
                .where(Alert.status == "pending")
            )
            if existing.scalar():
                continue

            alert = Alert(
                timestamp=datetime.now(timezone.utc),
                host=metric.host,
                metric_type=metric_type,
                severity=severity,
                message=f"{metric_type} is {value:.1f}% on {metric.host}",
                status="pending",
            )
            alerts.append(alert)

    return alerts
