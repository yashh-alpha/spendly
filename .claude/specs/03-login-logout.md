# Spec: Login and Logout

## Overview

The `/login` and `/logout` routes are currently stubs: `/login` renders a static
form but does not process it, and `/logout` clears the session without any
guardrails. This step wires up real authentication: the POST handler validates
the submitted email and password, looks the user up in the SQLite `users`
table, verifies the password hash with werkzeug, and on success starts a
session and redirects to the dashboard. The logout route destroys the session
and sends the user back to the landing page. Together with Step 2
(Registration), this completes the auth loop — the app can now let a real
user sign in, stay signed in, and sign out cleanly.

## Depends on

- Step 1 — Database setup (`database/db.py` with `get_db` and the `users`
  table schema).
- Step 2 — Registration (`/register` POST handler, session management, and the
  `dashboard` route that login redirects to).

## Routes

- `GET /login` — render the sign-in form (public)
- `POST /login` — validate credentials, verify password hash, start session,
  redirect to dashboard (public)
- `GET /logout` — destroy session, redirect to landing (logged-in)

## Database changes

No database changes. The `users` table from Step 1 already has the columns
needed (`id`, `name`, `email`, `password_hash`, `created_at`).

## Templates

- Modify: `templates/login.html`
  - Keep the existing form fields, `required` attributes, and error block
  - Ensure the form posts to `/login` via `url_for('login')`
- Modify: `templates/dashboard.html`
  - Keep the existing welcome markup and the "Logout" link
  - The logout link already points at `url_for('logout')` — no change needed
- Modify: `templates/base.html`
  - Optionally hide the "Sign in" / "Get started" nav links when a session is
    active, replacing them with a user greeting and a logout link

## Files to change

- `app.py` — implement the POST handler for `/login` and harden `/logout`
- `templates/login.html` — ensure the form posts to the login route
- `templates/base.html` — conditional nav rendering for logged-in users

## Files to create

None.

## New dependencies

No new dependencies. Use the already-installed `flask` and `werkzeug`.

## Rules for implementation

- No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()` only
- Parameterised queries only — never use string formatting in SQL
- Hash passwords with `werkzeug.security.generate_password_hash`
- Verify passwords with `werkzeug.security.check_password_hash`
- Use CSS variables for all colours — never hardcode hexadecimal values
- All templates must extend `base.html`
- Use Flask sessions (`session` object) for login state
- Never log or echo the plaintext password
- Redirect on success; re-render the form with the error on failure
- Logout must only be reachable when a session is active (redirect to login
  otherwise)
- Use a generic "Incorrect email or password" error — never reveal whether
  the email or the password was wrong, to avoid user enumeration

## Definition of done

- [ ] `GET /login` renders the sign-in form without errors
- [ ] Submitting valid credentials for the demo user logs the user in and
      redirects to the dashboard
- [ ] Submitting an incorrect password is rejected with a generic error
- [ ] Submitting an unregistered email is rejected with the same generic
      error
- [ ] Submitting an invalid email format is rejected
- [ ] Submitting an empty password is rejected
- [ ] After login, `session["user_id"]` and `session["name"]` are set
- [ ] `GET /logout` clears the session and redirects to the landing page
- [ ] Visiting `/logout` without an active session redirects to `/login`
- [ ] `GET /` redirects to `/login` when no session is active and to the
      dashboard when one is
- [ ] App starts without errors
- [ ] All queries use parameterised SQL