# Plan: 01-Database-Setup

## Context
Implement the database data layer for the Spendly expense tracker, as specified in `.claude/specs/database-setup.md`. This involves setting up SQLite connectivity, table schemas, and seeding data.

## Implementation Steps

### 1. Update `database/db.py`
*   Implement `get_db()`:
    *   Connect to `spendly.db`.
    *   Configure `row_factory = sqlite3.Row`.
    *   Enable `PRAGMA foreign_keys = ON`.
*   Implement `init_db()`:
    *   Create `users` table with columns: `id`, `name`, `email` (unique), `password_hash`, `created_at`.
    *   Create `expenses` table with columns: `id`, `user_id`, `amount`, `category`, `date`, `description`, `created_at`.
*   Implement `seed_db()`:
    *   Check for existing user to avoid duplication.
    *   Insert demo user (name: "Demo User", email: "demo@spendly.com", hashed password using `werkzeug.security`).
    *   Insert 8 sample expenses covering all specified categories.

### 2. Update `app.py`
*   Import `get_db`, `init_db`, `seed_db` from `database.db`.
*   Initialize database context on startup:
    *   Add `init_db()` and `seed_db()` calls inside `app.app_context()` when starting the application.

## Verification Plan
*   Start the app.
*   Check that `spendly.db` is generated.
*   Connect to the database using `sqlite3` CLI and verify:
    *   Tables exist (`users`, `expenses`).
    *   Demo user exists in `users`.
    *   8 sample expenses exist in `expenses`.
    *   Foreign keys are working.
*   Verify no duplicate seed data on repeated app restarts.
