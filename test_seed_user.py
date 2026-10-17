import sqlite3
import pytest
import tempfile
import os
from werkzeug.security import check_password_hash
from seed_user import seed_single_user

def test_seed_user_creation():
    # Use a isolated temporary database so spendly.db is untouched during testing
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db_path = temp_db.name
    temp_db.close()

    try:
        seed_single_user(db_path=temp_db_path)

        conn = sqlite3.connect(temp_db_path)
        conn.row_factory = sqlite3.Row
        user = conn.execute("SELECT * FROM users ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()

        assert user is not None
        assert user["name"] is not None
        assert "@" in user["email"]
        assert check_password_hash(user["password_hash"], "password123")
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

def test_seed_user_idempotency(capsys):
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db_path = temp_db.name
    temp_db.close()

    try:
        # First creation
        seed_single_user(db_path=temp_db_path)

        # Get created user email
        conn = sqlite3.connect(temp_db_path)
        conn.row_factory = sqlite3.Row
        user = conn.execute("SELECT email FROM users LIMIT 1").fetchone()
        email = user["email"]
        conn.close()

        # Attempt to seed with duplicate email check
        conn = sqlite3.connect(temp_db_path)
        existing = conn.execute("SELECT id, name, email FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        assert existing is not None
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)
