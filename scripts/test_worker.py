"""Quick local test: create user, add financial records, create a job and run handle_job_message.
Run: python scripts/test_worker.py
"""
import sys
from pathlib import Path
import asyncio
from datetime import datetime
from decimal import Decimal
import uuid

# ensure project root is on sys.path when running this script directly
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db.engine import AsyncSessionLocal
from app.db.models.users import User
from app.db.models.financial_data import FinancialData
from app.db.models.jobs import Job
from app.worker.worker import handle_job_message
from app.db.models.financial_data import TransactionType

async def main():
    async with AsyncSessionLocal() as db:
        # create user
        suffix = uuid.uuid4().hex[:8]
        user = User(username=f"testuser_{suffix}", email=f"test_{suffix}@example.com", hashed_password="x")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print("Created user", user.id)

        # add financial records
        fd1 = FinancialData(user_id=user.id, category="food", amount=Decimal("10.50"), type=TransactionType.EXPENSE, description="lunch")
        fd2 = FinancialData(user_id=user.id, category="salary", amount=Decimal("1000.00"), type=TransactionType.INCOME, description="pay")
        db.add_all([fd1, fd2])
        await db.commit()
        print("Added financial records")

        # create job
        job = Job(user_id=user.id, name="Test Job", description="Testing worker", type="expense_analysis", priority=1)
        db.add(job)
        await db.commit()
        await db.refresh(job)
        print("Created job", job.id)

    # call worker handler directly
    await handle_job_message({"job_id": str(job.id), "user_id": str(user.id)})
    print("Worker handler finished")

if __name__ == "__main__":
    asyncio.run(main())
