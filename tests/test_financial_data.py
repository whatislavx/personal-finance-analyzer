from fastapi.testclient import TestClient


def test_financial_data_crud(client: TestClient, auth_headers):
    create_payload = {
        "date": "2024-01-01T12:00:00",
        "category": "Food",
        "type": "EXPENSE",
        "amount": 100.0,
        "description": "Lunch",
    }
    create_resp = client.post(
        "/api/financial-data/", json=create_payload, headers=auth_headers
    )
    assert create_resp.status_code == 201
    record_id = create_resp.json()["id"]

    get_resp = client.get(f"/api/financial-data/{record_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["category"] == "Food"

    list_resp = client.get("/api/financial-data/", headers=auth_headers)
    assert list_resp.status_code == 200
    assert any(row["id"] == record_id for row in list_resp.json())

    update_resp = client.put(
        f"/api/financial-data/{record_id}",
        json={"description": "Team lunch"},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "Team lunch"

    delete_resp = client.delete(f"/api/financial-data/{record_id}", headers=auth_headers)
    assert delete_resp.status_code == 204


def test_financial_data_requires_auth(client: TestClient):
    assert client.get("/api/financial-data/").status_code == 401
    assert client.post("/api/financial-data/", json={}).status_code == 401
