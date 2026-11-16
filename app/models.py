"""Database models (SQLAlchemy ORM - protects against SQL injection)."""
from datetime import date, datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager

PRIORITIES = ["Low", "Medium", "High"]
STATUSES = ["To Do", "In Progress", "Completed"]


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    tasks = db.relationship(
        "Task", backref="owner", lazy=True, cascade="all, delete-orphan"
    )
    activities = db.relationship(
        "Activity", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default="")
    priority = db.Column(db.String(10), default="Medium", nullable=False)
    status = db.Column(db.String(20), default="To Do", nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    @property
    def is_overdue(self):
        return (
            self.due_date is not None
            and self.status != "Completed"
            and self.due_date < date.today()
        )


class Activity(db.Model):
    """History log: every create/edit/status change/delete is recorded."""

    __tablename__ = "activities"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    task_id = db.Column(db.Integer, nullable=True)
    task_title = db.Column(db.String(120), nullable=False)
    action = db.Column(db.String(30), nullable=False)
    detail = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=utcnow)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
