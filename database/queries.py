"""Pure query helpers for the Spendly profile page.

Each function opens its own SQLite connection, executes a parameterised query,
closes the connection, and returns plain Python data (dicts / lists).
No Flask request/session handling lives here — callers pass a ``user_id``.
"""

import sqlite3
from datetime import datetime

from database.db import DATABASE


def _get_connection():
    """Open a new SQLite connection with row factory and FK enforcement."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _format_member_since(created_at):
    """Format a SQLite datetime string as 'Month YYYY' (e.g. 'October 2026')."""
    dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%B %Y")


def get_user_by_id(user_id):
    """Return a dict with name, email, member_since for the given user.

    Returns ``None`` if no user exists with that id.
    """
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

        if row is None:
            return None

        return {
            "name": row["name"],
            "email": row["email"],
            "member_since": _format_member_since(row["created_at"]),
        }
    finally:
        conn.close()


def get_summary_stats(user_id):
    """Return total_spent, transaction_count, and top_category for a user.

    If the user has no expenses, returns zeros and ``"—"`` for top_category.
    """
    conn = _get_connection()
    try:
        row = conn.execute(
            """
            SELECT
                COALESCE(SUM(amount), 0) AS total_spent,
                COUNT(*)                AS transaction_count
            FROM expenses
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
        total_spent = row["total_spent"]
        transaction_count = row["transaction_count"]

        if transaction_count == 0:
            return {"total_spent": 0, "transaction_count": 0, "top_category": "—"}

        top_row = conn.execute(
            """
            SELECT category
            FROM expenses
            WHERE user_id = ?
            GROUP BY category
            ORDER BY SUM(amount) DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

        return {
            "total_spent": total_spent,
            "transaction_count": transaction_count,
            "top_category": top_row["category"],
        }
    finally:
        conn.close()


def get_recent_transactions(user_id, limit=10):
    """Return the user's most recent expenses, newest-first.

    Each item is a dict with ``date``, ``description``, ``category``, ``amount``.
    Returns an empty list if the user has no expenses.
    """
    conn = _get_connection()
    try:
        rows = conn.execute(
            """
            SELECT date, description, category, amount
            FROM expenses
            WHERE user_id = ?
            ORDER BY date DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()

        return [
            {
                "date": row["date"],
                "description": row["description"],
                "category": row["category"],
                "amount": row["amount"],
            }
            for row in rows
        ]
    finally:
        conn.close()


def get_category_breakdown(user_id):
    """Return per-category totals for a user, ordered by amount descending.

    Each item is a dict with ``name``, ``amount``, and ``pct`` (integer
    percentage of the user's total spend).  Percentages are rounded and the
    largest category absorbs any remainder so the values sum to 100.

    Returns an empty list if the user has no expenses.
    """
    conn = _get_connection()
    try:
        rows = conn.execute(
            """
            SELECT category, SUM(amount) AS amount
            FROM expenses
            WHERE user_id = ?
            GROUP BY category
            ORDER BY amount DESC
            """,
            (user_id,),
        ).fetchall()

        if not rows:
            return []

        total = sum(row["amount"] for row in rows)

        breakdown = []
        for row in rows:
            pct = int(round(row["amount"] / total * 100))
            breakdown.append(
                {"name": row["category"], "amount": row["amount"], "pct": pct}
            )

        # Adjust the largest category to absorb any rounding remainder so the
        # percentages sum to exactly 100.
        diff = 100 - sum(item["pct"] for item in breakdown)
        if diff != 0 and breakdown:
            breakdown[0]["pct"] += diff

        return breakdown
    finally:
        conn.close()