import json
import logging

logger = logging.getLogger(__name__)

# Try to import aio_pika; if unavailable, provide a noop function
try:
    import aio_pika
    AIO_PIKA_AVAILABLE = True
except Exception:
    AIO_PIKA_AVAILABLE = False


async def send_job_message(message: dict):
    """Send a job message to RabbitMQ if aio-pika is available and RABBIT_URL env var set.
    Falls back to logging if not configured.
    """
    if not AIO_PIKA_AVAILABLE:
        logger.info("aio-pika not installed; would send message: %s", message)
        return

    from app.core.config import settings
    rabbit_url = getattr(settings, "RABBITMQ_URL", None)
    if not rabbit_url:
        logger.info("RABBITMQ_URL not configured; message: %s", message)
        return

    try:
        connection = await aio_pika.connect_robust(rabbit_url)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange("jobs", aio_pika.ExchangeType.FANOUT)
            await exchange.publish(aio_pika.Message(body=json.dumps(message).encode()), routing_key="")
    except Exception:
        logger.exception("Failed to publish RabbitMQ message")
