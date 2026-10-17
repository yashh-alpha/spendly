import sqlite3
import random
from werkzeug.security import generate_password_hash
from database.db import DATABASE

# Lists of Indian names and email domains for randomization
FIRST_NAMES = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan", "Diya", "Ananya", "Aadhya", "Saanvi", "Kavya", "Aarohi", "Pari", "Anika", "Navya", "Riya"]
LAST_NAMES = ["Sharma", "Verma", "Gupta", "Malhotra", "Mehra", "Tiwari", "Jha", "Bhatt", "Reddy", "Rao", "Patel", "Shah", "Joshi", "Kumar", "Singh", "Das", "Choudhury", "Mukherjee", "Chatterjee", "Nair"]
EMAIL_DOMAINS = ["example.com", "spendly.in", "test.co.in", "mail.in", "sample.org"]

def generate_indian_user():
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    name = f"{first} {last}"

    # Generate unique-ish email using name and random digits
    email_user = f"{first.lower()}.{last.lower()}{random.randint(100, 999)}"
    domain = random.choice(EMAIL_DOMAINS)
    email = f"{email_user}@{domain}"

    return name, email

def seed_single_user(db_path=None):
    target_db = db_path or DATABASE
    # Ensure database tables exist
    conn = sqlite3.connect(target_db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    # Create tables if they don't exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
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
    conn.commit()

    # Try generating a unique Indian name and email until we find one that doesn't exist,
    # or if we want to ensure idempotency when a specific email is already tested/present.
    # The requirement states: "If the email already exists, try another email."
    # Let's loop until an available email is found.
    name, email = None, None
    for _ in range(50):
        candidate_name, candidate_email = generate_indian_user()
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (candidate_email,)).fetchone()
        if not existing:
            name, email = candidate_name, candidate_email
            break

    if not email:
        # Fallback if loop exhausts
        name = "Rajesh Sharma"
        email = f"rajesh.sharma{random.randint(10000, 99999)}@example.com"

    # Check if this exact email already exists (just in case)
    existing = conn.execute("SELECT id, name, email FROM users WHERE email = ?", (email,)).fetchone()

    if existing:
        print(f"User already exists: ID {existing['id']}, Name: {existing['name']}, Email: {existing['email']}")
        conn.close()
        return False
    else:
        hashed_password = generate_password_hash("password123")
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, hashed_password)
        )
        conn.commit()
        user_id = cursor.lastrowid
        print(f"Successfully created test user: ID {user_id}, Name: {name}, Email: {email}")
        conn.close()
        return True

if __name__ == "__main__":
    seed_single_user()
