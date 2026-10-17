import sqlite3
from flask import g
from werkzeug.security import generate_password_hash

DATABASE = 'spendly.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
    return db

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    db.commit()

def seed_db():
    db = get_db()
    # Check if users table already has data
    user = db.execute("SELECT id FROM users LIMIT 1").fetchone()
    if user:
        return

    # Insert demo user
    hashed_password = generate_password_hash('demo123')
    cursor = db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", hashed_password)
    )
    user_id = cursor.lastrowid

    # Insert 8 sample expenses
    expenses = [
        (user_id, 10.5, "Food", "2026-10-01", "Lunch"),
        (user_id, 20.0, "Transport", "2026-10-02", "Taxi"),
        (user_id, 100.0, "Bills", "2026-10-03", "Internet"),
        (user_id, 50.0, "Health", "2026-10-04", "Pharmacy"),
        (user_id, 30.0, "Entertainment", "2026-10-05", "Movie"),
        (user_id, 40.0, "Shopping", "2026-10-06", "Groceries"),
        (user_id, 20.0, "Other", "2026-10-07", "Gift"),
        (user_id, 15.0, "Food", "2026-10-08", "Coffee")
    ]
    db.executemany("""
        INSERT INTO expenses (user_id, amount, category, date, description)
        VALUES (?, ?, ?, ?, ?)
    """, expenses)
    db.commit()
