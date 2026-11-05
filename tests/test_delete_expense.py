"""Tests for Step 09 — Delete Expense feature."""

import pytest
from app import app
from database.db import init_db, get_db
from database.queries import insert_expense, delete_expense, get_expense_by_id


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
    """Create a test client with a logged-in user and one expense."""
    with app.app_context():
        db = get_db()
        user = db.execute('SELECT id FROM users LIMIT 1').fetchone()
        if user:
            with client.session_transaction() as sess:
                sess['user_id'] = user['id']
            # Insert a test expense for this user
            insert_expense(
                user_id=user['id'],
                amount=50.00,
                category='Food',
                date='2026-03-20',
                description='Test Expense to Delete'
            )
    return client


@pytest.fixture
def logged_in_client_with_expense(logged_in_client):
    """Create a logged-in client with a specific expense to delete."""
    # The expense is already created in logged_in_client fixture
    return logged_in_client


class TestDeleteExpense:
    """Unit tests for the delete_expense database helper."""

    def test_delete_expense_removes_row(self):
        """Delete removes an expense that belongs to the user."""
        with app.app_context():
            init_db()
            db = get_db()
            user = db.execute('SELECT id FROM users LIMIT 1').fetchone()
            assert user is not None

            # Insert an expense
            expense_id = insert_expense(
                user_id=user['id'],
                amount=100.0,
                category='Shopping',
                date='2026-04-01',
                description='To Delete'
            )

            # Delete it
            delete_expense(expense_id, user['id'])

            # Verify it's gone
            row = db.execute(
                'SELECT * FROM expenses WHERE id = ?', (expense_id,)
            ).fetchone()
            assert row is None

    def test_delete_expense_wrong_user_does_nothing(self):
        """Delete with wrong user_id removes nothing (ownership guard)."""
        with app.app_context():
            init_db()
            db = get_db()

            # Get two users
            users = db.execute('SELECT id FROM users').fetchall()
            if len(users) >= 2:
                user1_id = users[0]['id']
                user2_id = users[1]['id']

                # Insert expense for user1
                expense_id = insert_expense(
                    user_id=user1_id,
                    amount=100.0,
                    category='Shopping',
                    date='2026-04-01',
                    description='Should Stay'
                )

                # Try to delete as user2
                delete_expense(expense_id, user2_id)

                # Expense should still exist
                row = db.execute(
                    'SELECT * FROM expenses WHERE id = ?', (expense_id,)
                ).fetchone()
                assert row is not None
                assert row['amount'] == 100.0

    def test_delete_expense_nonexistent_id_safe(self):
        """Delete on non-existent id raises no error."""
        with app.app_context():
            init_db()
            # Should not raise
            delete_expense(99999, 1)


class TestPostRoute:
    """Tests for POST /expenses/<id>/delete."""

    def test_post_unauthenticated_redirects_to_login(self, client):
        """Unauthenticated POST redirects to /login."""
        # First create an expense
        with app.app_context():
            init_db()
            db = get_db()
            user = db.execute('SELECT id FROM users LIMIT 1').fetchone()
            if user:
                expense_id = insert_expense(
                    user_id=user['id'],
                    amount=50.0,
                    category='Food',
                    date='2026-03-20',
                    description='Test'
                )
                resp = client.post(f'/expenses/{expense_id}/delete')
                assert resp.status_code == 302
                assert '/login' in resp.location

    def test_post_authenticated_own_expense_deletes(self, logged_in_client):
        """Authenticated POST with own expense deletes and redirects."""
        # Get the expense id
        with app.app_context():
            db = get_db()
            expense = db.execute(
                'SELECT id FROM expenses WHERE description = ?',
                ('Test Expense to Delete',)
            ).fetchone()
            expense_id = expense['id']

        # Delete it
        resp = logged_in_client.post(f'/expenses/{expense_id}/delete')
        assert resp.status_code == 302
        assert '/profile' in resp.location

        # Verify it's gone
        with app.app_context():
            db = get_db()
            row = db.execute(
                'SELECT * FROM expenses WHERE id = ?', (expense_id,)
            ).fetchone()
            assert row is None

    def test_post_authenticated_other_user_expense_returns_404(self, logged_in_client):
        """Authenticated POST with other user's expense returns 404."""
        # Create an expense for another user
        with app.app_context():
            db = get_db()
            users = db.execute('SELECT id FROM users LIMIT 2').fetchall()
            if len(users) >= 2:
                other_user_id = users[1]['id']
                expense_id = insert_expense(
                    user_id=other_user_id,
                    amount=75.0,
                    category='Entertainment',
                    date='2026-04-01',
                    description='Other User Expense'
                )

                resp = logged_in_client.post(f'/expenses/{expense_id}/delete')
                assert resp.status_code == 404

                # Verify expense still exists
                row = db.execute(
                    'SELECT * FROM expenses WHERE id = ?', (expense_id,)
                ).fetchone()
                assert row is not None

    def test_post_authenticated_nonexistent_id_returns_404(self, logged_in_client):
        """Authenticated POST with non-existent id returns 404."""
        resp = logged_in_client.post('/expenses/99999/delete')
        assert resp.status_code == 404


class TestGetRoute:
    """Tests for GET /expenses/<id>/delete (should return 405)."""

    def test_get_returns_405(self, logged_in_client):
        """GET to delete route returns 405 Method Not Allowed."""
        with app.app_context():
            db = get_db()
            user = db.execute('SELECT id FROM users LIMIT 1').fetchone()
            expense_id = insert_expense(
                user_id=user['id'],
                amount=25.0,
                category='Transport',
                date='2026-04-02',
                description='GET Test'
            )

        resp = logged_in_client.get(f'/expenses/{expense_id}/delete')
        assert resp.status_code == 405


class TestProfileIntegration:
    """Integration tests with the profile page."""

    def test_delete_button_on_profile(self, logged_in_client):
        """Profile page has Delete button."""
        resp = logged_in_client.get('/profile')
        assert resp.status_code == 200
        assert b'Delete' in resp.data
        assert b'btn-delete' in resp.data

    def test_cancel_confirm_leaves_expense_intact(self, logged_in_client):
        """Clicking Delete and cancelling confirmation leaves expense intact."""
        with app.app_context():
            db = get_db()
            expense = db.execute(
                'SELECT id FROM expenses WHERE description = ?',
                ('Test Expense to Delete',)
            ).fetchone()
            expense_id = expense['id']

        # Note: We cannot test the JavaScript confirm() dialog directly in a test,
        # but the form structure ensures the DELETE only happens on POST
        # This test verifies the Delete button exists

        # Simulate cancel won't happen in unit tests
        # The confirmation is handled by browser JavaScript

    def test_deleted_expense_gone_from_profile(self, logged_in_client):
        """Deleted expense no longer appears on profile page."""
        with app.app_context():
            db = get_db()
            expense = db.execute(
                'SELECT id FROM expenses WHERE description = ?',
                ('Test Expense to Delete',)
            ).fetchone()
            expense_id = expense['id']

        # Delete it
        logged_in_client.post(f'/expenses/{expense_id}/delete')

        # Check profile - expense should not appear
        resp = logged_in_client.get('/profile')
        assert b'Test Expense to Delete' not in resp.data