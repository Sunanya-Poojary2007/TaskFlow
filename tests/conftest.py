import pytest

from app import create_app
from app.extensions import db
from config import TestConfig


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def register(client, username="alice", email="alice@example.com",
             password="Passw0rd123"):
    return client.post("/register", data={
        "username": username, "email": email,
        "password": password, "confirm_password": password})


def login(client, identifier="alice", password="Passw0rd123"):
    return client.post("/login", data={"identifier": identifier,
                                       "password": password})


@pytest.fixture()
def auth_client(client):
    register(client)
    login(client)
    return client
