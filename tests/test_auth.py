from app.models import User
from tests.conftest import login, register


def test_register_success(client):
    resp = register(client)
    assert resp.status_code == 302
    assert User.query.filter_by(username="alice").first() is not None


def test_password_is_hashed(client):
    register(client)
    user = User.query.filter_by(username="alice").first()
    assert user.password_hash != "Passw0rd123"
    assert user.check_password("Passw0rd123")


def test_register_duplicate_username(client):
    register(client)
    resp = register(client, email="other@example.com")
    assert resp.status_code == 400
    assert b"already taken" in resp.data


def test_register_invalid_email(client):
    resp = register(client, email="not-an-email")
    assert resp.status_code == 400


def test_register_weak_password(client):
    resp = register(client, password="short")
    assert resp.status_code == 400
    assert User.query.count() == 0


def test_register_password_mismatch(client):
    resp = client.post("/register", data={
        "username": "bob", "email": "bob@example.com",
        "password": "Passw0rd123", "confirm_password": "different1"})
    assert resp.status_code == 400


def test_login_and_logout(client):
    register(client)
    resp = login(client)
    assert resp.status_code == 302
    assert client.get("/dashboard").status_code == 200

    resp = client.post("/logout")
    assert resp.status_code == 302
    assert client.get("/dashboard").status_code == 302  # redirected to login


def test_login_with_email(client):
    register(client)
    assert login(client, identifier="alice@example.com").status_code == 302


def test_login_wrong_password(client):
    register(client)
    resp = login(client, password="WrongPass1")
    assert resp.status_code == 401
    assert b"Invalid" in resp.data


def test_login_ignores_external_redirect(client):
    register(client)
    resp = client.post("/login?next=https://evil.example.com",
                       data={"identifier": "alice",
                             "password": "Passw0rd123"})
    assert resp.status_code == 302
    assert "evil.example.com" not in resp.headers["Location"]


def test_profile_update(auth_client):
    resp = auth_client.post("/profile", data={
        "action": "details", "username": "alice2",
        "email": "alice2@example.com"})
    assert resp.status_code == 302
    assert User.query.filter_by(username="alice2").first() is not None


def test_change_password(auth_client):
    auth_client.post("/profile", data={
        "action": "password", "current_password": "Passw0rd123",
        "new_password": "NewPassw0rd9", "confirm_password": "NewPassw0rd9"})
    user = User.query.filter_by(username="alice").first()
    assert user.check_password("NewPassw0rd9")


def test_change_password_wrong_current(auth_client):
    auth_client.post("/profile", data={
        "action": "password", "current_password": "nope12345",
        "new_password": "NewPassw0rd9", "confirm_password": "NewPassw0rd9"})
    user = User.query.filter_by(username="alice").first()
    assert user.check_password("Passw0rd123")
