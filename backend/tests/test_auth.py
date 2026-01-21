def test_health(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.json().get("status") == "ok"


def test_register_and_login_flow(client):
    email = "test@example.com"
    password = "password123"
    client.post("/auth/register", json={"email": email, "password": password, "role": "OWNER"})
    login = client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    assert "access_token" in login.json()


def test_me_endpoint_requires_auth(client):
    res = client.get("/me")
    assert res.status_code in (401, 403)
