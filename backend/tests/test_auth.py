def test_health(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.json().get("status") == "ok"


def test_me_endpoint_requires_auth(client):
    res = client.get("/me")
    assert res.status_code in (401, 403)

def test_users_requires_auth(client):
    res = client.get("/users")
    assert res.status_code in (401, 403)
