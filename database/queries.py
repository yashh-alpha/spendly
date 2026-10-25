"""Pure query helpers for the Spendly expense tracker.

Each function opens its own SQLite connection, executes a parameterised query,
closes the connection, and returns plain Python data (dicts / lists).
No Flask request/session handling lives here — callers pass a ``user_id``.
"""

import sqlite3
from datetime import date, datetime

from database.db import DATABASE


def _build_date_filter(date_from: date | None, date_to: date | None) -> tuple[str, list]:
    """Returns (where_sql_fragment, params) for date range filtering.

    Example: date_from=2026-10-01, date_to=2026-10-31 →
    ("date >= ? AND date <= ?", ["2026-10-01", "2026-10-31"])
    """
    clauses = []
    params = []
    if date_from:
        clauses.append("date >= ?")
        params.append(str(date_from))
    if date_to:
        clauses.append("date <= ?")
        params.append(str(date_to))
    return (" AND ".join(clauses), params)


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


def get_summary_stats(user_id, date_from=None, date_to=None):
    """Return total_spent, transaction_count, and top_category for a user.

    If the user has no expenses, returns zeros and ``"—"`` for top_category.
    Optional date_from and date_to parameters filter by date range (inclusive).
    """
    conn = _get_connection()
    try:
        where_clauses = ["user_id = ?"]
        params = [user_id]

        if date_from or date_to:
            date_where, date_params = _build_date_filter(date_from, date_to)
            where_clauses.append(date_where)
            params.extend(date_params)

        where_sql = " AND ".join(where_clauses)

        row = conn.execute(
            f"""
            SELECT
                COALESCE(SUM(amount), 0) AS total_spent,
                COUNT(*)                AS transaction_count
            FROM expenses
            WHERE {where_sql}
            """,
            params,
        ).fetchone()
        total_spent = row["total_spent"]
        transaction_count = row["transaction_count"]

        if transaction_count == 0:
            return {"total_spent": 0, "transaction_count": 0, "top_category": "—"}

        top_row = conn.execute(
            f"""
            SELECT category
            FROM expenses
            WHERE {where_sql}
            GROUP BY category
            ORDER BY SUM(amount) DESC
            LIMIT 1
            """,
            params,
        ).fetchone()

        return {
            "total_spent": total_spent,
            "transaction_count": transaction_count,
            "top_category": top_row["category"],
        }
    finally:
        conn.close()


def get_recent_transactions(user_id, limit=10, date_from=None, date_to=None):
    """Return the user's most recent expenses, newest-first.

    Each item is a dict with ``date``, ``description``, ``category``, ``amount``.
    Returns an empty list if the user has no expenses.
    Optional date_from and date_to parameters filter by date range (inclusive).
    """
    conn = _get_connection()
    try:
        where_clauses = ["user_id = ?"]
        params = [user_id]

        if date_from or date_to:
            date_where, date_params = _build_date_filter(date_from, date_to)
            where_clauses.append(date_where)
            params.extend(date_params)

        where_sql = " AND ".join(where_clauses)
        params.append(limit)

        rows = conn.execute(
            f"""
            SELECT date, description, category, amount
            FROM expenses
            WHERE {where_sql}
            ORDER BY date DESC
            LIMIT ?
            """,
            params,
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


def get_category_breakdown(user_id, date_from=None, date_to=None):
    """Return per-category totals for a user, ordered by amount descending.

    Each item is a dict with ``name``, ``amount``, and ``pct`` (integer
    percentage of the user's total spend).  Percentages are rounded and the
    largest category absorbs any remainder so the values sum to 100.

    Returns an empty list if the user has no expenses.
    Optional date_from and date_to parameters filter by date range (inclusive).
    """
    conn = _get_connection()
    try:
        where_clauses = ["user_id = ?"]
        params = [user_id]

        if date_from or date_to:
            date_where, date_params = _build_date_filter(date_from, date_to)
            where_clauses.append(date_where)
            params.extend(date_params)

        where_sql = " AND ".join(where_clauses)

        rows = conn.execute(
            f"""
            SELECT category, SUM(amount) AS amount
            FROM expenses
            WHERE {where_sql}
            GROUP BY category
            ORDER BY amount DESC
            """,
            params,
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


def insert_expense(user_id, amount, category, date, description=None):
    """Insert a new expense for the given user.

    Args:
        user_id: The user's database id.
        amount: Positive dollar amount (float).
        category: Must be one of: Food, Transport, Bills, Health,
            Entertainment, Shopping, Other.
        date: ISO date string YYYY-MM-DD.
        description: Optional textual description; stored as NULL if blank.

    Returns:
        The newly inserted expense row id (integer).
    """
    conn = _get_connection()
    try:
        description = description.strip() if description and description.strip() else None
        cursor = conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date, description),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()