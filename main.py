from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
import json

from app.core.errors import (
    RequestIdMiddleware,
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)
from app.core.config import settings

app = FastAPI()

# request id + consistent JSON errors
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

# IMPORTANT: frontend (prod via nginx and dev via Vite) calls /api/*
API_PREFIX = "/api"

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
import logging
import socket
from urllib.parse import urlparse


@app.websocket(f"{API_PREFIX}/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    user = await get_user_from_token(token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws_manager.connect(websocket, str(user.id))
    try:
        while True:
            # Keep the connection alive
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

@app.on_event("startup")
async def startup_event():
    # Start background consumers only if RabbitMQ is available. This avoids
    # leaving pending tasks when RabbitMQ is down during local dev.
    rabbit_ok = False
    try:
        if AIO_PIKA_AVAILABLE and getattr(aio_pika, "ExchangeType", None) is not None:
            # Parse host and port from RABBITMQ_URL
            parsed = urlparse(settings.RABBITMQ_URL)
            host = parsed.hostname or "localhost"
            port = parsed.port or 5672
            # quick TCP check with short timeout using thread executor
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: socket.create_connection((host, port), timeout=2).close(),
            )
            rabbit_ok = True
    except Exception:
        rabbit_ok = False

    if rabbit_ok:
        logging.info("RabbitMQ accessible — starting background consumers")
        asyncio.create_task(consume_ui_events())
        asyncio.create_task(consume_job_events())
    else:
        logging.warning("RabbitMQ not available — skipping background consumers (UI events, job events).")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
