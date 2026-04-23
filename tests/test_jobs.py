import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient


@patch("app.api.jobs.send_job_message")
def test_job_crud_flow(mock_send, client: TestClient, auth_headers):
    job_data = {"name": "CRUD Job", "type": "analysis", "priority": 1}
    create_resp = client.post("/api/jobs/", json=job_data, headers=auth_headers)
    assert create_resp.status_code == 201
    job_id = create_resp.json()["id"]

    list_resp = client.get("/api/jobs/", headers=auth_headers)
    assert list_resp.status_code == 200
    assert any(item["id"] == job_id for item in list_resp.json())

    get_resp = client.get(f"/api/jobs/{job_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "CRUD Job"

    update_resp = client.put(
        f"/api/jobs/{job_id}", json={"name": "Updated Job"}, headers=auth_headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Updated Job"

    delete_resp = client.delete(f"/api/jobs/{job_id}", headers=auth_headers)
    assert delete_resp.status_code == 204
    assert client.get(f"/api/jobs/{job_id}", headers=auth_headers).status_code == 404
    assert mock_send.called


def test_job_invalid_and_missing_access(client: TestClient, auth_headers):
    invalid_id_resp = client.get("/api/jobs/not-a-uuid", headers=auth_headers)
    assert invalid_id_resp.status_code == 422

    missing_resp = client.get(f"/api/jobs/{uuid.uuid4()}", headers=auth_headers)
    assert missing_resp.status_code == 404