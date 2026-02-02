import json
from typing import Optional
from aio_pika import connect_robust, Message
from aio_pika.abc import AbstractRobustConnection, AbstractChannel

from .config import RABBITMQ_URL

QUEUE_NAME = "metrics"

_connection: Optional[AbstractRobustConnection] = None
_channel: Optional[AbstractChannel] = None


async def get_channel() -> AbstractChannel:
    global _connection, _channel

    if _connection is None or _connection.is_closed:
        _connection = await connect_robust(RABBITMQ_URL)

    if _channel is None or _channel.is_closed:
        _channel = await _connection.channel()
        await _channel.declare_queue(QUEUE_NAME, durable=True)

    return _channel


async def publish_metric(host: str, timestamp: str):
    channel = await get_channel()
    message = Message(
        body=json.dumps({"host": host, "timestamp": timestamp}).encode(),
        content_type="application/json",
    )
    await channel.default_exchange.publish(message, routing_key=QUEUE_NAME)


async def close_connection():
    global _connection, _channel
    if _channel:
        await _channel.close()
        _channel = None
    if _connection:
        await _connection.close()
        _connection = None