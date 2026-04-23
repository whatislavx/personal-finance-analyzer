import uuid

from fastapi.testclient import TestClient


def _register(client: TestClient, suffix: str, password: str = "pass-123"):
    payload = {
        "username": f"user_{suffix}",
        "email": f"user_{suffix}@example.com",
        "password": password,
    }
    resp = client.post("/api/users/", json=payload)
    assert resp.status_code == 201
    return payload, resp.json()


def _login_headers(client: TestClient, username: str, password: str):
    resp = client.post("/api/token", data={"username": username, "password": password})
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_users_duplicates_and_basic_crud(client: TestClient):
    suffix = uuid.uuid4().hex[:8]
    payload, created = _register(client, suffix)

    dup_user = client.post(
        "/api/users/",
        json={"username": payload["username"], "email": f"another_{suffix}@example.com", "password": "x"},
    )
    assert dup_user.status_code == 400

    dup_email = client.post(
        "/api/users/",
        json={"username": f"another_{suffix}", "email": payload["email"], "password": "x"},
    )
    assert dup_email.status_code == 400

    users_resp = client.get("/api/users/")
    assert users_resp.status_code == 200
    assert isinstance(users_resp.json(), list)

    user_id = created["id"]
    get_resp = client.get(f"/api/users/{user_id}")
    assert get_resp.status_code == 200

    update_resp = client.put(
        f"/api/users/{user_id}",
        json={"username": f"updated_{suffix}", "new_password": "new-pass"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["username"] == f"updated_{suffix}"

    delete_resp = client.delete(f"/api/users/{user_id}")
    assert delete_resp.status_code == 204
    assert client.get(f"/api/users/{user_id}").status_code == 404


def test_profile_update_validation_paths(client: TestClient):
    suffix = uuid.uuid4().hex[:8]
    payload, _ = _register(client, suffix, password="secret-123")
    headers = _login_headers(client, payload["username"], "secret-123")

    missing_current = client.put(
        "/api/users/profile",
        json={"username": f"new_{suffix}"},
        headers=headers,
    )
    assert missing_current.status_code == 400

    wrong_current = client.put(
        "/api/users/profile",
        json={"username": f"new_{suffix}", "current_password": "wrong"},
        headers=headers,
    )
    assert wrong_current.status_code == 400

    empty_new_password = client.put(
        "/api/users/profile",
        json={"new_password": " ", "confirm_new_password": " ", "current_password": "secret-123"},
        headers=headers,
    )
    assert empty_new_password.status_code == 400

    mismatch = client.put(
        "/api/users/profile",
        json={
            "new_password": "abc12345",
            "confirm_new_password": "zzz",
            "current_password": "secret-123",
        },
        headers=headers,
    )
    assert mismatch.status_code == 400

    ok = client.put(
        "/api/users/profile",
        json={
            "first_name": "Test",
            "last_name": "User",
            "phone_number": "123456789",
            "current_password": "secret-123",
            "new_password": "secret-456",
            "confirm_new_password": "secret-456",
        },
        headers=headers,
    )
    assert ok.status_code == 200
    assert ok.json()["first_name"] == "Test"
