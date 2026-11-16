"""Module 3: dashboard and landing page."""
from datetime import date, timedelta

from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.models import PRIORITIES, STATUSES, Activity, Task

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/healthz")
def healthz():
    """Used by Render and the post-deploy check."""
    return {"status": "ok"}


@main_bp.route("/dashboard")
@login_required
def dashboard():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == "Completed")
    pending = total - completed
    overdue = sum(1 for t in tasks if t.is_overdue)
    percent = round(completed / total * 100) if total else 0

    status_counts = [sum(1 for t in tasks if t.status == s)
                     for s in STATUSES]
    priority_counts = [sum(1 for t in tasks if t.priority == p)
                       for p in PRIORITIES]

    today = date.today()
    upcoming = sorted(
        (t for t in tasks
         if t.due_date and t.status != "Completed"
         and today <= t.due_date <= today + timedelta(days=7)),
        key=lambda t: t.due_date)

    recent = (Activity.query.filter_by(user_id=current_user.id)
              .order_by(Activity.created_at.desc(), Activity.id.desc())
              .limit(6).all())

    return render_template(
        "dashboard.html", total=total, completed=completed,
        pending=pending, overdue=overdue, percent=percent,
        statuses=STATUSES, status_counts=status_counts,
        priorities=PRIORITIES, priority_counts=priority_counts,
        upcoming=upcoming, recent=recent)
