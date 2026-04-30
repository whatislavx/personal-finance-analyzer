from pydantic import BaseModel, ConfigDict
from typing import Any
import uuid
import datetime


class JobResultBase(BaseModel):
    result_type: str
    result_data: Any | None = None
    s3_key: str | None = None


class JobResultCreate(JobResultBase):
    job_id: uuid.UUID


class JobResultUpdate(BaseModel):
    result_type: Any = None
    result_data: Any = None


class JobResultRead(JobResultBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    created_at: datetime.datetime
