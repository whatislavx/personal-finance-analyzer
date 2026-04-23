import uuid

from fastapi.testclient import TestClient


def test_job_results_flow(client: TestClient, auth_headers):
    job_resp = client.post(
        "/api/jobs/",
        json={"name": "Result Job", "description": "desc", "type": "test", "priority": 1},
        headers=auth_headers,
    )
    assert job_resp.status_code == 201
    job_id = job_resp.json()["id"]

    create_result = client.post(
        "/api/job-results/",
        json={"job_id": job_id, "result_type": "SIMPLE", "result_data": {"score": 100}},
        headers=auth_headers,
    )
    assert create_result.status_code == 201
    result_id = create_result.json()["id"]

    get_result = client.get(f"/api/job-results/{result_id}", headers=auth_headers)
    assert get_result.status_code == 200
    assert get_result.json()["result_type"] == "SIMPLE"

    list_results = client.get("/api/job-results/", headers=auth_headers)
    assert list_results.status_code == 200
    assert any(item["id"] == result_id for item in list_results.json())

    update_result = client.put(
        f"/api/job-results/{result_id}",
        json={"result_type": "UPDATED"},
        headers=auth_headers,
    )
    assert update_result.status_code == 200
    assert update_result.json()["result_type"] == "UPDATED"

    delete_result = client.delete(f"/api/job-results/{result_id}", headers=auth_headers)
    assert delete_result.status_code == 204


def test_job_results_not_found_and_validation(client: TestClient, auth_headers):
    assert client.get(f"/api/job-results/{uuid.uuid4()}", headers=auth_headers).status_code == 404
    assert (
        client.post(
            "/api/job-results/",
            json={"job_id": str(uuid.uuid4()), "result_type": "SIMPLE"},
            headers=auth_headers,
        ).status_code
        == 404
    )


def test_get_job_result_payload_endpoint(client: TestClient, auth_headers):
    job_resp = client.post(
        "/api/jobs/",
        json={"name": "Payload Job", "description": "desc", "type": "test", "priority": 1},
        headers=auth_headers,
    )
    assert job_resp.status_code == 201
    job_id = job_resp.json()["id"]

    create_result = client.post(
        "/api/job-results/",
        json={
            "job_id": job_id,
            "result_type": "SIMPLE",
            "result_data": {"by_category": {"Food": 10}, "total_income": 100, "total_expense": 10},
        },
        headers=auth_headers,
    )
    assert create_result.status_code == 201

    payload_resp = client.get(f"/api/job-results/jobs/{job_id}/result", headers=auth_headers)
    assert payload_resp.status_code == 200
    assert payload_resp.json()["total_income"] == 100
