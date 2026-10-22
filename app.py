from flask import Flask, render_template, request, redirect, url_for, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, init_db, seed_db, close_db
from database.queries import get_recent_transactions, get_category_breakdown, get_user_by_id, get_summary_stats

app = Flask(__name__)
app.secret_key = "spendly-dev-secret-change-in-production"
app.teardown_appcontext(close_db)

with app.app_context():
    init_db()
    seed_db()

# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    if session.get("user_id"):
        return redirect(url_for("profile"))
    return render_template("landing.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    error = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name:
            error = "Please enter your full name."
        elif not email or "@" not in email or "." not in email.split("@")[-1]:
            error = "Please enter a valid email address."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        else:
            db = get_db()
            existing = db.execute(
                "SELECT id FROM users WHERE email = ?", (email,)
            ).fetchone()
            if existing:
                error = "Email already registered. Please sign in."
            else:
                password_hash = generate_password_hash(password)
                db.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, password_hash),
                )
                db.commit()

                session["user_id"] = db.execute(
                    "SELECT id FROM users WHERE email = ?", (email,)
                ).fetchone()["id"]
                session["name"] = name
                return redirect(url_for("profile"))

    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or "@" not in email or "." not in email.split("@")[-1]:
            error = "Please enter a valid email address."
        elif not password:
            error = "Please enter your password."
        else:
            db = get_db()
            user = db.execute(
                "SELECT id, name, email, password_hash FROM users WHERE email = ?", (email,)
            ).fetchone()

            if user is None or not check_password_hash(user["password_hash"], password):
                error = "Incorrect email or password."
            else:
                session["user_id"] = user["id"]
                session["name"] = user["name"]
                return redirect(url_for("profile"))

    return render_template("login.html", error=error)


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("dashboard.html", name=session.get("name"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    # Real user data from the database
    user = get_user_by_id(session["user_id"])
    name = user["name"]
    email = user["email"]
    avatar_initials = "".join([n[0] for n in name.split()[:2]]).upper()
    member_since = user["member_since"]

    # Real summary stats from the database
    summary_stats = get_summary_stats(session["user_id"])

    # Recent transactions from the database
    transactions = get_recent_transactions(session["user_id"])

    # Real category breakdown from the database
    categories = get_category_breakdown(session["user_id"])

    return render_template(
        "profile.html",
        user={
            "name": name,
            "email": email,
            "avatar_initials": avatar_initials,
            "member_since": member_since
        },
        summary_stats=summary_stats,
        transactions=transactions,
        categories=categories
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
