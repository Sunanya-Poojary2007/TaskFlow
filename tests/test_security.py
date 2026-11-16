import pytest

from app import create_app
from app.extensions import db
from config import TestConfig

PROTECTED = ["/dashboard", "/tasks/", "/tasks/board", "/tasks/new",
             "/tasks/history", "/profile"]


@pytest.mark.parametrize("path", PROTECTED)
def test_unauthorized_access_redirects_to_login(client, path):
    resp = client.get(path)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_unauthorized_post_blocked(client):
    resp = client.post("/tasks/new", data={"title": "x"})
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_public_pages_open(client):
    assert client.get("/login").status_code == 200
    assert client.get("/register").status_code == 200
    assert client.get("/healthz").get_json() == {"status": "ok"}


def test_unknown_page_returns_404(client):
    assert client.get("/does-not-exist").status_code == 404


def test_csrf_is_enforced_when_enabled():
    class CsrfConfig(TestConfig):
        WTF_CSRF_ENABLED = True

    app = create_app(CsrfConfig)
    with app.app_context():
        db.create_all()
        resp = app.test_client().post("/login", data={
            "identifier": "a", "password": "b"})
        assert resp.status_code == 400  # missing CSRF token
        db.drop_all()


def test_session_cookie_flags(client):
    client.post("/register", data={
        "username": "alice", "email": "alice@example.com",
        "password": "Passw0rd123", "confirm_password": "Passw0rd123"})
    resp = client.post("/login", data={"identifier": "alice",
                                       "password": "Passw0rd123"})
    cookie = resp.headers.get("Set-Cookie", "")
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
