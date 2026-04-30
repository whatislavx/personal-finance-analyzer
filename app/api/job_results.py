from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
import uuid
import json
import logging
import io
import re
from pathlib import Path
from datetime import datetime
from decimal import Decimal, InvalidOperation

import httpx
from jinja2 import Environment, FileSystemLoader, select_autoescape
from app.core.s3 import s3_client
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.deps import get_db
from app.db.models.job_results import JobResult
from app.db.schemas.job_results import JobResultCreate, JobResultRead, JobResultUpdate
from app.core.auth import get_current_user
from app.core.config import settings
from app.db.models.jobs import Job

logger = logging.getLogger(__name__)
template_env = Environment(
    loader=FileSystemLoader(Path(__file__).resolve().parents[1] / "templates"),
    autoescape=select_autoescape(["html", "xml"]),
)

router = APIRouter(prefix="/job-results", tags=["job_results"])


def _safe_filename(value: str | None) -> str:
        if not value:
                return "analysis-report"

        sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-._")
        return sanitized or "analysis-report"


def _to_decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
        try:
                if value is None:
                        return default
                return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
                return default


async def _load_result_payload(result: JobResult) -> Dict[str, Any]:
        if result.s3_key:
                try:
                        response = s3_client.get_object(Bucket=settings.S3_BUCKET, Key=result.s3_key)
                        return json.loads(response["Body"].read().decode("utf-8"))
                except Exception as exc:
                        logger.error("Failed to fetch result from S3: %s", str(exc))
                        raise HTTPException(status_code=500, detail="Failed to fetch result from S3")

        if result.result_data:
                return result.result_data

        raise HTTPException(status_code=404, detail="Result data is empty")


def _build_report_html(*, job: Job, result: JobResult, payload: Dict[str, Any]) -> str:
        by_category = payload.get("by_category") or {}
        categories = [
                {
                        "name": name,
                        "amount": _to_decimal(amount),
                }
                for name, amount in sorted(
                        by_category.items(), key=lambda item: (-_to_decimal(item[1]), str(item[0]).lower())
                )
        ]

        total_expense = _to_decimal(payload.get("total_expense") or payload.get("total_expenses"))
        total_income = _to_decimal(payload.get("total_income"))
        net_balance = _to_decimal(payload.get("net_balance"), total_income - total_expense)
        summary = payload.get("summary") or {}
        savings_rate = summary.get("savings_rate")
        savings_rate_decimal = _to_decimal(savings_rate) if savings_rate is not None else None

        raw_anomalies = payload.get("anomalies") or []
        anomalies = [
                {
                        "date": str(item.get("date") or "—"),
                        "category": str(item.get("category") or "Unknown"),
                        "amount": _to_decimal(item.get("amount")),
                        "method": str(item.get("method") or "—"),
                        "score": item.get("score"),
                        "summary": str(item.get("summary") or item.get("reason") or "Anomaly detected"),
                }
                for item in raw_anomalies
                if isinstance(item, dict)
        ]
        anomalies.sort(key=lambda item: item["amount"], reverse=True)

        recommendations = [str(item) for item in (payload.get("recommendations") or []) if item is not None]
        raw_insights = payload.get("category_insights") or []
        category_insights = [item for item in raw_insights if isinstance(item, dict)]
        largest_category = summary.get("largest_category")
        largest_category_share = (
                _to_decimal(summary.get("largest_category_share"))
                if summary.get("largest_category_share") is not None
                else None
        )

        template = template_env.get_template("analysis_report.html")

        def money(value: Any) -> str:
                decimal_value = _to_decimal(value)
                return f"${decimal_value:,.2f}"

        def percent(value: Any) -> str:
                decimal_value = _to_decimal(value)
                return f"{(decimal_value * Decimal('100')):.1f}%"

        def percent_width(value: Any) -> str:
                decimal_value = _to_decimal(value)
                bounded = max(Decimal('0'), min(Decimal('1'), decimal_value))
                return f"{(bounded * Decimal('100')):.1f}%"

        def score(value: Any) -> str:
                if value is None:
                        return "—"
                try:
                        return f"{float(value):.2f}"
                except (TypeError, ValueError):
                        return str(value)

        return template.render(
                job=job,
                result=result,
                categories=categories,
                total_expense=total_expense,
                total_income=total_income,
                net_balance=net_balance,
                anomalies=anomalies,
                recommendations=recommendations,
                category_insights=category_insights,
                summary=summary,
                savings_rate=savings_rate_decimal,
                largest_category=largest_category,
                largest_category_share=largest_category_share,
                generated_at=(result.created_at or job.completed_at or job.updated_at or datetime.utcnow()).strftime("%Y-%m-%d %H:%M UTC"),
                money=money,
                percent=percent,
                percent_width=percent_width,
                score=score,
                Decimal=Decimal,
        )


@router.post("/", response_model=JobResultRead, status_code=status.HTTP_201_CREATED)
async def create_result(
    result_in: JobResultCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    job = await db.get(Job, result_in.job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    result = JobResult(**result_in.model_dump())
    db.add(result)
    await db.commit()
    await db.refresh(result)
    return result


@router.get("/", response_model=List[JobResultRead])
async def list_results(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = (
        select(JobResult)
        .join(Job)
        .where(Job.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    resp = await db.execute(q)
    items = resp.scalars().all()
    return items


@router.get("/{result_id}", response_model=JobResultRead)
async def get_result_by_id(
    result_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = await db.get(JobResult, result_id)
    if not item:
        raise HTTPException(status_code=404, detail="Result not found")
    job = await db.get(Job, item.job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Result not found")
    return item


@router.get("/jobs/{job_id}/result", response_model=Dict[str, Any])
async def get_job_result(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    job = await db.get(Job, job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="The job associated with this result does not exist or is not accessible to you.")

    q = select(JobResult).where(JobResult.job_id == job_id)
    resp = await db.execute(q)
    result = resp.scalars().first()

    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    return await _load_result_payload(result)


@router.get("/jobs/{job_id}/report")
async def export_job_report(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    job = await db.get(Job, job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="The analysis associated with this report does not exist or is not accessible to you.")

    q = select(JobResult).where(JobResult.job_id == job_id)
    resp = await db.execute(q)
    result = resp.scalars().first()

    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    payload = await _load_result_payload(result)
    try:
        html = _build_report_html(job=job, result=result, payload=payload)
    except Exception as exc:
        logger.exception("Failed to build report HTML for job %s", job_id)
        raise HTTPException(status_code=500, detail="The report data is invalid and could not be rendered.") from exc

    gotenberg_url = "http://gotenberg:3000/forms/chromium/convert/html"
    try:
        async with httpx.AsyncClient() as client:
            files = {"index.html": ("index.html", html, "text/html")}
            response = await client.post(gotenberg_url, files=files, timeout=60.0)
    except Exception as exc:
        logger.exception("PDF report conversion request failed for job %s", job_id)
        raise HTTPException(status_code=502, detail="The PDF report service is unavailable. Please try again later.") from exc

    if response.status_code != 200:
        logger.error(
            "PDF report conversion failed for job %s with status %s and body %s",
            job_id,
            response.status_code,
            response.text[:500],
        )
        raise HTTPException(status_code=502, detail="The PDF report could not be generated.")

    filename = f"{_safe_filename(job.name)}-analysis-report.pdf"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(io.BytesIO(response.content), media_type="application/pdf", headers=headers)


@router.put("/{result_id}", response_model=JobResultRead)
async def update_result(
    result_id: uuid.UUID,
    result_in: JobResultUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = await db.get(JobResult, result_id)
    if not item:
        raise HTTPException(status_code=404, detail="Result not found")
    job = await db.get(Job, item.job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Result not found")
    update_data = result_in.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(item, k, v)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_result(
    result_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = await db.get(JobResult, result_id)
    if not item:
        raise HTTPException(status_code=404, detail="Result not found")
    job = await db.get(Job, item.job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Result not found")
    await db.delete(item)
    await db.commit()
    return None
