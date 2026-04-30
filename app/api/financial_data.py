from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.deps import get_db
from app.db.models.financial_data import FinancialData
from app.db.schemas.financial_data import (
    FinancialDataCreate,
    FinancialDataRead,
    FinancialDataUpdate,
)
from app.core.auth import get_current_user
from fastapi.responses import StreamingResponse
import httpx
from datetime import datetime
from jinja2 import Template
import io

router = APIRouter(prefix="/financial-data", tags=["financial_data"])


@router.post("/", response_model=FinancialDataRead, status_code=status.HTTP_201_CREATED)
async def create_record(
    record_in: FinancialDataCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Pydantic provides TransactionType enum; SQLAlchemy model expects the same enum
    record = FinancialData(**record_in.model_dump())
    record.user_id = current_user.id
    db.add(record)

    await db.commit()
    await db.refresh(record)

    return record


@router.get("/", response_model=List[FinancialDataRead])
async def list_records(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = (
        select(FinancialData)
        .where(FinancialData.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    resp = await db.execute(q)
    items = resp.scalars().all()

    return items


@router.get("/{record_id}", response_model=FinancialDataRead)
async def get_record(
    record_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = select(FinancialData).where(
        FinancialData.id == record_id, FinancialData.user_id == current_user.id
    )
    resp = await db.execute(q)
    item = resp.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="The requested financial record does not exist or you do not have access to it.")
    return item


@router.put("/{record_id}", response_model=FinancialDataRead)
async def update_record(
    record_id: uuid.UUID,
    record_in: FinancialDataUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = select(FinancialData).where(
        FinancialData.id == record_id, FinancialData.user_id == current_user.id
    )
    resp = await db.execute(q)
    item = resp.scalars().first()

    if not item:
        raise HTTPException(status_code=404, detail="The requested financial record does not exist or you do not have access to it.")

    update_data = record_in.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(item, key, value)

    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(
    record_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = select(FinancialData).where(
        FinancialData.id == record_id, FinancialData.user_id == current_user.id
    )
    resp = await db.execute(q)
    item = resp.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="The requested financial record does not exist or you do not have access to it.")
    await db.delete(item)
    await db.commit()
    return None


@router.get('/report')
async def export_report(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate PDF report for user's financial data via Gotenberg.

    Returns PDF bytes as StreamingResponse.
    """
    q = select(FinancialData).where(FinancialData.user_id == current_user.id)
    if date_from:
        q = q.where(FinancialData.date >= date_from)
    if date_to:
        q = q.where(FinancialData.date <= date_to)

    resp = await db.execute(q)
    items = resp.scalars().all()

    # simple HTML template
    tmpl = Template('''
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <title>Financial Report</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 20px }
          table { border-collapse: collapse; width: 100% }
          th, td { border: 1px solid #ddd; padding: 8px }
          th { background: #f4f4f4 }
        </style>
      </head>
      <body>
        <h1>Financial Report</h1>
        <p>User: {{ user }}</p>
        <table>
          <thead><tr><th>Date</th><th>Category</th><th>Type</th><th>Amount</th><th>Description</th></tr></thead>
          <tbody>
          {% for r in rows %}
            <tr>
              <td>{{ r.date.strftime('%Y-%m-%d') }}</td>
              <td>{{ r.category }}</td>
              <td>{{ r.type.value }}</td>
              <td style="text-align:right">{{ '%.2f'|format(r.amount) }}</td>
              <td>{{ r.description or '' }}</td>
            </tr>
          {% endfor %}
          </tbody>
        </table>
      </body>
    </html>
    ''')

    html = tmpl.render(user=current_user.email, rows=items)

    # send to Gotenberg
    gotenberg_url = "http://gotenberg:3000/forms/chromium/convert/html"
    async with httpx.AsyncClient() as client:
        files = {"index.html": ("report.html", html, "text/html")}
        r = await client.post(gotenberg_url, files=files, timeout=60.0)

    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="Gotenberg conversion failed")

    pdf_bytes = r.content
    headers = {"Content-Disposition": "attachment; filename=financial_report.pdf"}
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type='application/pdf', headers=headers)
