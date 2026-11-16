"""Module 2: task management."""
from datetime import datetime

from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, url_for)
from flask_login import current_user, login_required

from app.extensions import db
from app.models import PRIORITIES, STATUSES, Activity, Task

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")


def _log(task_title, action, detail="", task_id=None):
    db.session.add(Activity(user_id=current_user.id, task_id=task_id,
                            task_title=task_title, action=action,
                            detail=detail))


def _get_own_task(task_id):
    """Return the task only if it belongs to the logged-in user."""
    task = db.session.get(Task, task_id)
    if task is None or task.user_id != current_user.id:
        abort(404)
    return task


def _parse_form(form):
    """Validate task form data. Returns (data, error)."""
    title = form.get("title", "").strip()
    description = form.get("description", "").strip()
    priority = form.get("priority", "Medium")
    status = form.get("status", "To Do")
    due_raw = form.get("due_date", "").strip()

    if not title:
        return None, "Title is required."
    if len(title) > 120:
        return None, "Title must be 120 characters or fewer."
    if len(description) > 2000:
        return None, "Description must be 2000 characters or fewer."
    if priority not in PRIORITIES:
        return None, "Invalid priority."
    if status not in STATUSES:
        return None, "Invalid status."

    due_date = None
    if due_raw:
        try:
            due_date = datetime.strptime(due_raw, "%Y-%m-%d").date()
        except ValueError:
            return None, "Due date must be a valid date."

    return {"title": title, "description": description,
            "priority": priority, "status": status,
            "due_date": due_date}, None


@tasks_bp.route("/")
@login_required
def list_tasks():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "")
    priority = request.args.get("priority", "")

    query = Task.query.filter_by(user_id=current_user.id)
    if q:
        like = f"%{q}%"
        query = query.filter(Task.title.ilike(like)
                             | Task.description.ilike(like))
    if status in STATUSES:
        query = query.filter_by(status=status)
    if priority in PRIORITIES:
        query = query.filter_by(priority=priority)

    tasks = query.order_by(Task.due_date.is_(None), Task.due_date,
                           Task.created_at.desc()).all()
    return render_template("tasks/list.html", tasks=tasks, q=q,
                           status=status, priority=priority,
                           statuses=STATUSES, priorities=PRIORITIES)


@tasks_bp.route("/board")
@login_required
def board():
    tasks = (Task.query.filter_by(user_id=current_user.id)
             .order_by(Task.due_date.is_(None), Task.due_date).all())
    columns = {s: [t for t in tasks if t.status == s] for s in STATUSES}
    return render_template("tasks/board.html", columns=columns,
                           statuses=STATUSES)


@tasks_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        data, error = _parse_form(request.form)
        if error:
            flash(error, "danger")
            return render_template("tasks/form.html", task=None,
                                   form=request.form, statuses=STATUSES,
                                   priorities=PRIORITIES), 400
        task = Task(user_id=current_user.id, **data)
        db.session.add(task)
        db.session.flush()
        _log(task.title, "Created", f"Priority {task.priority}", task.id)
        db.session.commit()
        flash("Task created.", "success")
        return redirect(url_for("tasks.list_tasks"))

    return render_template("tasks/form.html", task=None, form={},
                           statuses=STATUSES, priorities=PRIORITIES)


@tasks_bp.route("/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit(task_id):
    task = _get_own_task(task_id)

    if request.method == "POST":
        data, error = _parse_form(request.form)
        if error:
            flash(error, "danger")
            return render_template("tasks/form.html", task=task,
                                   form=request.form, statuses=STATUSES,
                                   priorities=PRIORITIES), 400

        changes = [f"{k}: {getattr(task, k) or '-'} -> {v or '-'}"
                   for k, v in data.items() if getattr(task, k) != v]
        for key, value in data.items():
            setattr(task, key, value)
        if changes:
            _log(task.title, "Edited", "; ".join(changes)[:250], task.id)
        db.session.commit()
        flash("Task updated.", "success")
        return redirect(url_for("tasks.list_tasks"))

    return render_template("tasks/form.html", task=task, form={},
                           statuses=STATUSES, priorities=PRIORITIES)


@tasks_bp.route("/<int:task_id>/status", methods=["POST"])
@login_required
def update_status(task_id):
    task = _get_own_task(task_id)
    new_status = request.form.get("status", "")
    if new_status not in STATUSES:
        flash("Invalid status.", "danger")
        return redirect(request.referrer or url_for("tasks.list_tasks"))
    if new_status != task.status:
        _log(task.title, "Status changed",
             f"{task.status} -> {new_status}", task.id)
        task.status = new_status
        db.session.commit()
        flash(f"Marked as {new_status}.", "success")
    return redirect(request.referrer or url_for("tasks.list_tasks"))


@tasks_bp.route("/<int:task_id>/delete", methods=["POST"])
@login_required
def delete(task_id):
    task = _get_own_task(task_id)
    _log(task.title, "Deleted", "", task.id)
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted.", "info")
    return redirect(url_for("tasks.list_tasks"))


@tasks_bp.route("/history")
@login_required
def history():
    activities = (Activity.query.filter_by(user_id=current_user.id)
                  .order_by(Activity.created_at.desc(),
                            Activity.id.desc()).limit(200).all())
    return render_template("tasks/history.html", activities=activities)
