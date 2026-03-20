from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, Text, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.users import User
    from app.db.models.job_events import JobEvent
    from app.db.models.job_results import JobResult
    from app.db.models.financial_data import FinancialData


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="PENDING"
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, server_default="0")
    result_url: Mapped[str] = mapped_column(String(512), nullable=True)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )
    started_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    owner: Mapped["User"] = relationship("User", back_populates="jobs")
    events: Mapped[list["JobEvent"]] = relationship(
        "JobEvent", back_populates="job", cascade="all, delete-orphan"
    )
    detailed_result: Mapped["JobResult"] = relationship(
        "JobResult", back_populates="job", uselist=False, cascade="all, delete-orphan"
    )
    financial_data: Mapped[list["FinancialData"]] = relationship(
        "FinancialData", back_populates="job"
    )
