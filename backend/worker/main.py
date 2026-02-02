import asyncio
import json
from datetime import datetime
from aio_pika import connect_robust
from aio_pika.abc import AbstractIncomingMessage
from sqlalchemy import select

from shared import AsyncSessionLocal, Metric, QUEUE_NAME
from shared.config import RABBITMQ_URL
from .detector import check_thresholds
from .ml_detector import check_ml_anomaly


async def process_message(message: AbstractIncomingMessage):
    async with message.process():
        data = json.loads(message.body.decode())
        host = data["host"]
        timestamp = datetime.fromisoformat(data["timestamp"])

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Metric)
                .where(Metric.host == host)
                .where(Metric.timestamp == timestamp)
            )
            metric = result.scalar()

            if not metric:
                print(f"Metric not found: {host} @ {timestamp}")
                return

            # Check threshold-based alerts
            alerts = await check_thresholds(metric, session)
            for alert in alerts:
                session.add(alert)
                print(f"[ALERT] {alert.severity}: {alert.message}")

            # Check ML-based anomalies
            ml_alert = await check_ml_anomaly(metric, session)
            if ml_alert:
                session.add(ml_alert)
                print(f"[ML-ALERT] {ml_alert.severity}: {ml_alert.message}")

            await session.commit()


async def run():
    print("Starting Analysis Worker...")
    connection = await connect_robust(RABBITMQ_URL)

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        queue = await channel.declare_queue(QUEUE_NAME, durable=True)
        print(f"Listening on queue: {QUEUE_NAME}")

        await queue.consume(process_message)
        await asyncio.Future()


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()