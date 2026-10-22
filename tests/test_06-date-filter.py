"""Tests for Step 6: date filter for profile page.

Covers GET /profile with date_from/date_to query params, preset handling,
validation, flash messages, active state, empty state, auth guard and
currency display.
"""

import pytest
from datetime import date, timedelta
from app import app as flask_app
from database.db import init_db, seed_db, get_db
from database.queries import get_summary_stats, get_recent_transactions, get_category_breakdown


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
# Auth guard
# --------------------------------------------------------------------------- #

def test_profile_unauthenticated_redirects_to_login(client):
    resp = client.get("/profile")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")


# --------------------------------------------------------------------------- #
# Happy paths – unfiltered / All Time
# --------------------------------------------------------------------------- #

def test_profile_unfiltered_shows_all_expenses(auth_client):
    resp = auth_client.get("/profile")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert "Demo User" in html
    assert "₹" in html
    assert "285.50" in html
    assert "8" in html  # transaction count


def test_preset_all_time_generates_clean_url(auth_client):
    resp = auth_client.get("/profile")
    html = resp.data.decode("utf-8")
    # All Time preset link should be clean /profile with active state
    assert 'href="/profile"' in html
    assert "All Time" in html


# --------------------------------------------------------------------------- #
# Preset happy paths
# --------------------------------------------------------------------------- #

def test_preset_this_monthFilters_AllSeedData(auth_client):
    today = date.today()
    start = date(today.year, today.month, 1)
    resp = auth_client.get(
        "/profile",
        query_string={"date_from": start.isoformat(), "date_to": today.isoformat()},
    )
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    # All seed expenses are in October 2026, so total remains 285.50
    assert "285.50" in html
    assert "₹" in html


def test_preset_last_3_months_filters(auth_client, user_id):
    today = date.today()
    # compute start like app does
    month = today.month - 3
    year = today.year
    if month <= 0:
        month += 12
        year -= 1
    start = date(year, month, 1)
    resp = auth_client.get(
        "/profile",
        query_string={"date_from": start.isoformat(), "date_to": today.isoformat()},
    )
    assert resp.status_code == 200
    # query helper should return all seed data
    stats = get_summary_stats(user_id, date_from=start, date_to=today)
    assert stats["total_spent"] == pytest.approx(285.50)
    assert stats["transaction_count"] == 8


def test_preset_last_6_months_filters(auth_client, user_id):
    today = date.today()
    month = today.month - 6
    year = today.year
    if month <= 0:
        month += 12
        year -= 1
    start = date(year, month, 1)
    stats = get_summary_stats(user_id, date_from=start, date_to=today)
    assert stats["total_spent"] == pytest.approx(285.50)


def test_active_preset_highlighted_this_month(auth_client):
    today = date.today()
    start = date(today.year, today.month, 1)
    resp = auth_client.get(
        "/profile",
        query_string={"date_from": start.isoformat(), "date_to": today.isoformat()},
    )
    html = resp.data.decode("utf-8")
    # Active class should be present on This Month link
    assert 'class="filter-preset active"' in html
    assert "This Month" in html


# --------------------------------------------------------------------------- #
# Custom date range
# --------------------------------------------------------------------------- #

def test_custom_date_range_valid_filters_all_sections(auth_client, user_id):
    # 2026-10-05 to 2026-10-07 includes 3 expenses: 30 + 40 + 20 = 90
    resp = auth_client.get(
        "/profile",
        query_string={"date_from": "2026-10-05", "date_to": "2026-10-07"},
    )
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    # Summary stats
    assert "90.00" in html
    # Transactions table should contain the three dates and not 2026-10-01
    # Dates now displayed in dd-mm-yyyy format
    assert "05-10-2026" in html
    assert "06-10-2026" in html
    assert "07-10-2026" in html
    assert "Lunch" not in html  # 2026-10-01 expense excluded
    # Custom inputs pre-filled
    assert 'name="date_from"' in html
    assert 'value="2026-10-05"' in html
    assert 'value="2026-10-07"' in html
    # Query helper verification
    stats = get_summary_stats(user_id, date_from=date(2026, 10, 5), date_to=date(2026, 10, 7))
    assert stats["total_spent"] == pytest.approx(90.0)
    assert stats["transaction_count"] == 3
    txs = get_recent_transactions(user_id, date_from=date(2026, 10, 5), date_to=date(2026, 10, 7))
    assert len(txs) == 3
    cats = get_category_breakdown(user_id, date_from=date(2026, 10, 5), date_to=date(2026, 10, 7))
    # Should have Entertainment, Shopping, Other
    assert len(cats) == 3


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #

def test_date_from_after_date_to_shows_flash_error_and_fallback(auth_client):
    resp = auth_client.get(
        "/profile",
        query_string={"date_from": "2026-10-10", "date_to": "2026-10-01"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert "Start date must be before end date." in html
    # Fallback to unfiltered view
    assert "285.50" in html


def test_malformed_dates_fallback_to_unfiltered(auth_client):
    resp = auth_client.get(
        "/profile",
        query_string={"date_from": "not-a-date", "date_to": "2026-13-40"},
    )
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    # Should not crash and should show unfiltered totals
    assert "285.50" in html
    assert "₹" in html


# --------------------------------------------------------------------------- #
# Empty state
# --------------------------------------------------------------------------- #

def test_empty_state_no_expenses_in_range(auth_client, user_id):
    resp = auth_client.get(
        "/profile",
        query_string={"date_from": "2025-01-01", "date_to": "2025-01-31"},
    )
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    # Summary shows zero
    assert "₹0.00" in html
    # Transaction count zero
    assert ">0<" in html or "Transactions" in html
    # Query helpers confirm empty
    stats = get_summary_stats(user_id, date_from=date(2025, 1, 1), date_to=date(2025, 1, 31))
    assert stats["total_spent"] == 0
    assert stats["transaction_count"] == 0
    assert stats["top_category"] == "—"
    assert get_recent_transactions(user_id, date_from=date(2025, 1, 1), date_to=date(2025, 1, 31)) == []
    assert get_category_breakdown(user_id, date_from=date(2025, 1, 1), date_to=date(2025, 1, 31)) == []


# --------------------------------------------------------------------------- #
# Currency symbol
# --------------------------------------------------------------------------- #

def test_currency_symbol_present_in_filtered_views(auth_client):
    resp = auth_client.get(
        "/profile",
        query_string={"date_from": "2026-10-01", "date_to": "2026-10-08"},
    )
    html = resp.data.decode("utf-8")
    # ₹ should appear in summary, transactions and breakdown
    assert html.count("₹") >= 3


# --------------------------------------------------------------------------- #
# Query helper date filtering
# --------------------------------------------------------------------------- #

def test_query_helpers_respect_date_range(user_id):
    # Full range
    stats_all = get_summary_stats(user_id)
    assert stats_all["total_spent"] == pytest.approx(285.50)

    # Narrow range
    stats_narrow = get_summary_stats(user_id, date_from=date(2026, 10, 1), date_to=date(2026, 10, 3))
    # 10.5 + 20 + 100 = 130.5
    assert stats_narrow["total_spent"] == pytest.approx(130.5)
    assert stats_narrow["transaction_count"] == 3

    txs = get_recent_transactions(user_id, date_from=date(2026, 10, 1), date_to=date(2026, 10, 3))
    assert len(txs) == 3
    dates = [t["date"] for t in txs]
    assert all(d >= "2026-10-01" and d <= "2026-10-03" for d in dates)

    cats = get_category_breakdown(user_id, date_from=date(2026, 10, 1), date_to=date(2026, 10, 3))
    assert len(cats) > 0
    # Percentages sum to 100
    assert sum(c["pct"] for c in cats) == 100
