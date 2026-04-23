import asyncio
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.api import financial_data as fd_api
from app.api import job_results as jr_api
from app.api.jobs import ConnectionManager, consume_job_events, perform_job
from app.core import auth as auth_core


class _FakeAsyncClient:
    def __init__(self, response):
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *args, **kwargs):
        return self._response


def test_financial_report_error_branch(client, auth_headers, monkeypatch):
    class _ExecResult:
        def scalars(self):
            return self

        def all(self):
            return [
                SimpleNamespace(
                    date=datetime.utcnow(),
                    category="Food",
                    type=SimpleNamespace(value="EXPENSE"),
                    amount=12.5,
                    description="Lunch",
                )
            ]

    class _DB:
        async def execute(self, _q):
            return _ExecResult()

    response = SimpleNamespace(status_code=502, content=b"", text="error")
    monkeypatch.setattr(fd_api.httpx, "AsyncClient", lambda: _FakeAsyncClient(response))

    async def _run():
        with pytest.raises(Exception):
            await fd_api.export_report(
                db=_DB(),
                current_user=SimpleNamespace(email="u@example.com", id="u1"),
            )

    asyncio.run(_run())


def test_job_result_helpers_and_report_html():
    payload = {
        "by_category": {"Food": "120.5", "Rent": "500"},
        "total_income": "1000",
        "total_expense": "620.5",
        "summary": {"savings_rate": "0.2", "largest_category": "Rent", "largest_category_share": "0.8"},
        "anomalies": [{"title": "High food expense", "score": 0.83}],
        "recommendations": ["Reduce dining out"],
        "category_insights": [{"category": "Food", "trend": "up", "score": 0.91}],
    }
    job = SimpleNamespace(name="ReportJob", completed_at=None, updated_at=datetime.utcnow())
    result = SimpleNamespace(created_at=datetime.utcnow())
    html = jr_api._build_report_html(job=job, result=result, payload=payload)
    assert "ReportJob" in html
    assert "Reduce dining out" in html


def test_job_result_payload_from_s3_and_errors(monkeypatch):
    class _Body:
        def read(self):
            return b'{"ok": true}'

    monkeypatch.setattr(
        jr_api.s3_client,
        "get_object",
        lambda **kwargs: {"Body": _Body()},
    )
    result = SimpleNamespace(s3_key="x.json", result_data=None)
    payload = asyncio.run(jr_api._load_result_payload(result))
    assert payload["ok"] is True

    monkeypatch.setattr(jr_api.s3_client, "get_object", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(Exception):
        asyncio.run(jr_api._load_result_payload(SimpleNamespace(s3_key="x", result_data=None)))


def test_core_auth_negative_paths(monkeypatch):
    token = auth_core.create_access_token({"sub": "abc"})
    assert isinstance(token, str)

    monkeypatch.setattr(auth_core, "_HAS_JOSE", False)
    with pytest.raises(RuntimeError):
        auth_core.create_access_token({"sub": "abc"})

    monkeypatch.setattr(auth_core, "_HAS_JOSE", True)


def test_jobs_connection_manager_and_consumers(monkeypatch):
    manager = ConnectionManager()
    ws = SimpleNamespace()

    async def _accept():
        return None

    async def _send_text(_msg):
        return None

    ws.accept = _accept
    ws.send_text = _send_text
    asyncio.run(manager.connect(ws, "job-1"))
    asyncio.run(manager.send_personal_message("msg", "job-1"))
    manager.disconnect(ws, "job-1")

    monkeypatch.setitem(__import__("sys").modules, "aio_pika", None)
    asyncio.run(consume_job_events())


def test_perform_job_missing_ml_dependencies():
    class _Job:
        def __init__(self):
            self.id = "j1"
            self.status = "pending"
            self.result = None
            self.progress = 0

    class _DB:
        def __init__(self):
            self.job = _Job()

        async def get(self, model, value):
            return self.job

        def add(self, obj):
            return None

        async def commit(self):
            return None

    db = _DB()
    asyncio.run(perform_job("j1", db))
    assert db.job.result is not None
