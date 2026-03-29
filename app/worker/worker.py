import asyncio
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict

from sqlalchemy import select

from app.core.config import settings
from app.db.models.jobs import Job
from app.db.models.job_events import JobEvent
from app.db.models.job_results import JobResult
from app.db.models.financial_data import FinancialData

logger = logging.getLogger(__name__)


async def _add_event(
    db, *, job_id, event_type: str, message: str | None = None
) -> JobEvent:
    ev = JobEvent(job_id=job_id, type=event_type, message=message)
    db.add(ev)
    await db.commit()
    await db.refresh(ev)
    return ev


async def handle_job_message(payload: Dict[str, Any]) -> None:
    """Business logic for a single RabbitMQ message.

    Expected payload: {"job_id": "...", "user_id": "..."}
    """
    job_id = payload.get("job_id")
    user_id = payload.get("user_id")
    if not job_id or not user_id:
        logger.warning("Invalid payload: %s", payload)
        return

    # Lazy import so importing this module doesn't require DB drivers
    from app.db.engine import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        job = await db.get(Job, job_id)
        if not job:
            logger.warning("Job not found: %s", job_id)
            return
        if str(job.user_id) != str(user_id):
            logger.warning(
                "User mismatch for job %s: payload user_id=%s", job_id, user_id
            )
            return

        try:
            # Mark as STARTED
            job.status = "STARTED"
            job.started_at = datetime.now(timezone.utc)
            db.add(job)
            await db.commit()
            await db.refresh(job)
            await _add_event(
                db,
                job_id=job.id,
                event_type="STARTED",
                message="Job processing started",
            )

            # === Expense analysis: group FinancialData by category and sum amounts ===
            q = select(FinancialData).where(FinancialData.user_id == job.user_id)
            resp = await db.execute(q)
            rows = resp.scalars().all()

            totals: Dict[str, Decimal] = {}
            for r in rows:
                # optionally analyze only expenses
                if str(getattr(r, "type", "")).lower() not in {"expense", "expenses"}:
                    continue
                totals[r.category] = totals.get(r.category, Decimal("0")) + (
                    r.amount or Decimal("0")
                )

            analysis = {
                "by_category": {
                    k: str(v)
                    for k, v in sorted(totals.items(), key=lambda x: (-x[1], x[0]))
                },
                "total_expense": str(sum(totals.values(), Decimal("0"))),
            }

            # Upsert JobResult for this job
            existing_q = select(JobResult).where(JobResult.job_id == job.id)
            existing_resp = await db.execute(existing_q)
            existing = existing_resp.scalars().first()
            if existing:
                existing.result_type = "expense_analysis"
                existing.result_data = analysis
                db.add(existing)
            else:
                db.add(
                    JobResult(
                        job_id=job.id,
                        result_type="expense_analysis",
                        result_data=analysis,
                    )
                )
            await db.commit()

            await _add_event(
                db,
                job_id=job.id,
                event_type="RESULT",
                message="Expense analysis stored",
            )

            # Mark as COMPLETED
            job.status = "COMPLETED"
            job.completed_at = datetime.now(timezone.utc)
            db.add(job)
            await db.commit()
            await db.refresh(job)
            await _add_event(
                db,
                job_id=job.id,
                event_type="COMPLETED",
                message="Job processing completed",
            )

        except Exception as e:
            # Mark as ERROR + store event
            try:
                job.status = "ERROR"
                db.add(job)
                await db.commit()
                await _add_event(db, job_id=job.id, event_type="ERROR", message=str(e))
            except Exception:
                logger.exception("Failed to store error state")
            logger.exception("Job processing failed")


async def run_worker() -> None:
    """RabbitMQ consumer loop using aio-pika."""
    try:
        import aio_pika  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "aio-pika is required to run the worker. Install: pip install aio-pika"
        ) from e

    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            settings.RABBITMQ_EXCHANGE, aio_pika.ExchangeType.FANOUT
        )

        # Exclusive auto-delete queue for this worker instance
        queue = await channel.declare_queue("", exclusive=True)
        await queue.bind(exchange)

        logger.info(
            "Worker started. Waiting for messages on exchange '%s'...",
            settings.RABBITMQ_EXCHANGE,
        )

        async with queue.iterator() as qiterator:
            async for message in qiterator:
                async with message.process():
                    try:
                        payload = json.loads(message.body.decode())
                    except Exception:
                        logger.exception("Failed to decode message")
                        continue

                    try:
                        await handle_job_message(payload)
                    except Exception:
                        logger.exception("Failed to handle message: %s", payload)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
