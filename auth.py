import re
from datetime import datetime, timezone

from flask import (Blueprint, render_template, request, redirect, url_for, flash)
from flask_login import (login_user, logout_user, login_required, current_user)
from pymongo.errors import DuplicateKeyError
from werkzeug.security import (generate_password_hash, check_password_hash)

from user_model import User

auth_bp = Blueprint("auth", __name__)

def init_auth_routes(users):
    @auth_bp.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("home"))

        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")

            # require an NYU email address
            if not re.fullmatch(r"[A-Za-z0-9._%+-]+@nyu\.edu", email):
                flash("Please use a valid @nyu.edu email.", "error")
                return render_template("register.html", email=email)

            if len(password) < 8:
                flash(
                    "Password must be at least 8 characters.",
                    "error"
                )
                return render_template("register.html", email=email)

            if password != confirm_password:
                flash("Passwords do not match.", "error")
                return render_template("register.html", email=email)

            if users.find_one({"email": email}):
                flash("This email is already registered.", "error")
                return render_template("register.html", email=email)

            new_user = {
                "email": email,
                "password_hash": generate_password_hash(password),
                "created_at": datetime.now(timezone.utc)
            }

            try:
                users.insert_one(new_user)
            except DuplicateKeyError:
                flash("This email is already registered.", "error")
                return render_template("register.html", email=email)

            flash("Account created! Please log in.", "success")
            return redirect(url_for("auth.login"))

        return render_template("register.html")

    @auth_bp.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("home"))

        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            user = User.find_by_email(users, email)

            if user is None or not check_password_hash(user.password_hash, password):
                flash("Invalid email or password.", "error")
                return render_template("login.html", email=email)

            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for("home"))

        return render_template("login.html")

    @auth_bp.route("/logout", methods=["POST"])
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "success")
        return redirect(url_for("home"))

    return auth_bp
