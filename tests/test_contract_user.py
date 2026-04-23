from fastapi.testclient import TestClient


def test_contract_auth_token_shape(client: TestClient, unique_user_payload):
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
    data = login_resp.json()

    # Contract for auth flow response.
    assert set(data.keys()) == {"access_token", "token_type"}
    assert isinstance(data["access_token"], str)
    assert data["token_type"] == "bearer"