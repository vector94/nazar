from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared import Metric, Alert
from .notifier import send_slack_alert

THRESHOLDS = {
    "cpu_percent": {"warning": 70, "critical": 90},
    "memory_percent": {"warning": 75, "critical": 90},
    "disk_percent": {"warning": 80, "critical": 95},
}

SEVERITY_RANK = {"warning": 1, "critical": 2}
OPEN_STATUSES = ["pending", "acknowledged"]


def resolve_alerts(alerts: list[Alert]) -> None:
    for alert in alerts:
        alert.status = "resolved"


async def check_thresholds(metric: Metric, session: AsyncSession) -> list[Alert]:
    result = await session.execute(
        select(Alert)
        .where(Alert.host == metric.host)
        .where(Alert.metric_type.in_(list(THRESHOLDS.keys())))
        .where(Alert.status.in_(OPEN_STATUSES))
    )
    open_alerts = result.scalars().all()
    new_alerts: list[Alert] = []

    for metric_type, levels in THRESHOLDS.items():
        prefix = metric_type.split("_")[0]
        max_val = getattr(metric, f"{prefix}_max", None)
        value = max_val if max_val is not None else getattr(metric, metric_type)
        if value is None:
            continue

        severity = None
        if value >= levels["critical"]:
            severity = "critical"
        elif value >= levels["warning"]:
            severity = "warning"

        open_metric_alerts: list[Alert] = []
        highest_open_rank = 0
        for open_alert in open_alerts:
            if open_alert.metric_type == metric_type:
                open_metric_alerts.append(open_alert)
                highest_open_rank = max(highest_open_rank, SEVERITY_RANK[open_alert.severity])

        if severity is None:
            resolve_alerts(open_metric_alerts)
            continue

        if highest_open_rank >= SEVERITY_RANK[severity]:
            continue

        resolve_alerts(open_metric_alerts)

        message = f"{metric_type} is {value:.1f}% on {metric.host}"
        alert = Alert(
            timestamp=datetime.now(timezone.utc),
            host=metric.host,
            metric_type=metric_type,
            severity=severity,
            message=message,
            status="pending",
        )
        new_alerts.append(alert)
        await send_slack_alert(severity, message)

    return new_alerts
