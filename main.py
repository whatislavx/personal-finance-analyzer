from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
import json
import logging

from app.core.errors import (
    RequestIdMiddleware,
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)
from app.core.config import settings

app = FastAPI(title="Personal Finance Analyzer API")
logger = logging.getLogger(__name__)

# Request ID + consistent JSON errors
app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# CORS middleware - allow common dev frontend origins; adjust in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "*",  # Дозволяємо доступ всередині кластера (буде контролюватись Ingress)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers from the app.api package
from app.api import (
    auth_router,
    users_router,
    jobs_router,
    job_events_router,
    job_results_router,
    financial_data_router,
)

# IMPORTANT: frontend calls /api/*
API_PREFIX = "/api"

# КУБЕРНЕТЕС HEALTH CHECKS
@app.get("/healthz", status_code=status.HTTP_200_OK)
async def liveness_probe():
    return {"status": "healthy"}

@app.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_probe():
    try:
        from sqlalchemy import text
        from app.db.engine import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Readiness check failed: database is unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is not ready: database is unavailable.",
        )

    return {
        "status": "ready",
        "dependencies": {
            "database": "ok",
        },
    }


app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)
app.include_router(jobs_router, prefix=API_PREFIX)
app.include_router(job_events_router, prefix=API_PREFIX)
app.include_router(job_results_router, prefix=API_PREFIX)
app.include_router(financial_data_router, prefix=API_PREFIX)

from app.core.ws import ws_manager
from app.core.auth import get_user_from_token
from app.core.rabbit import get_rabbit_connection, AIO_PIKA_AVAILABLE
import aio_pika
import asyncio
import socket
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

@app.websocket(f"{API_PREFIX}/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    user = await get_user_from_token(token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws_manager.connect(websocket, str(user.id))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, str(user.id))


async def consume_ui_events():
    """Listen for UI events from RabbitMQ and push to WebSockets."""
    connection = await get_rabbit_connection()
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            "ui_events", aio_pika.ExchangeType.FANOUT
        )
        queue = await channel.declare_queue("", exclusive=True)
        await queue.bind(exchange)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        data = json.loads(message.body.decode())
                        user_id = data.get("user_id")
                        if user_id:
                            await ws_manager.broadcast_to_user(user_id, data)
                    except Exception as e:
                        logging.error(f"Failed to process UI event: {e}")


from app.api.jobs import consume_job_events

async def start_background_consumers_with_retry():
    parsed = urlparse(settings.RABBITMQ_URL)
    host = parsed.hostname or "localhost"
    port = parsed.port or 5672
    
    max_retries = 15
    retry_delay = 3
    
    logging.info(f"Checking RabbitMQ connectivity on {host}:{port}...")
    
    for attempt in range(1, max_retries + 1):
        try:
            if AIO_PIKA_AVAILABLE and getattr(aio_pika, "ExchangeType", None) is not None:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None,
                    lambda: socket.create_connection((host, port), timeout=2).close(),
                )
                logging.info("RabbitMQ is accessible! Starting background consumers...")
                asyncio.create_task(consume_ui_events())
                asyncio.create_task(consume_job_events())
                return
        except Exception as e:
            logging.warning(f"[Attempt {attempt}/{max_retries}] RabbitMQ not ready yet: {e}. Retrying in {retry_delay}s...")
            await asyncio.sleep(retry_delay)
            
    logging.error("Failed to connect to RabbitMQ after multiple attempts. Background consumers skipped.")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_background_consumers_with_retry())


@app.get("/")
async def root():
    return {"message": "Personal Finance Analyzer API is running"}
