import asyncio
import json
import logging
import io
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

import math

from app.core.s3 import s3_client, build_result_s3_key
from app.core.rabbit import publish_ui_event
from sqlalchemy import select

from app.core.config import settings
from app.db.models.jobs import Job
from app.db.models.job_events import JobEvent
from app.db.models.job_results import JobResult
from app.db.models.financial_data import FinancialData

logger = logging.getLogger(__name__)

_STAGE_DELAY_SECONDS = float(getattr(settings, "WORKER_STAGE_DELAY_SECONDS", 0) or 0)


async def _stage_delay(seconds: float | None = None) -> None:
    s = _STAGE_DELAY_SECONDS if seconds is None else float(seconds)
    if s and s > 0:
        await asyncio.sleep(s)


def _median(values: list[Decimal]) -> Decimal:
    if not values:
        return Decimal("0")
    vs = sorted(values)
    n = len(vs)
    mid = n // 2
    if n % 2 == 1:
        return vs[mid]
    return (vs[mid - 1] + vs[mid]) / Decimal("2")


def _quantile(values: list[Decimal], q: float) -> Decimal:
    """Linear-interpolated quantile for q in [0,1]."""
    if not values:
        return Decimal("0")
    if q <= 0:
        return min(values)
    if q >= 1:
        return max(values)
    vs = sorted(values)
    pos = (len(vs) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return vs[lo]
    frac = Decimal(str(pos - lo))
    return (vs[lo] * (Decimal("1") - frac)) + (vs[hi] * frac)


def _mad(values: list[Decimal], med: Decimal | None = None) -> Decimal:
    if not values:
        return Decimal("0")
    m = med if med is not None else _median(values)
    devs = [abs(v - m) for v in values]
    return _median(devs)


def _robust_zscore(x: Decimal, med: Decimal, mad: Decimal) -> float | None:
    """Return robust z-score using MAD. 0.6745*(x-med)/MAD."""
    if mad is None or mad == 0:
        return None
    return float(Decimal("0.6745") * (x - med) / mad)


async def _add_event(
    db, *, job_id, event_type: str, message: str | None = None, user_id: str
) -> JobEvent:
    ev = JobEvent(job_id=job_id, type=event_type, message=message)
    db.add(ev)
    await db.commit()
    await db.refresh(ev)
    await publish_ui_event({
        "user_id": str(user_id),
        "job_id": str(job_id),
        "event_type": "job_event",
        "payload": {
            "id": str(ev.id),
            "type": ev.type,
            "message": ev.message,
            "created_at": ev.created_at.isoformat(),
        }
    })
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

    logger.info("Handling job message for job_id=%s user_id=%s", job_id, user_id)
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

        if job.status == "COMPLETED":
            existing_q = select(JobResult).where(JobResult.job_id == job.id)
            existing_resp = await db.execute(existing_q)
            if existing_resp.scalars().first() is not None:
                logger.info("Job %s already COMPLETED with result; skipping", job.id)
                return

        try:
            job.status = "STARTED"
            job.started_at = datetime.utcnow()
            db.add(job)
            await db.commit()
            await db.refresh(job)
            await _add_event(
                db,
                job_id=job.id,
                event_type="STARTED",
                message="Job processing started",
                user_id=user_id,
            )
            logger.info("Job %s marked STARTED", job.id)
            await _stage_delay()

            job.status = "PROCESSING"
            db.add(job)
            await db.commit()
            await db.refresh(job)
            await _add_event(
                db,
                job_id=job.id,
                event_type="PROCESSING",
                message="Analysis in progress",
                user_id=user_id,
            )
            logger.info("Job %s marked PROCESSING", job.id)
            await _stage_delay()

            await _add_event(
                db,
                job_id=job.id,
                event_type="INFO",
                message="Loading transactions",
                user_id=user_id,
            )
            await _stage_delay(0.5 if _STAGE_DELAY_SECONDS == 0 else None)

            q = select(FinancialData).where(FinancialData.user_id == job.user_id)
            resp = await db.execute(q)
            rows = resp.scalars().all()

            logger.info("Found %d financial records for user %s", len(rows), job.user_id)

            await _add_event(
                db,
                job_id=job.id,
                event_type="INFO",
                message=f"Processing {len(rows)} transactions",
                user_id=user_id,
            )
            await _stage_delay()

            expense_by_category: Dict[str, Decimal] = {}
            total_expense = Decimal("0")
            total_income = Decimal("0")

            expenses_by_category_amounts: Dict[str, list[Decimal]] = {}
            expenses_rows: list[FinancialData] = []

            for r in rows:
                raw_type = getattr(r, "type", None)
                if raw_type is None:
                    t = ""
                elif hasattr(raw_type, "value"):
                    t = str(raw_type.value).lower()
                else:
                    t = str(raw_type).lower()
                amt = Decimal(str(r.amount)) if r.amount is not None else Decimal("0")

                if t == "income":
                    total_income += amt
                elif t == "expense":
                    total_expense += amt
                    expense_by_category[r.category] = expense_by_category.get(r.category, Decimal("0")) + amt
                    expenses_by_category_amounts.setdefault(r.category, []).append(amt)
                    expenses_rows.append(r)

            await _add_event(
                db,
                job_id=job.id,
                event_type="INFO",
                message="Detecting anomalies",
                user_id=user_id,
            )
            await _stage_delay()


            ANOMALY_MIN_SAMPLES_CATEGORY = 5
            ANOMALY_ZSCORE_THRESHOLD = 3.5
            ANOMALY_CATEGORY_FALLBACK_MIN_SAMPLES = 3
            ANOMALY_CATEGORY_Q = 0.95
            ANOMALY_IQR_K = Decimal("1.5")

            ANOMALY_GLOBAL_MIN_SAMPLES = 10
            ANOMALY_GLOBAL_Q = 0.99

            anomalies: list[dict[str, Any]] = []

            robust_stats: Dict[str, dict[str, Any]] = {}
            for cat, amounts in expenses_by_category_amounts.items():
                if len(amounts) < ANOMALY_MIN_SAMPLES_CATEGORY:
                    continue
                med = _median(amounts)
                mad = _mad(amounts, med)
                robust_stats[cat] = {"median": med, "mad": mad, "n": len(amounts)}

            cat_fallback: Dict[str, dict[str, Any]] = {}
            for cat, amounts in expenses_by_category_amounts.items():
                if len(amounts) < ANOMALY_CATEGORY_FALLBACK_MIN_SAMPLES:
                    continue
                q_hi = _quantile(amounts, ANOMALY_CATEGORY_Q)
                q1 = _quantile(amounts, 0.25)
                q3 = _quantile(amounts, 0.75)
                iqr = q3 - q1
                iqr_hi = q3 + (ANOMALY_IQR_K * iqr)

                threshold = max(q_hi, iqr_hi)
                cat_fallback[cat] = {
                    "threshold": threshold,
                    "q_hi": q_hi,
                    "q": ANOMALY_CATEGORY_Q,
                    "q1": q1,
                    "q3": q3,
                    "iqr": iqr,
                    "iqr_k": str(ANOMALY_IQR_K),
                    "n": len(amounts),
                }

            all_expense_amounts = [
                Decimal(str(r.amount))
                for r in expenses_rows
                if r.amount is not None
            ]
            global_threshold: Decimal | None = None
            if len(all_expense_amounts) >= ANOMALY_GLOBAL_MIN_SAMPLES:
                global_threshold = _quantile(all_expense_amounts, ANOMALY_GLOBAL_Q)

            for r in expenses_rows:
                cat = r.category
                amt = Decimal(str(r.amount)) if r.amount is not None else Decimal("0")

                st = robust_stats.get(cat)
                if st:
                    z = _robust_zscore(amt, st["median"], st["mad"])
                    if z is not None and z > ANOMALY_ZSCORE_THRESHOLD:
                        summary = (
                            f"Unusually large expense in \"{cat}\": ${amt} "
                            f"(typical is around ${st['median']})."
                        )
                        debug = {
                            "kind": "expense",
                            "method": "robust_zscore_mad",
                            "z": z,
                            "threshold": float(ANOMALY_ZSCORE_THRESHOLD),
                            "median": str(st["median"]),
                            "mad": str(st["mad"]),
                            "n": st["n"],
                        }
                        anomalies.append(
                            {
                                "id": str(r.id),
                                "date": str(r.date) if getattr(r, "date", None) is not None else None,
                                "category": cat,
                                "amount": str(amt),
                                "description": r.description,
                                "method": "robust_zscore_mad",
                                "score": z,
                                "summary": summary,
                                "debug": debug,
                            }
                        )
                        await _add_event(db, job_id=job.id, event_type="INFO", message=summary, user_id=user_id)
                        continue

                fb = cat_fallback.get(cat)
                if fb and amt > fb["threshold"]:
                    summary = (
                        f"Unusually large expense in \"{cat}\": ${amt}. "
                        f"This is significantly higher than what's typical for this category."
                    )
                    debug = {
                        "kind": "expense",
                        "method": "category_quantile_iqr",
                        "threshold": str(fb["threshold"]),
                        "q": fb["q"],
                        "q_hi": str(fb["q_hi"]),
                        "q1": str(fb["q1"]),
                        "q3": str(fb["q3"]),
                        "iqr": str(fb["iqr"]),
                        "iqr_k": fb["iqr_k"],
                        "n": fb["n"],
                    }
                    anomalies.append(
                        {
                            "id": str(r.id),
                            "date": str(r.date) if getattr(r, "date", None) is not None else None,
                            "category": cat,
                            "amount": str(amt),
                            "description": r.description,
                            "method": "category_quantile_iqr",
                            "summary": summary,
                            "debug": debug,
                        }
                    )
                    await _add_event(db, job_id=job.id, event_type="INFO", message=summary, user_id=user_id)
                    continue

                if global_threshold is not None and amt > global_threshold:
                    summary = (
                        f"Large expense: ${amt} (one of the biggest expenses in this period)."
                    )
                    debug = {
                        "kind": "expense",
                        "method": "global_quantile",
                        "threshold": str(global_threshold),
                        "quantile": ANOMALY_GLOBAL_Q,
                    }
                    anomalies.append(
                        {
                            "id": str(r.id),
                            "date": str(r.date) if getattr(r, "date", None) is not None else None,
                            "category": cat,
                            "amount": str(amt),
                            "description": r.description,
                            "method": "global_quantile",
                            "summary": summary,
                            "debug": debug,
                        }
                    )
                    await _add_event(db, job_id=job.id, event_type="INFO", message=summary, user_id=user_id)

            analysis = {
                "by_category": {
                    k: str(v)
                    for k, v in sorted(expense_by_category.items(), key=lambda x: (-x[1], x[0]))
                },
                "total_expense": str(total_expense),
                "total_income": str(total_income),
                "net_balance": str(total_income - total_expense),
                "anomalies": anomalies,
                "summary": {
                    "transaction_count": len(rows),
                    "expense_count": len(expenses_rows),
                    "income_count": sum(1 for r in rows if str(getattr(getattr(r, 'type', ''), 'value', getattr(r, 'type', ''))).lower() == 'income'),
                    "largest_category": next(iter(sorted(expense_by_category.items(), key=lambda x: (-x[1], x[0]))))[0] if expense_by_category else None,
                    "largest_category_share": str((next(iter(sorted(expense_by_category.items(), key=lambda x: (-x[1], x[0]))))[1] / total_expense) if expense_by_category and total_expense else Decimal("0")),
                    "savings_rate": str((total_income - total_expense) / total_income) if total_income else None,
                },
                "recommendations": [
                    "Review the largest expense category first and split fixed costs from discretionary ones.",
                    "Repeated anomalies in the same category usually point to a pattern, not a one-off event.",
                    "Automating savings immediately after income arrives reduces month-end leakage.",
                ],
                "category_insights": [
                    {
                        "category": category,
                        "share_of_expenses": str(amount / total_expense) if total_expense else "0",
                        "amount": str(amount),
                        "tip": (
                            "This category is one of the strongest cost drivers in the current analysis. "
                            "Compare it with the previous period and set a cap if it keeps growing."
                        ),
                    }
                    for category, amount in sorted(expense_by_category.items(), key=lambda x: (-x[1], x[0]))[:6]
                ],
            }

            logger.info("Analysis for job %s: %s", job.id, analysis)

            s3_key = build_result_s3_key(str(job.id))
            analysis_json = json.dumps(analysis)


            s3_client.put_object(
                Bucket=settings.S3_BUCKET,
                Key=s3_key,
                Body=analysis_json.encode('utf-8'),
                ContentType="application/json"
            )

            await _add_event(
                db,
                job_id=job.id,
                event_type="INFO",
                message="Saving results to S3",
                user_id=user_id,
            )
            await _stage_delay()

            existing_q = select(JobResult).where(JobResult.job_id == job.id)
            existing_resp = await db.execute(existing_q)
            existing = existing_resp.scalars().first()
            if existing:
                existing.result_type = "financial_analysis"
                existing.result_data = analysis
                existing.s3_key = s3_key
                db.add(existing)
            else:
                db.add(
                    JobResult(
                        job_id=job.id,
                        result_type="financial_analysis",
                        result_data=analysis,
                        s3_key=s3_key
                    )
                )
            await db.commit()

            await _add_event(
                db,
                job_id=job.id,
                event_type="RESULT",
                message="Financial analysis stored in S3",
                user_id=user_id,
            )

            logger.info("Stored job result for job %s", job.id)
            await _stage_delay()

            job.status = "COMPLETED"
            job.completed_at = datetime.utcnow()
            db.add(job)
            await db.commit()
            await db.refresh(job)
            await _add_event(
                db,
                job_id=job.id,
                event_type="COMPLETED",
                message="Job processing completed",
                user_id=user_id,
            )
            logger.info("Job %s marked COMPLETED", job.id)

        except Exception as e:
            try:
                job.status = "ERROR"
                db.add(job)
                await db.commit()
                await _add_event(db, job_id=job.id, event_type="FAILED", message=str(e), user_id=user_id)
            except Exception:
                logger.exception("Failed to store error state")
            logger.exception("Job processing failed")


async def run_worker() -> None:
    """RabbitMQ consumer loop using aio-pika."""
    try:
        import aio_pika
    except Exception as e:
        raise RuntimeError(
            "aio-pika is required to run the worker. Install: pip install aio-pika"
        ) from e

    reconnect_delay = float(getattr(settings, "WORKER_RABBITMQ_RECONNECT_DELAY", 5))
    while True:
        try:
            logger.info("Attempting to connect to RabbitMQ at %s", settings.RABBITMQ_URL)
            connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            async with connection:
                channel = await connection.channel()
                exchange = await channel.declare_exchange(
                    settings.RABBITMQ_EXCHANGE, aio_pika.ExchangeType.FANOUT
                )

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
        except Exception:
            logger.exception("Worker connection/processing error, will retry in %s seconds", reconnect_delay)
            try:
                await asyncio.sleep(reconnect_delay)
            except asyncio.CancelledError:
                logger.info("Worker sleep cancelled, exiting")
                break


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
