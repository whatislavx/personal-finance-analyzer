from fastapi.testclient import TestClient


def test_register_login_and_profile(client: TestClient, unique_user_payload):
    register_resp = client.post("/api/users/", json=unique_user_payload)
    assert register_resp.status_code == 201

    login_resp = client.post(
        "/api/token",
        data={
            "username": unique_user_payload["username"],
            "password": unique_user_payload["password"],
        },
    )
    assert login_resp.status_code == 200
    payload = login_resp.json()
    assert "access_token" in payload
    assert payload["token_type"] == "bearer"

    headers = {"Authorization": f"Bearer {payload['access_token']}"}
    profile_resp = client.get("/api/users/profile", headers=headers)
    assert profile_resp.status_code == 200
    assert profile_resp.json()["username"] == unique_user_payload["username"]


def test_profile_requires_valid_token(client: TestClient):
    assert client.get("/api/users/profile").status_code == 401
    invalid = client.get(
        "/api/users/profile", headers={"Authorization": "Bearer invalid.token.value"}
    )
    assert invalid.status_code == 401


def test_login_invalid_credentials(client: TestClient):
    response = client.post(
        "/api/token", data={"username": "missing-user", "password": "wrongpassword"}
    )
    assert response.status_code == 401