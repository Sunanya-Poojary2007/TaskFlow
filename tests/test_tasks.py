from datetime import date, timedelta

import pytest

from app.models import Activity, Task
from tests.conftest import login, register


def make_task(client, **overrides):
    data = {"title": "Write report", "description": "Cloud project",
            "priority": "High", "status": "To Do", "due_date": ""}
    data.update(overrides)
    return client.post("/tasks/new", data=data)


def test_create_task(auth_client):
    resp = make_task(auth_client)
    assert resp.status_code == 302
    task = Task.query.one()
    assert task.title == "Write report"
    assert task.priority == "High"


def test_create_task_with_due_date(auth_client):
    make_task(auth_client, due_date="2030-01-31")
    assert Task.query.one().due_date == date(2030, 1, 31)


@pytest.mark.parametrize("bad", [
    {"title": ""},
    {"title": "   "},
    {"title": "x" * 121},
    {"priority": "Urgent"},
    {"status": "Done"},
    {"due_date": "31-01-2030"},
])
def test_invalid_task_forms_rejected(auth_client, bad):
    resp = make_task(auth_client, **bad)
    assert resp.status_code == 400
    assert Task.query.count() == 0


def test_edit_task(auth_client):
    make_task(auth_client)
    task = Task.query.one()
    resp = auth_client.post(f"/tasks/{task.id}/edit", data={
        "title": "Updated", "description": "", "priority": "Low",
        "status": "In Progress", "due_date": ""})
    assert resp.status_code == 302
    task = Task.query.one()
    assert (task.title, task.priority, task.status) == (
        "Updated", "Low", "In Progress")


def test_edit_invalid_rejected(auth_client):
    make_task(auth_client)
    task = Task.query.one()
    resp = auth_client.post(f"/tasks/{task.id}/edit", data={
        "title": "", "priority": "Low", "status": "To Do"})
    assert resp.status_code == 400
    assert Task.query.one().title == "Write report"


def test_update_status(auth_client):
    make_task(auth_client)
    task = Task.query.one()
    auth_client.post(f"/tasks/{task.id}/status",
                     data={"status": "Completed"})
    assert Task.query.one().status == "Completed"


def test_update_status_invalid(auth_client):
    make_task(auth_client)
    task = Task.query.one()
    auth_client.post(f"/tasks/{task.id}/status", data={"status": "Nope"})
    assert Task.query.one().status == "To Do"


def test_delete_task(auth_client):
    make_task(auth_client)
    task = Task.query.one()
    resp = auth_client.post(f"/tasks/{task.id}/delete")
    assert resp.status_code == 302
    assert Task.query.count() == 0


def test_delete_requires_post(auth_client):
    make_task(auth_client)
    task = Task.query.one()
    assert auth_client.get(f"/tasks/{task.id}/delete").status_code == 405
    assert Task.query.count() == 1


def test_history_is_recorded(auth_client):
    make_task(auth_client)
    task = Task.query.one()
    auth_client.post(f"/tasks/{task.id}/status",
                     data={"status": "Completed"})
    auth_client.post(f"/tasks/{task.id}/delete")
    actions = [a.action for a in Activity.query.order_by(Activity.id)]
    assert actions == ["Created", "Status changed", "Deleted"]
    assert b"Created" in auth_client.get("/tasks/history").data


def test_search_and_filter(auth_client):
    make_task(auth_client, title="Alpha", priority="High")
    make_task(auth_client, title="Beta", priority="Low")
    html = auth_client.get("/tasks/?q=alp").data
    assert b"Alpha" in html and b"Beta" not in html
    html = auth_client.get("/tasks/?priority=Low").data
    assert b"Beta" in html and b"Alpha" not in html


def test_search_sql_injection_is_harmless(auth_client):
    make_task(auth_client)
    resp = auth_client.get("/tasks/?q=' OR 1=1 --")
    assert resp.status_code == 200
    assert b"Write report" not in resp.data


def test_board_page(auth_client):
    make_task(auth_client)
    resp = auth_client.get("/tasks/board")
    assert resp.status_code == 200
    assert b"In Progress" in resp.data


def test_dashboard_numbers(auth_client):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    make_task(auth_client, title="Overdue one", due_date=yesterday)
    make_task(auth_client, title="Done one", status="Completed")
    resp = auth_client.get("/dashboard")
    assert resp.status_code == 200
    assert b"50%" in resp.data  # 1 of 2 completed


def test_user_cannot_touch_other_users_tasks(client):
    register(client, "alice", "alice@example.com")
    login(client, "alice")
    make_task(client)
    task_id = Task.query.one().id
    client.post("/logout")

    register(client, "bob", "bob@example.com")
    login(client, "bob")
    assert client.get(f"/tasks/{task_id}/edit").status_code == 404
    assert client.post(f"/tasks/{task_id}/delete").status_code == 404
    assert client.post(f"/tasks/{task_id}/status",
                       data={"status": "Completed"}).status_code == 404
    assert Task.query.count() == 1
