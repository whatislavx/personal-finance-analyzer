import uuid

from fastapi.testclient import TestClient


def test_job_events_update_delete_and_not_found(client: TestClient, auth_headers):
    job_resp = client.post(
        "/api/jobs/",
        json={"name": "events-ext", "type": "analysis"},
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

    upd = client.put(
        f"/api/job-events/{event_id}",
        json={"message": "updated"},
        headers=auth_headers,
    )
    assert upd.status_code == 200
    assert upd.json()["message"] == "updated"

    delete_resp = client.delete(f"/api/job-events/{event_id}", headers=auth_headers)
    assert delete_resp.status_code == 204

    assert client.get(f"/api/job-events/{event_id}", headers=auth_headers).status_code == 404
    assert client.put(f"/api/job-events/{uuid.uuid4()}", json={}, headers=auth_headers).status_code == 404
    assert client.delete(f"/api/job-events/{uuid.uuid4()}", headers=auth_headers).status_code == 404
