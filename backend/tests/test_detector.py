from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared import Alert, Metric
from worker import detector


class FakeSlack:
    def __init__(self) -> None:
        self.sent: list[str] = []

    async def send(self, severity: str, message: str) -> None:
        self.sent.append(severity)


@pytest.fixture
def slack(monkeypatch: pytest.MonkeyPatch) -> FakeSlack:
    fake = FakeSlack()
    monkeypatch.setattr(detector, "send_slack_alert", fake.send)
    return fake


async def process_metric(session: AsyncSession, cpu: float) -> None:
    metric = Metric(
        timestamp=datetime.now(timezone.utc),
        host="web-1",
        cpu_percent=cpu,
        cpu_max=cpu,
        memory_percent=40.0,
        memory_max=40.0,
        disk_percent=30.0,
        disk_max=30.0,
    )
    new_alerts = await detector.check_thresholds(metric, session)
    session.add_all(new_alerts)
    await session.commit()


async def acknowledge(session: AsyncSession) -> None:
    result = await session.execute(select(Alert))
    alert = result.scalar_one()
    alert.status = "acknowledged"
    await session.commit()


async def load_alerts(session: AsyncSession) -> list[tuple[str, str, str]]:
    result = await session.execute(
        select(Alert.metric_type, Alert.severity, Alert.status).order_by(Alert.id)
    )
    rows: list[tuple[str, str, str]] = []
    for metric_type, severity, status in result:
        rows.append((metric_type, severity, status))
    return rows


async def test_repeated_breach_does_not_raise_again(session: AsyncSession, slack: FakeSlack):
    await process_metric(session, cpu=75)
    await process_metric(session, cpu=80)

    assert await load_alerts(session) == [("cpu_percent", "warning", "pending")]
    assert slack.sent == ["warning"]


async def test_escalation_to_critical_raises_critical(session: AsyncSession, slack: FakeSlack):
    await process_metric(session, cpu=75)
    await process_metric(session, cpu=97)

    assert await load_alerts(session) == [
        ("cpu_percent", "warning", "resolved"),
        ("cpu_percent", "critical", "pending"),
    ]
    assert slack.sent == ["warning", "critical"]


async def test_deescalation_keeps_critical_open(session: AsyncSession, slack: FakeSlack):
    await process_metric(session, cpu=97)
    await process_metric(session, cpu=75)

    assert await load_alerts(session) == [("cpu_percent", "critical", "pending")]
    assert slack.sent == ["critical"]


async def test_breach_after_recovery_raises_again(session: AsyncSession, slack: FakeSlack):
    await process_metric(session, cpu=75)
    await process_metric(session, cpu=30)
    await process_metric(session, cpu=80)

    assert await load_alerts(session) == [
        ("cpu_percent", "warning", "resolved"),
        ("cpu_percent", "warning", "pending"),
    ]
    assert slack.sent == ["warning", "warning"]


async def test_acknowledged_alert_is_not_raised_again(session: AsyncSession, slack: FakeSlack):
    await process_metric(session, cpu=75)
    await acknowledge(session)
    await process_metric(session, cpu=80)

    assert await load_alerts(session) == [("cpu_percent", "warning", "acknowledged")]
    assert slack.sent == ["warning"]
