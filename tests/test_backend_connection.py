"""Tests for Step 5: backend connection for the profile page.

Covers the four query helpers in ``database/queries.py`` and the
``GET /profile`` route.
"""

import pytest
from app import app
from database.db import init_db, seed_db, get_db
from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)


# --------------------------------------------------------------------------- #
# Fixtures                                                                     #
# --------------------------------------------------------------------------- #

@pytest.fixture
def client():
    """Provide a test client backed by the real (seeded) database."""
    app.config["TESTING"] = True
    with app.app_context():
        init_db()
        seed_db()
    with app.test_client() as client:
        yield client


@pytest.fixture
def app_context():
    """Provide an app context for query helper tests."""
    with app.app_context():
        init_db()
        seed_db()
        yield app


@pytest.fixture
def seed_user_id(app_context):
    """Return the id of the seeded demo user."""
    db = get_db()
    row = db.execute(
        "SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)
    ).fetchone()
    db.close()
    return row["id"]


# --------------------------------------------------------------------------- #
# get_user_by_id                                                               #
# --------------------------------------------------------------------------- #

def test_get_user_by_id_valid(app_context, seed_user_id):
    user = get_user_by_id(seed_user_id)
    assert user is not None
    assert user["name"] == "Demo User"
    assert user["email"] == "demo@spendly.com"
    assert "2026" in user["member_since"]


def test_get_user_by_id_nonexistent(app_context):
    assert get_user_by_id(99999) is None


# --------------------------------------------------------------------------- #
# get_summary_stats                                                            #
# --------------------------------------------------------------------------- #

def test_get_summary_stats_with_expenses(app_context, seed_user_id):
    stats = get_summary_stats(seed_user_id)
    assert stats["total_spent"] == pytest.approx(285.50)
    assert stats["transaction_count"] == 8
    assert stats["top_category"] == "Bills"


def test_get_summary_stats_no_expenses(app_context):
    stats = get_summary_stats(99999)
    assert stats == {
        "total_spent": 0,
        "transaction_count": 0,
        "top_category": "—",
    }


# --------------------------------------------------------------------------- #
# get_recent_transactions                                                      #
# --------------------------------------------------------------------------- #

def test_get_recent_transactions_with_expenses(app_context, seed_user_id):
    txs = get_recent_transactions(seed_user_id)
    assert len(txs) == 8
    # Newest-first ordering
    dates = [t["date"] for t in txs]
    assert dates == sorted(dates, reverse=True)
    # Each item has the required keys
    for tx in txs:
        assert set(tx.keys()) == {"date", "description", "category", "amount"}


def test_get_recent_transactions_no_expenses(app_context):
    assert get_recent_transactions(99999) == []


def test_get_recent_transactions_limit(app_context, seed_user_id):
    txs = get_recent_transactions(seed_user_id, limit=3)
    assert len(txs) == 3


# --------------------------------------------------------------------------- #
# get_category_breakdown                                                       #
# --------------------------------------------------------------------------- #

def test_get_category_breakdown_with_expenses(app_context, seed_user_id):
    cats = get_category_breakdown(seed_user_id)
    assert len(cats) == 7
    # Ordered by amount descending
    amounts = [c["amount"] for c in cats]
    assert amounts == sorted(amounts, reverse=True)
    # Percentages sum to 100
    assert sum(c["pct"] for c in cats) == 100
    # Each item has the required keys
    for cat in cats:
        assert set(cat.keys()) == {"name", "amount", "pct"}


def test_get_category_breakdown_no_expenses(app_context):
    assert get_category_breakdown(99999) == []


# --------------------------------------------------------------------------- #
# Route: GET /profile                                                          #
# --------------------------------------------------------------------------- #

def test_profile_unauthenticated_redirects(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_profile_authenticated_seed_user(client):
    # Log in as the seeded demo user
    client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123",
    })

    response = client.get("/profile")
    assert response.status_code == 200

    html = response.data.decode("utf-8")
    assert "Demo User" in html
    assert "demo@spendly.com" in html
    assert "₹" in html
    assert "285.50" in html
    assert "Bills" in html