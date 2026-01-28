import io
import zipfile


def _auth_headers(token: str, transfer_token: str | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    if transfer_token:
        headers["X-Transfer-Token"] = transfer_token
    return headers


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


def test_transfer_flow_code_gating_and_zip(client, db_session):
    a = _create_user(db_session, "ta@example.com")
    b = _create_user(db_session, "tb@example.com")
    c = _create_user(db_session, "tc@example.com")

    token_a = _make_token(a.id)
    token_b = _make_token(b.id)
    token_c = _make_token(c.id)

    files = [
        ("files", ("one.txt", io.BytesIO(b"one"), "text/plain")),
        ("files", ("two.txt", io.BytesIO(b"two"), "text/plain")),
        ("files", ("three.txt", io.BytesIO(b"three"), "text/plain")),
    ]

    send_res = client.post(
        "/transfers/send",
        headers=_auth_headers(token_a),
        data={"receiver_id": str(b.id), "access_code": "ABC123"},
        files=files,
    )
    assert send_res.status_code == 200
    transfer_id = send_res.json()["transfer_id"]

    # Incoming count for receiver
    count_res = client.get("/transfers/incoming/count", headers=_auth_headers(token_b))
    assert count_res.status_code == 200
    assert count_res.json()["count"] >= 1

    # Receiver cannot list files without transfer token (code gating)
    list_denied = client.get(f"/transfers/{transfer_id}/files", headers=_auth_headers(token_b))
    assert list_denied.status_code in (401, 403)

    # Wrong code attempts -> 401 then 429 at 5
    for i in range(4):
        bad = client.post(
            f"/transfers/{transfer_id}/verify",
            headers=_auth_headers(token_b),
            json={"access_code": "WRONG12"},
        )
        assert bad.status_code == 401
    locked = client.post(
        f"/transfers/{transfer_id}/verify",
        headers=_auth_headers(token_b),
        json={"access_code": "WRONG12"},
    )
    assert locked.status_code == 429

    # Still locked even if correct (until manual reset / new transfer)
    still_locked = client.post(
        f"/transfers/{transfer_id}/verify",
        headers=_auth_headers(token_b),
        json={"access_code": "ABC123"},
    )
    assert still_locked.status_code == 429


def test_transfer_flow_success_then_download_zip(client, db_session):
    a = _create_user(db_session, "ta2@example.com")
    b = _create_user(db_session, "tb2@example.com")
    c = _create_user(db_session, "tc2@example.com")

    token_a = _make_token(a.id)
    token_b = _make_token(b.id)
    token_c = _make_token(c.id)

    files = [
        ("files", ("one.txt", io.BytesIO(b"one"), "text/plain")),
        ("files", ("two.txt", io.BytesIO(b"two"), "text/plain")),
    ]

    send_res = client.post(
        "/transfers/send",
        headers=_auth_headers(token_a),
        data={"receiver_id": str(b.id), "access_code": "ABC123"},
        files=files,
    )
    assert send_res.status_code == 200
    transfer_id = send_res.json()["transfer_id"]

    # Verify correct code
    ok = client.post(
        f"/transfers/{transfer_id}/verify",
        headers=_auth_headers(token_b),
        json={"access_code": "ABC123"},
    )
    assert ok.status_code == 200
    transfer_token = ok.json().get("transfer_access_token")
    assert transfer_token

    # Receiver can list files with transfer token
    lf = client.get(f"/transfers/{transfer_id}/files", headers=_auth_headers(token_b, transfer_token))
    assert lf.status_code == 200
    files_list = lf.json()
    assert len(files_list) == 2
    file_ids = [f["id"] for f in files_list]

    # Receiver can download zip-all with transfer token
    zip_res = client.get(f"/transfers/{transfer_id}/download-all", headers=_auth_headers(token_b, transfer_token))
    assert zip_res.status_code == 200
    assert zip_res.headers.get("content-type", "").startswith("application/zip")
    assert zip_res.content[:2] == b"PK"

    zf = zipfile.ZipFile(io.BytesIO(zip_res.content))
    names = set(zf.namelist())
    assert "one.txt" in names
    assert "two.txt" in names

    # Receiver deletes one file -> it should disappear only for receiver
    del_one = client.delete(
        f"/transfers/{transfer_id}/files/{file_ids[0]}",
        headers=_auth_headers(token_b, transfer_token),
    )
    assert del_one.status_code == 200
    assert del_one.json()["deleted"] is True
    assert del_one.json()["remaining_visible_files"] == 1

    lf2 = client.get(f"/transfers/{transfer_id}/files", headers=_auth_headers(token_b, transfer_token))
    assert lf2.status_code == 200
    assert len(lf2.json()) == 1

    # Sender can still see both files
    lf_sender = client.get(f"/transfers/{transfer_id}/files", headers=_auth_headers(token_a))
    assert lf_sender.status_code == 200
    assert len(lf_sender.json()) == 2

    # Sender deletes the same file -> now it's hard-deleted (both sides deleted)
    del_same = client.delete(
        f"/transfers/{transfer_id}/files/{file_ids[0]}",
        headers=_auth_headers(token_a),
    )
    assert del_same.status_code == 200
    assert del_same.json()["hard_deleted"] is True

    lf_sender2 = client.get(f"/transfers/{transfer_id}/files", headers=_auth_headers(token_a))
    assert lf_sender2.status_code == 200
    assert len(lf_sender2.json()) == 1

    # Receiver deletes their remaining visible file -> transfer should disappear for receiver,
    # but remain for sender with 1 file.
    remaining_id_receiver = lf2.json()[0]["id"]
    del_last_receiver = client.delete(
        f"/transfers/{transfer_id}/files/{remaining_id_receiver}",
        headers=_auth_headers(token_b, transfer_token),
    )
    assert del_last_receiver.status_code == 200
    assert del_last_receiver.json()["remaining_visible_files"] == 0

    received_list = client.get("/transfers/received", headers=_auth_headers(token_b))
    assert received_list.status_code == 200
    assert all(x["transfer_id"] != transfer_id for x in received_list.json())

    sent_list = client.get("/transfers/sent", headers=_auth_headers(token_a))
    assert sent_list.status_code == 200
    assert any(x["transfer_id"] == transfer_id for x in sent_list.json())

    # Third user cannot access
    denied = client.get(f"/transfers/{transfer_id}/files", headers=_auth_headers(token_c, transfer_token))
    assert denied.status_code == 403

