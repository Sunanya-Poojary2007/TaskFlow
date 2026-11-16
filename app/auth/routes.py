"""Module 1: user authentication."""
import re
from urllib.parse import urlparse

from flask import (Blueprint, flash, redirect, render_template, request,
                   url_for)
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.models import User

auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")


def _safe_next(target):
    """Only allow redirects to our own site (prevents open redirect)."""
    if not target:
        return None
    parts = urlparse(target)
    if parts.netloc or parts.scheme or not target.startswith("/"):
        return None
    return target


def _validate_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "Password must contain letters and numbers."
    return None


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        error = None
        if not USERNAME_RE.match(username):
            error = "Username must be 3-30 letters, numbers or underscores."
        elif not EMAIL_RE.match(email):
            error = "Please enter a valid email address."
        elif _validate_password(password):
            error = _validate_password(password)
        elif password != confirm:
            error = "Passwords do not match."
        elif User.query.filter_by(username=username).first():
            error = "That username is already taken."
        elif User.query.filter_by(email=email).first():
            error = "An account with that email already exists."

        if error:
            flash(error, "danger")
            return render_template("auth/register.html",
                                   username=username, email=email), 400

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Account created. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier.lower())
        ).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(_safe_next(request.args.get("next"))
                            or url_for("main.dashboard"))

        flash("Invalid username/email or password.", "danger")
        return render_template("auth/login.html", identifier=identifier), 401

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "details":
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip().lower()
            other = User.query.filter(
                ((User.username == username) | (User.email == email))
                & (User.id != current_user.id)
            ).first()
            if not USERNAME_RE.match(username):
                flash("Username must be 3-30 letters, numbers or "
                      "underscores.", "danger")
            elif not EMAIL_RE.match(email):
                flash("Please enter a valid email address.", "danger")
            elif other:
                flash("Username or email is already in use.", "danger")
            else:
                current_user.username = username
                current_user.email = email
                db.session.commit()
                flash("Profile updated.", "success")

        elif action == "password":
            current = request.form.get("current_password", "")
            new = request.form.get("new_password", "")
            confirm = request.form.get("confirm_password", "")
            if not current_user.check_password(current):
                flash("Current password is incorrect.", "danger")
            elif _validate_password(new):
                flash(_validate_password(new), "danger")
            elif new != confirm:
                flash("New passwords do not match.", "danger")
            else:
                current_user.set_password(new)
                db.session.commit()
                flash("Password changed.", "success")

        return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html")
