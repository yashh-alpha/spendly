"""Tests for Step 7: Add Expense feature.

Covers insert_expense query helper, GET /expenses/add and POST /expenses/add routes,
authentication guards, validation rules (amount, category, date), description handling,
and DB side effects.
"""

import pytest
from datetime import date, timedelta
from app import app as flask_app
from database.db import init_db, seed_db, get_db
from database.queries import insert_expense, get_recent_transactions, get_summary_stats


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture
def app():
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "WTF_CSRF_ENABLED": False,
    })
    with flask_app.app_context():
        init_db()
        seed_db()
        yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """Client logged in as the seeded demo user."""
    client.post(
        "/login",
        data={"email": "demo@spendly.com", "password": "demo123"},
    )
    return client


@pytest.fixture
def user_id(app):
    db = get_db()
    row = db.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()
    return row["id"]


# --------------------------------------------------------------------------- #
# Unit tests: insert_expense query helper
# --------------------------------------------------------------------------- #

def test_insert_expense_valid(app, user_id):
    """insert_expense correctly inserts a row and querying returns it."""
    expense_id = insert_expense(
        user_id=user_id,
        amount=50.0,
        category="Food",
        date="2026-03-20",
        description="Lunch",
    )
    assert expense_id is not None
    assert isinstance(expense_id, int)

    db = get_db()
    row = db.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    assert row is not None
    assert row["user_id"] == user_id
    assert row["amount"] == pytest.approx(50.0)
    assert row["category"] == "Food"
    assert row["date"] == "2026-03-20"
    assert row["description"] == "Lunch"


def test_insert_expense_null_description(app, user_id):
    """insert_expense stores description as NULL when None or blank."""
    expense_id = insert_expense(
        user_id=user_id,
        amount=25.0,
        category="Transport",
        date="2026-03-21",
        description=None,
    )

    db = get_db()
    row = db.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    assert row["description"] is None

    # Also test whitespace-only description
    expense_id_blank = insert_expense(
        user_id=user_id,
        amount=15.0,
        category="Other",
        date="2026-03-21",
        description="   ",
    )
    row_blank = db.execute("SELECT * FROM expenses WHERE id = ?", (expense_id_blank,)).fetchone()
    assert row_blank["description"] is None


# --------------------------------------------------------------------------- #
# Route tests: GET /expenses/add
# --------------------------------------------------------------------------- #

def test_get_add_expense_unauthenticated_redirects_to_login(client):
    """Unauthenticated access to GET /expenses/add redirects to /login."""
    resp = client.get("/expenses/add")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")


def test_get_add_expense_authenticated_returns_form(auth_client):
    """Authenticated user accessing GET /expenses/add gets form with category options."""
    resp = auth_client.get("/expenses/add")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert '<form' in html
    assert 'method="POST"' in html
    assert 'action="/expenses/add"' in html

    # Check all 7 fixed options are present
    categories = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]
    for cat in categories:
        assert cat in html


# --------------------------------------------------------------------------- #
# Route tests: POST /expenses/add
# --------------------------------------------------------------------------- #

def test_post_add_expense_unauthenticated_redirects_to_login(client):
    """Unauthenticated POST to /expenses/add redirects to /login."""
    resp = client.post(
        "/expenses/add",
        data={"amount": "50.0", "category": "Food", "date": "2026-03-20", "description": "Lunch"},
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")


def test_post_add_expense_authenticated_valid_redirects_and_inserts(auth_client, user_id):
    """Authenticated POST with valid data inserts expense and redirects to /profile."""
    initial_count = get_summary_stats(user_id)["transaction_count"]

    # Use today's date to ensure it's the most recent
    from datetime import date
    today_str = date.today().strftime("%Y-%m-%d")

    resp = auth_client.post(
        "/expenses/add",
        data={
            "amount": "50.0",
            "category": "Food",
            "date": today_str,
            "description": "Test Lunch",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")

    new_count = get_summary_stats(user_id)["transaction_count"]
    assert new_count == initial_count + 1

    # Query specifically for the inserted expense
    with flask_app.app_context():
        db = get_db()
        row = db.execute(
            "SELECT * FROM expenses WHERE description = ? AND amount = ? AND category = ? "
            "ORDER BY id DESC LIMIT 1",
            ("Test Lunch", 50.0, "Food")
        ).fetchone()
        assert row is not None
        assert row["amount"] == 50.0
        assert row["category"] == "Food"
        assert row["date"] == today_str
        assert row["description"] == "Test Lunch"


@pytest.mark.parametrize("invalid_amount", ["", "0", "0.0", "-10", "abc", None])
def test_post_add_expense_invalid_amount_re_renders_form(auth_client, invalid_amount):
    """Submitting missing, zero, negative, or non-numeric amount re-renders form with error."""
    data = {
        "category": "Food",
        "date": "2026-03-20",
        "description": "Test",
    }
    if invalid_amount is not None:
        data["amount"] = invalid_amount

    resp = auth_client.post("/expenses/add", data=data)
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert "Amount must be a positive number greater than 0" in html


def test_post_add_expense_invalid_category_re_renders_form(auth_client):
    """Submitting an invalid category re-renders form with error."""
    resp = auth_client.post(
        "/expenses/add",
        data={
            "amount": "25.0",
            "category": "Crypto",
            "date": "2026-03-20",
            "description": "Investment",
        },
    )
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert "Category must be one of" in html


@pytest.mark.parametrize("invalid_date", ["not-a-date", "2026-02-30", "13-2026-20"])
def test_post_add_expense_invalid_date_format_re_renders_form(auth_client, invalid_date):
    """Submitting malformed dates re-renders form with error."""
    resp = auth_client.post(
        "/expenses/add",
        data={
            "amount": "25.0",
            "category": "Food",
            "date": invalid_date,
            "description": "Dinner",
        },
    )
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert "Date must be a valid date" in html


def test_post_add_expense_future_date_re_renders_form(auth_client):
    """Submitting a future date re-renders form with error."""
    future_date = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
    resp = auth_client.post(
        "/expenses/add",
        data={
            "amount": "25.0",
            "category": "Food",
            "date": future_date,
            "description": "Future meal",
        },
    )
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert "Date cannot be in the future" in html


def test_post_add_expense_optional_description_blank_succeeds(auth_client, user_id):
    """Submitting without a description saves expense successfully with NULL description."""
    resp = auth_client.post(
        "/expenses/add",
        data={
            "amount": "30.0",
            "category": "Shopping",
            "date": "2026-03-15",
            "description": "",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")

    with flask_app.app_context():
        db = get_db()
        row = db.execute(
            "SELECT * FROM expenses WHERE description IS NULL AND category = ? AND amount = ? "
            "ORDER BY id DESC LIMIT 1",
            ("Shopping", 30.0)
        ).fetchone()
        assert row is not None
        assert row["description"] is None
        assert row["amount"] == 30.0
