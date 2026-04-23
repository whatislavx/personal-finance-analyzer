from fastapi.testclient import TestClient


def test_job_events_crud(client: TestClient, auth_headers):
    job_resp = client.post(
        "/api/jobs/",
        json={"name": "Events Job", "description": "desc", "type": "test"},
        headers=auth_headers,
    )
    assert job_resp.status_code == 201
    job_id = job_resp.json()["id"]

    create_resp = client.post(
        "/api/job-events/",
        json={"job_id": job_id, "type": "STARTED", "message": "begin"},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    event_id = create_resp.json()["id"]

    get_resp = client.get(f"/api/job-events/{event_id}", headers=auth_headers)
    assert get_resp.status_code == 200

    list_resp = client.get("/api/job-events/", headers=auth_headers)
    assert list_resp.status_code == 200
    assert any(item["id"] == event_id for item in list_resp.json())
