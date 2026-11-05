# Spec: Registration

## Overview

The `/register` route currently only renders a static HTML template — it does
not accept form data or persist anything. This step wires up real user
registration: the POST handler validates the submitted name, email, and
password, rejects duplicate emails, hashes the password with werkzeug, and
inserts the user into the SQLite `users` table. On success the user is logged
in and redirected to the dashboard; on failure the form re-renders with an
error message. This is the first step that turns the app from a static landing
page into a working product.

## Depends on

- Step 1 — Database setup (`database/db.py` with `get_db`, `init_db`, and the
  `users` table schema).

## Routes

- `GET /register` — render the registration form (public)
- `POST /register` — validate input, create user, log in, redirect to dashboard (public)
- `GET /` — landing page; redirects to `/login` if a session is already
  active (public / logged-in)

## Database changes

No database changes. The `users` table from Step 1 already has the columns
needed (`id`, `name`, `email`, `password_hash`, `created_at`).

## Templates

- Modify: `templates/register.html`
  - Add an inline error display block (already present via `{% if error %}`)
  - Keep the existing form fields and `required` attributes
- Create: `templates/dashboard.html`
  - A minimal welcome screen shown after successful registration/login
  - Extends `base.html`

## Files to change

- `app.py` — add POST handler for `/register`, session management, and a
  dashboard route
- `templates/register.html` — minor markup to surface server-side errors

## Files to create

- `templates/dashboard.html` — post-registration welcome template

## New dependencies

No new dependencies. Use the already-installed `flask` and `werkzeug`.

## Rules for implementation

- No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()` only
- Parameterised queries only — never use string formatting in SQL
- Hash passwords with `werkzeug.security.generate_password_hash`
- Verify passwords with `werkzeug.security.check_password_hash`
- Use CSS variables for all colours — never hardcode hex values
- All templates must extend `base.html`
- Use Flask sessions (`session` object) for login state
- Minimum password length: 8 characters
- Reject duplicate emails with a clear, non-technical error message
- Never log or echo the plaintext password
- Redirect on success; re-render the form with the error on failure

## Definition of done

- [ ] `GET /register` renders the registration form without errors
- [ ] Submitting valid data creates a user with a hashed password
- [ ] Submitting a duplicate email is rejected and shows an error
- [ ] Submitting a password shorter than 8 characters is rejected
- [ ] Submitting an invalid email format is rejected
- [ ] After successful registration the user is redirected to the dashboard
- [ ] The user is logged in (session is set)
- [ ] `GET /` redirects to `/login` when no session is active
- [ ] App starts without errors
- [ ] All queries use parameterised SQL