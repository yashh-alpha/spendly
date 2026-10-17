import pytest
from app import app
from database.db import get_db, init_db

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.app_context():
        init_db()
    with app.test_client() as client:
        yield client

def test_login_get(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Sign in" in response.data

def test_login_success(client):
    # Test logging in with seeded demo user
    response = client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Dashboard" in response.data
    assert b"Demo User" in response.data

def test_login_invalid_password(client):
    response = client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "wrongpassword"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Incorrect email or password" in response.data

def test_login_nonexistent_email(client):
    response = client.post("/login", data={
        "email": "nonexistent@spendly.com",
        "password": "somepassword"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Incorrect email or password" in response.data

def test_logout(client):
    # First login
    client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123"
    }, follow_redirects=True)

    # Then logout
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"Track every rupee" in response.data # Landed on landing page

def test_logged_in_user_redirected_from_login_and_register(client):
    # Login first
    client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123"
    }, follow_redirects=True)

    # Try accessing /login
    response = client.get("/login", follow_redirects=True)
    assert response.status_code == 200
    assert b"Dashboard" in response.data

    # Try accessing /register
    response = client.get("/register", follow_redirects=True)
    assert response.status_code == 200
    assert b"Dashboard" in response.data

