"""Worker anomaly detection smoke test.

Creates a user and financial records so that at least one anomaly is detected,
creates a job and runs handle_job_message directly.

Run:
    python scripts/test_worker_anomalies.py
"""

import sys
from pathlib import Path
import asyncio
from decimal import Decimal
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db.engine import AsyncSessionLocal
from app.db.models.users import User
from app.db.models.financial_data import FinancialData, TransactionType
from app.db.models.jobs import Job
from app.worker.worker import handle_job_message
from sqlalchemy import select
from app.db.models.job_results import JobResult


async def main():
    async with AsyncSessionLocal() as db:
        suffix = uuid.uuid4().hex[:8]
        user = User(username=f"anom_{suffix}", email=f"anom_{suffix}@example.com", hashed_password="x")
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Add expenses in one category with one big outlier
        amounts = [Decimal("10"), Decimal("12"), Decimal("11"), Decimal("9"), Decimal("10"), Decimal("150")]
        rows = [
            FinancialData(user_id=user.id, category="food", amount=a, type=TransactionType.EXPENSE, description="t")
            for a in amounts
        ]
        db.add_all(rows)

        # Add some income
        db.add(FinancialData(user_id=user.id, category="salary", amount=Decimal("1000"), type=TransactionType.INCOME, description="pay"))

        await db.commit()

        job = Job(user_id=user.id, name="Anom job", description="", type="expense_analysis", priority=1)
        db.add(job)
        await db.commit()
        await db.refresh(job)

    await handle_job_message({"job_id": str(job.id), "user_id": str(user.id)})

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(JobResult).where(JobResult.job_id == job.id))
        jr = res.scalars().first()
        print("anomalies:", jr.result_data.get("anomalies"))


if __name__ == "__main__":
    asyncio.run(main())

