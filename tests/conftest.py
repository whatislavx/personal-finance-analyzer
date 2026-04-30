import uuid
import asyncio
import sys

import pytest
from fastapi.testclient import TestClient

import main

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

main.AIO_PIKA_AVAILABLE = False
app = main.app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def disable_rabbit_publish(monkeypatch):
    async def _noop(*args, **kwargs):
        return None

    monkeypatch.setattr("app.api.jobs.send_job_message", _noop)


@pytest.fixture
def unique_user_payload():
    suffix = uuid.uuid4().hex[:8]
    return {
        "username": f"test_user_{suffix}",
        "email": f"test_user_{suffix}@example.com",
        "password": "test-password-123",
        "full_name": "Test User",
    }


@pytest.fixture
def auth_headers(client: TestClient, unique_user_payload):
    create_resp = client.post("/api/users/", json=unique_user_payload)
    assert create_resp.status_code == 201

    login_resp = client.post(
        "/api/token",
        data={
            "username": unique_user_payload["username"],
            "password": unique_user_payload["password"],
        },
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}