import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    import aio_pika
    AIO_PIKA_AVAILABLE = True
except ImportError:
    AIO_PIKA_AVAILABLE = False

async def get_rabbit_connection():
    if not AIO_PIKA_AVAILABLE:
        raise RuntimeError("aio-pika is not installed")
    return await aio_pika.connect_robust(settings.RABBITMQ_URL)

async def publish_ui_event(event: dict):
    if not AIO_PIKA_AVAILABLE:
        logger.warning("aio-pika not available, cannot send UI event.")
        return

    try:
        connection = await get_rabbit_connection()
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                "ui_events", aio_pika.ExchangeType.FANOUT
            )
            await exchange.publish(
                aio_pika.Message(body=json.dumps(event).encode()), routing_key=""
            )
    except Exception:
        logger.exception("Failed to publish UI event to RabbitMQ")


async def send_job_message(message: dict):
    """Send a job message to RabbitMQ if aio-pika is available and RABBIT_URL env var set."""
    if not AIO_PIKA_AVAILABLE:
        logger.warning("aio-pika not installed; cannot send job message.")
        return

    try:
        connection = await get_rabbit_connection()
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                settings.RABBITMQ_EXCHANGE, aio_pika.ExchangeType.FANOUT
            )
            await exchange.publish(
                aio_pika.Message(body=json.dumps(message).encode()), routing_key=""
            )
    except Exception:
        logger.exception("Failed to publish RabbitMQ message")
