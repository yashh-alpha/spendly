# Spendly

A clean, lightweight personal expense tracker built with **Flask** and **SQLite**.
Track your spending, categorize your expenses, and see where your money goes at a glance.

---

## 🚀 Features

- **User accounts** — Register, login, and logout with secure password hashing.
- **Expense CRUD** — Add, edit, and delete your expenses with full ownership checks.
- **Smart validation** — Server-side validation for amounts, categories, dates, and descriptions.
- **Category breakdown** — See exactly how much you spend on Food, Transport, Bills, Health, Entertainment, Shopping, and Other.
- **Date filtering** — Filter your history by presets (This Month, Last 3 Months, Last 6 Months, All Time) or a custom date range.
- **Summary stats** — Total spent, transaction count, and top category, all filterable by date.
- **Analytics dashboard** — Visualize your spending patterns over time.
- **Responsive UI** — Clean, modern templates that work on desktop and mobile.

---

## 📁 Project Structure

```
spendly/
├── app.py                  # Flask application + all routes
├── requirements.txt        # Python dependencies
├── database/
│   ├── __init__.py
│   ├── db.py               # DB connection helpers (get_db, init_db, seed_db)
│   └── queries.py          # Pure query functions (no Flask/HTTP logic)
├── templates/              # Jinja2 HTML templates
│   ├── base.html
│   ├── landing.html
│   ├── register.html
│   ├── login.html
│   ├── dashboard.html
│   ├── profile.html
│   ├── analytics.html
│   ├── add_expense.html
│   ├── edit_expense.html
│   ├── terms.html
│   └── privacy.html
├── static/                 # CSS, JS, images
├── tests/                  # Pytest test suite
└── seed_user.py            # Standalone user seeding script
```

---

## ⚙️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Flask 3.1.3 |
| Database | SQLite (via `sqlite3`) |
| Password hashing | Werkzeug (`generate_password_hash` / `check_password_hash`) |
| Testing | pytest 8.3.5 + pytest-flask 1.3.0 |
| Frontend | Jinja2 templates, vanilla HTML/CSS/JS |

---

## 🛠️ Getting Started

### Prerequisites
- Python 3.10+ (the `date | None` type hints require 3.10+)
- pip

### Installation

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the development server
python app.py
```

The app starts on **`http://localhost:5001`** by default.

### Demo account

A demo user is seeded automatically on startup:

| Field | Value |
|-------|-------|
| Email | `demo@spendly.com` |
| Password | `demo123` |

You can log in with these credentials to explore the app immediately — no registration required.

---

## 🌐 Deployment

Spendly is configured to deploy on **Railway**. It binds to `0.0.0.0` and reads the port from the `PORT` environment variable:

```bash
railway deploy
```

For local development, set `FLASK_DEBUG=true` to enable the Werkzeug debugger:

```bash
FLASK_DEBUG=true python app.py
```

> ⚠️ **Production note:** Set a strong `SECRET_KEY` via the environment before deploying — the app falls back to a hardcoded dev secret only when none is provided.

---

## 📝 API / Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Landing page (redirects to profile if logged in) |
| GET | `/register` | Registration form |
| GET | `/login` | Login form |
| GET | `/logout` | Clears session and redirects home |
| GET | `/dashboard` | Dashboard overview |
| GET | `/profile` | Main expense dashboard with stats, transactions & category breakdown |
| GET | `/analytics` | Spending analytics |
| GET/POST | `/expenses/add` | Add a new expense |
| GET/POST | `/expenses/<id>/edit` | Edit an existing expense |
| POST | `/expenses/<id>/delete` | Delete an expense |
| GET | `/terms` | Terms of service |
| GET | `/privacy` | Privacy policy |

All expense routes are **scoped to the logged-in user** — you can only see and modify your own data.

---

## 🧪 Testing

```bash
pytest
```

The test suite covers registration, login, and user seeding behavior using `pytest-flask`.

---

## 📋 Valid Categories

Expenses must fall into one of these seven categories:

`Food` · `Transport` · `Bills` · `Health` · `Entertainment` · `Shopping` · `Other`

---

## 📄 License

MIT

---

## 🔗 Live Demo

This project is configured for deployment on **Railway**. Once deployed, you can access the live app at:

```
https://expense-tracker-production-fae6.up.railway.app/
```

Or check the Railway dashboard for the exact URL after deployment.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, fork the repository, and create pull requests. For major changes, please open an issue first to discuss what you'd like to change.

---

## 📧 Contact

Built by **yashh-alpha** — [GitHub](https://github.com/yashh-alpha/spendly)