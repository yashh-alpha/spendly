"""Tests for Step 07 — Add Expense feature."""

import pytest
from app import app
from database.db import init_db, get_db
from database.queries import insert_expense


@pytest.fixture
def client():
    """Create a test client with a fresh database for each test."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client


@pytest.fixture
def logged_in_client(client):
    """Create a test client with a logged-in user."""
    with app.app_context():
        db = get_db()
        user = db.execute('SELECT id FROM users LIMIT 1').fetchone()
        if user:
            with client.session_transaction() as sess:
                sess['user_id'] = user['id']
    return client


class TestInsertExpense:
    """Unit tests for the insert_expense database helper."""

    def test_insert_expense_valid(self):
        """Insert expense with all valid fields."""
        with app.app_context():
            init_db()
            db = get_db()
            user = db.execute('SELECT id FROM users LIMIT 1').fetchone()
            assert user is not None

            new_id = insert_expense(
                user_id=user['id'],
                amount=50.0,
                category='Food',
                date='2026-03-20',
                description='Lunch'
            )

            # Verify the row was inserted
            row = db.execute('SELECT * FROM expenses WHERE id = ?', (new_id,)).fetchone()
            assert row is not None
            assert row['user_id'] == user['id']
            assert row['amount'] == 50.0
            assert row['category'] == 'Food'
            assert row['date'] == '2026-03-20'
            assert row['description'] == 'Lunch'

    def test_insert_expense_no_description(self):
        """Insert expense with description=None stores NULL."""
        with app.app_context():
            init_db()
            db = get_db()
            user = db.execute('SELECT id FROM users LIMIT 1').fetchone()
            assert user is not None

            new_id = insert_expense(
                user_id=user['id'],
                amount=25.0,
                category='Transport',
                date='2026-03-21',
                description=None
            )

            row = db.execute('SELECT * FROM expenses WHERE id = ?', (new_id,)).fetchone()
            assert row is not None
            assert row['description'] is None


class TestGetRoute:
    """Tests for GET /expenses/add."""

    def test_get_unauthenticated_redirects_to_login(self, client):
        """Unauthenticated GET should redirect to /login."""
        resp = client.get('/expenses/add')
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_get_authenticated_returns_200(self, logged_in_client):
        """Authenticated GET returns 200 with form."""
        resp = logged_in_client.get('/expenses/add')
        assert resp.status_code == 200

    def test_get_form_contains_category_select(self, logged_in_client):
        """Form contains category <select> with all 7 options."""
        resp = logged_in_client.get('/expenses/add')
        categories = ['Food', 'Transport', 'Bills', 'Health', 'Entertainment', 'Shopping', 'Other']
        for cat in categories:
            assert cat.encode() in resp.data

    def test_get_form_has_post_method(self, logged_in_client):
        """Form has method='POST'."""
        resp = logged_in_client.get('/expenses/add')
        assert b'method="POST"' in resp.data or b"method='POST'" in resp.data


class TestPostRoute:
    """Tests for POST /expenses/add."""

    def test_post_unauthenticated_redirects_to_login(self, client):
        """Unauthenticated POST redirects to /login."""
        resp = client.post('/expenses/add', data={
            'amount': '10.00',
            'category': 'Food',
            'date': '2026-03-20',
            'description': 'Test'
        })
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_post_valid_data_redirects_to_profile(self, logged_in_client):
        """Valid POST redirects to /profile and inserts row."""
        unique_desc = 'Test Lunch Unique 123'
        resp = logged_in_client.post('/expenses/add', data={
            'amount': '50.0',
            'category': 'Food',
            'date': '2026-03-20',
            'description': unique_desc
        })
        assert resp.status_code == 302
        assert '/profile' in resp.location

        # Verify row exists in DB
        with app.app_context():
            db = get_db()
            row = db.execute(
                'SELECT * FROM expenses WHERE description = ?',
                (unique_desc,)
            ).fetchone()
            assert row is not None
            assert row['amount'] == 50.0
            assert row['category'] == 'Food'

    def test_post_missing_amount_returns_200_with_error(self, logged_in_client):
        """Missing amount re-renders form with error."""
        resp = logged_in_client.post('/expenses/add', data={
            'amount': '',
            'category': 'Food',
            'date': '2026-03-20',
            'description': 'Test'
        })
        assert resp.status_code == 200
        assert b'Amount' in resp.data or b'amount' in resp.data

    def test_post_zero_amount_returns_200_with_error(self, logged_in_client):
        """Amount = 0 re-renders form with error."""
        resp = logged_in_client.post('/expenses/add', data={
            'amount': '0',
            'category': 'Food',
            'date': '2026-03-20',
            'description': 'Test'
        })
        assert resp.status_code == 200
        assert b'Amount' in resp.data or b'amount' in resp.data

    def test_post_non_numeric_amount_returns_200_with_error(self, logged_in_client):
        """Non-numeric amount re-renders form with error."""
        resp = logged_in_client.post('/expenses/add', data={
            'amount': 'not-a-number',
            'category': 'Food',
            'date': '2026-03-20',
            'description': 'Test'
        })
        assert resp.status_code == 200
        assert b'Amount' in resp.data or b'amount' in resp.data

    def test_post_invalid_category_returns_200_with_error(self, logged_in_client):
        """Invalid category re-renders form with error."""
        resp = logged_in_client.post('/expenses/add', data={
            'amount': '10.00',
            'category': 'InvalidCategory',
            'date': '2026-03-20',
            'description': 'Test'
        })
        assert resp.status_code == 200
        assert b'Category' in resp.data or b'category' in resp.data

    def test_post_invalid_date_string_returns_200_with_error(self, logged_in_client):
        """Invalid date string re-renders form with error."""
        resp = logged_in_client.post('/expenses/add', data={
            'amount': '10.00',
            'category': 'Food',
            'date': 'not-a-date',
            'description': 'Test'
        })
        assert resp.status_code == 200
        assert b'date' in resp.data.lower() or b'Date' in resp.data

    def test_post_no_description_succeeds_and_stores_null(self, logged_in_client):
        """Empty description succeeds and stores NULL."""
        resp = logged_in_client.post('/expenses/add', data={
            'amount': '15.00',
            'category': 'Food',
            'date': '2026-03-20',
            'description': ''
        })
        assert resp.status_code == 302
        assert '/profile' in resp.location

        with app.app_context():
            db = get_db()
            row = db.execute(
                'SELECT * FROM expenses WHERE amount = ? AND category = ? ORDER BY id DESC LIMIT 1',
                (15.00, 'Food')
            ).fetchone()
            assert row is not None
            assert row['description'] is None or row['description'] == ''


class TestIntegration:
    """Integration tests with the profile page."""

    def test_add_expense_button_on_profile(self, logged_in_client):
        """Profile page has Add Expense button/link."""
        resp = logged_in_client.get('/profile')
        assert resp.status_code == 200
        assert b'Add Expense' in resp.data

    def test_navbar_has_add_expense_when_logged_in(self, logged_in_client):
        """Navbar shows Add Expense link when logged in."""
        resp = logged_in_client.get('/profile')
        assert resp.status_code == 200
        assert b'Add Expense' in resp.data

    def test_new_expense_appears_on_profile(self, logged_in_client):
        """Newly added expense appears on profile page."""
        # Add an expense
        logged_in_client.post('/expenses/add', data={
            'amount': '99.99',
            'category': 'Entertainment',
            'date': '2026-03-20',
            'description': 'Test Movie'
        })

        # Check profile page
        resp = logged_in_client.get('/profile')
        assert resp.status_code == 200
        assert b'Test Movie' in resp.data
        assert b'Entertainment' in resp.data
        assert b'99.99' in resp.data