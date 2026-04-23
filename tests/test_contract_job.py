from fastapi.testclient import TestClient


def test_contract_jobs_response_shape(client: TestClient, auth_headers):
    create_resp = client.post(
        "/api/jobs/",
        json={"name": "Contract Job", "type": "analysis", "priority": 2},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    job = create_resp.json()

    required = {"id", "name", "type", "status", "user_id", "created_at", "updated_at"}
    assert required.issubset(job.keys())
    assert isinstance(job["name"], str)
    assert isinstance(job["priority"], int)

    list_resp = client.get("/api/jobs/", headers=auth_headers)
    assert list_resp.status_code == 200
    assert any(item["id"] == job["id"] for item in list_resp.json())