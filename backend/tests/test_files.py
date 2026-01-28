import io


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_user(db_session, email: str):
    from app import models

    user = models.User(email=email, password_hash="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _make_token(user_id: int) -> str:
    from app.core.security import create_access_token

    return create_access_token({"sub": str(user_id)})


def test_users_excludes_current_user(client, db_session):
    a = _create_user(db_session, "a@example.com")
    b = _create_user(db_session, "b@example.com")
    token_a = _make_token(a.id)

    res = client.get("/users", headers=_auth_headers(token_a))
    assert res.status_code == 200
    data = res.json()

    # Excludes current user
    ids = {u["id"] for u in data}
    assert a.id not in ids
    assert b.id in ids

    # Only public fields
    assert all(set(u.keys()) == {"id", "email"} for u in data)


def test_send_rejects_self(client, db_session):
    a = _create_user(db_session, "self@example.com")
    token_a = _make_token(a.id)

    files = {"file": ("hello.txt", io.BytesIO(b"hello"), "text/plain")}
    data = {"receiver_id": str(a.id)}
    res = client.post("/files/send", headers=_auth_headers(token_a), data=data, files=files)
    assert res.status_code == 422


def test_send_rejects_invalid_receiver(client, db_session):
    a = _create_user(db_session, "sender@example.com")
    token_a = _make_token(a.id)

    files = {"file": ("hello.txt", io.BytesIO(b"hello"), "text/plain")}
    data = {"receiver_id": "999999"}
    res = client.post("/files/send", headers=_auth_headers(token_a), data=data, files=files)
    assert res.status_code == 404


def test_send_list_and_download_permissions(client, db_session, test_env):
    a = _create_user(db_session, "a2@example.com")
    b = _create_user(db_session, "b2@example.com")
    c = _create_user(db_session, "c2@example.com")

    token_a = _make_token(a.id)
    token_b = _make_token(b.id)
    token_c = _make_token(c.id)

    payload = b"file-bytes-123"
    files = {"file": ("note.txt", io.BytesIO(payload), "text/plain")}
    data = {"receiver_id": str(b.id)}

    send_res = client.post("/files/send", headers=_auth_headers(token_a), data=data, files=files)
    assert send_res.status_code == 200
    sent = send_res.json()
    file_id = sent["id"]

    # Stored file exists on disk
    stored_filename = sent.get("stored_filename")
    assert stored_filename
    storage_path = test_env["storage_dir"] / stored_filename
    assert storage_path.exists()

    # Sent list visible only to sender
    sent_list = client.get("/files/sent", headers=_auth_headers(token_a))
    assert sent_list.status_code == 200
    assert any(f["id"] == file_id for f in sent_list.json())

    # Received list visible only to receiver
    recv_list = client.get("/files/received", headers=_auth_headers(token_b))
    assert recv_list.status_code == 200
    assert any(f["id"] == file_id for f in recv_list.json())

    # Download allowed for sender
    dl_a = client.get(f"/files/{file_id}/download", headers=_auth_headers(token_a))
    assert dl_a.status_code == 200
    assert dl_a.content == payload

    # Download allowed for receiver
    dl_b = client.get(f"/files/{file_id}/download", headers=_auth_headers(token_b))
    assert dl_b.status_code == 200
    assert dl_b.content == payload

    # Download forbidden for third-party user
    dl_c = client.get(f"/files/{file_id}/download", headers=_auth_headers(token_c))
    assert dl_c.status_code == 403

