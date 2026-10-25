from flask import Flask, render_template, request, redirect, url_for, session, abort, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import os
from database.db import get_db, init_db, seed_db, close_db
from database.queries import get_recent_transactions, get_category_breakdown, get_user_by_id, get_summary_stats, insert_expense


VALID_CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]
MAX_DESCRIPTION_LENGTH = 200


def _parse_iso_date(s: str) -> date | None:
    """Parse an ISO date string (YYYY-MM-DD) to a date object.
    Returns None if the string is invalid or empty.
    """
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def _months_ago_start(today: date, months: int) -> date:
    """Return the first day of the month `months` months before `today`."""
    m = today.month - months
    y = today.year
    if m <= 0:
        m += 12
        y -= 1
    return date(y, m, 1)


def _render_add_expense_form(amount="", category="", date_str="", description="", error=None):
    """Helper to render the add expense form with preserved values and optional error."""
    if error:
        flash(error, "error")
    return render_template(
        "add_expense.html",
        amount=amount,
        category=category,
        date=date_str,
        description=description,
        max_date=date.today().strftime("%Y-%m-%d"),
    )

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "spendly-dev-secret-change-in-production")
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

    # --- Date filter parsing & validation ---
    raw_from = request.args.get("date_from", "")
    raw_to = request.args.get("date_to", "")

    date_from = _parse_iso_date(raw_from) if raw_from else None
    date_to = _parse_iso_date(raw_to) if raw_to else None

    # Validate range
    date_error = None
    if date_from and date_to and date_from > date_to:
        date_from = None
        date_to = None
        date_error = "Start date must be before end date."
        flash(date_error, "error")

    # --- Preset calculations for template ---
    today = date.today()

    presets = {
        "this_month": {"label": "This Month", "date_from": _months_ago_start(today, 0), "date_to": today},
        "last_3_months": {"label": "Last 3 Months", "date_from": _months_ago_start(today, 3), "date_to": today},
        "last_6_months": {"label": "Last 6 Months", "date_from": _months_ago_start(today, 6), "date_to": today},
        "all_time": {"label": "All Time", "date_from": None, "date_to": None},
    }

    # Determine active preset
    active_preset = "all_time"
    for key, preset in presets.items():
        if preset["date_from"] == date_from and preset["date_to"] == date_to:
            active_preset = key
            break

    # --- Fetch data with date filters ---
    user = get_user_by_id(session["user_id"])
    name = user["name"]
    email = user["email"]
    avatar_initials = "".join([n[0] for n in name.split()[:2]]).upper()
    member_since = user["member_since"]

    summary_stats = get_summary_stats(session["user_id"], date_from, date_to)
    transactions = get_recent_transactions(session["user_id"], date_from=date_from, date_to=date_to)
    categories = get_category_breakdown(session["user_id"], date_from, date_to)

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
        categories=categories,
        # Date filter context
        date_from=date_from,
        date_to=date_to,
        presets=presets,
        active_preset=active_preset,
        date_error=date_error,
    )


@app.route("/analytics")
def analytics():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("analytics.html")


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    if request.method == "POST":
        # --- Parse and validate form fields ---
        raw_amount = request.form.get("amount", "").strip()
        raw_category = request.form.get("category", "").strip()
        raw_date = request.form.get("date", "").strip()
        raw_description = request.form.get("description", "").strip()

        # Validate amount: must be a positive number
        try:
            amount = float(raw_amount)
            if amount <= 0:
                raise ValueError("Amount must be greater than 0")
        except (ValueError, TypeError):
            return _render_add_expense_form(
                amount=raw_amount,
                category=raw_category,
                date_str=raw_date,
                description=raw_description,
                error="Amount must be a positive number greater than 0.",
            )

        # Validate category: must be one of the 7 fixed options
        if raw_category not in VALID_CATEGORIES:
            return _render_add_expense_form(
                amount=raw_amount,
                category=raw_category,
                date_str=raw_date,
                description=raw_description,
                error=f"Category must be one of: {', '.join(VALID_CATEGORIES)}.",
            )

        # Validate date: must be a valid YYYY-MM-DD date (not a future date)
        try:
            parsed_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
            if parsed_date > date.today():
                return _render_add_expense_form(
                    amount=raw_amount,
                    category=raw_category,
                    date_str=raw_date,
                    description=raw_description,
                    error="Date cannot be in the future.",
                )
        except (ValueError, TypeError):
            return _render_add_expense_form(
                amount=raw_amount,
                category=raw_category,
                date_str=raw_date,
                description=raw_description,
                error="Date must be a valid date in YYYY-MM-DD format.",
            )

        # Validate description length (server-side)
        if len(raw_description) > MAX_DESCRIPTION_LENGTH:
            return _render_add_expense_form(
                amount=raw_amount,
                category=raw_category,
                date_str=raw_date,
                description=raw_description,
                error=f"Description too long (max {MAX_DESCRIPTION_LENGTH} characters).",
            )

        # --- Insert the expense ---
        insert_expense(
            user_id=session["user_id"],
            amount=amount,
            category=raw_category,
            date=raw_date,
            description=raw_description if raw_description else None,
        )
        flash("Expense added successfully!", "success")
        return redirect(url_for("profile"))

    # --- GET request: render the form ---
    return _render_add_expense_form(date_str=date.today().strftime("%Y-%m-%d"))


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode, port=5001)
