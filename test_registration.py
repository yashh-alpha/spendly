import pytest
import sqlite3
import tempfile
import os
from werkzeug.security import check_password_hash
from app import app
from database.db import init_db

@pytest.fixture
def client():
    # Setup temporary database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)

    app.config["TESTING"] = True
    app.config["DATABASE"] = db_path

    import database.db
    old_db = database.db.DATABASE
    database.db.DATABASE = db_path

    with app.app_context():
        init_db()

    with app.test_client() as client:
        yield client

    # Cleanup
    database.db.DATABASE = old_db
    if os.path.exists(db_path):
        os.unlink(db_path)

def test_get_register_page(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Create your account" in response.data

def test_register_success(client):
    response = client.post(
        "/register",
        data={
            "name": "Aarav Patel",
            "email": "aarav@example.com",
            "password": "password123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Aarav Patel" in response.data
    assert b"Member since" in response.data

    # Verify user saved in DB
    import database.db
    conn = sqlite3.connect(database.db.DATABASE)
    conn.row_factory = sqlite3.Row
    user = conn.execute("SELECT * FROM users WHERE email = ?", ("aarav@example.com",)).fetchone()
    conn.close()

    assert user is not None
    assert user["name"] == "Aarav Patel"
    assert check_password_hash(user["password_hash"], "password123")

def test_register_duplicate_email(client):
    # First registration
    client.post(
        "/register",
        data={
            "name": "First User",
            "email": "duplicate@example.com",
            "password": "password123",
        },
    )

    # Logout to clear session from first registration
    client.get("/logout")

    # Second registration with same email
    response = client.post(
        "/register",
        data={
            "name": "Second User",
            "email": "duplicate@example.com",
            "password": "password456",
        },
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert b"Email already registered" in response.data

def test_register_short_password(client):
    response = client.post(
        "/register",
        data={
            "name": "Short Pass",
            "email": "short@example.com",
            "password": "short",
        },
    )
    assert response.status_code == 200
    assert b"Password must be at least 8 characters" in response.data

def test_register_invalid_email(client):
    response = client.post(
        "/register",
        data={
            "name": "Bad Email",
            "email": "not-an-email",
            "password": "password123",
        },
    )
    assert response.status_code == 200
    assert b"Please enter a valid email address" in response.data

def test_landing_redirect_when_logged_in(client):
    # Register to establish session
    client.post(
        "/register",
        data={
            "name": "Session User",
            "email": "session@example.com",
            "password": "password123",
        },
        follow_redirects=True,
    )

    # Visiting landing page should redirect to profile
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")
