import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import select

from shared import AsyncSessionLocal, Metric
from .detector import check_thresholds

POLL_INTERVAL = 10


async def process_metrics():
    async with AsyncSessionLocal() as session:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=POLL_INTERVAL * 2)
        result = await session.execute(
            select(Metric).where(Metric.timestamp >= cutoff)
        )
        metrics = result.scalars().all()

        for metric in metrics:
            alerts = await check_thresholds(metric, session)
            for alert in alerts:
                session.add(alert)
                print(f"[ALERT] {alert.severity}: {alert.message}")

        await session.commit()


async def run():
    print("Starting Analysis Worker...")
    while True:
        try:
            await process_metrics()
        except Exception as e:
            print(f"Error: {e}")
        await asyncio.sleep(POLL_INTERVAL)


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
