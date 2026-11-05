---
description: Create a spec file and feature branch for the next Spendly step
argument-hint: "Step number and feature name e.g. 2 registration"
allowed-tools: Read, Write, Glob, Bash(git:*)
---

You are a senior developer spinning up a new feature for the Spendly expense tracker. Always follow the rules in `CLAUDE.md`.

User input: $ARGUMENTS

## Step 1 — Check working directory is clean

Run `git status` and check for uncommitted, unstaged, or untracked files.

If any exist, stop immediately and tell the user to commit or stash changes before proceeding.

**DO NOT CONTINUE until the working directory is clean.**

## Step 2 — Parse the arguments

From `$ARGUMENTS`, extract:

1. `step_number` — zero-padded to 2 digits.
   - Example: `2` → `02`, `11` → `11`

2. `feature_title` — human-readable title in Title Case.
   - Example: `Registration` or `Login and Logout`

3. `feature_slug` — Git- and file-safe slug.
   - Lowercase, kebab-case
   - Only `a-z`, `0-9`, and `-`
   - Maximum 40 characters
   - Example: `registration`, `login-logout`

4. `branch_name` — format: `feature/<feature_slug>`
   - Example: `feature/registration`

If you cannot infer these from `$ARGUMENTS`, ask the user to clarify before proceeding.

## Step 3 — Check branch name is not taken

Run `git branch` to list existing branches.

If `branch_name` is already taken, append a number:

- `feature/registration-01`
- `feature/registration-02`
- And so on.

Use the first available branch name.

## Step 4 — Switch to main and pull latest

Run:

```bash
git checkout main
git pull origin main
```

If either command fails, stop and report the error. Do not continue with an incorrectly prepared branch.

## Step 5 — Create and switch to the feature branch

Run:

```bash
git checkout -b <branch_name>
```

Replace `<branch_name>` with the branch name determined in Step 3.

If the command fails, stop and report the error.

## Step 6 — Research the codebase

Read these files before writing the spec:

- `CLAUDE.md` — roadmap, conventions, and schema.
- `app.py` — existing routes and application structure.
- `database/db.py` — existing database schema and functions.
- All files in `.claude/specs/` — avoid duplicating existing specifications.

Check `CLAUDE.md` to confirm the requested step is not already marked complete.

If it is already marked complete, warn the user and stop.

## Step 7 — Write the spec

Generate a specification document with this exact structure:

# Spec: <feature_title>

## Overview

One paragraph describing what this feature does, why it is needed, and why it exists at this stage of the Spendly roadmap.

## Depends on

List the previous steps that must be completed before this feature can be implemented.

## Routes

List every new route required.

Use this format:

- `METHOD /path` — description — access level (`public` or `logged-in`)

If no new routes are needed, state:

`No new routes`.

## Database changes

Describe any new tables, columns, or constraints needed.

Always verify the existing schema against `database/db.py` before writing this section.

If no database changes are needed, state:

`No database changes`.

## Templates

- **Create:** List new templates and their paths.
- **Modify:** List existing templates and describe the required changes.

## Files to change

List every existing file that will be modified.

## Files to create

List every new file that will be created.

## New dependencies

List any new Python packages required.

If there are no new dependencies, state:

`No new dependencies`.

## Rules for implementation

List the specific constraints Claude must follow during implementation.

Always include:

- No SQLAlchemy or ORMs.
- Parameterised queries only.
- Passwords must be hashed with Werkzeug.
- Use CSS variables; never hardcode hexadecimal color values.
- All templates must extend `base.html`.

Include any additional feature-specific constraints where appropriate.

## Definition of done

Provide a specific, testable checklist.

Each item must describe something that can be verified by running the application or executing an appropriate test.

Avoid vague statements such as "feature works correctly".

---

## Step 8 — Save the spec

Save the specification to:

`.claude/specs/<step_number>-<feature_slug>.md`

Use the parsed, zero-padded step number and feature slug in the filename.

For example:

`.claude/specs/02-registration.md`

Ensure the specification follows the exact structure defined in Step 7.

## Step 9 — Report to the user

Print a short summary in this exact format:

```text
Branch:     <branch_name>
Spec file:  .claude/specs/<step_number>-<feature_slug>.md
Title:      <feature_title>
```

Then tell the user:

"Review the spec at `.claude/specs/<step_number>-<feature_slug>.md` then enter Plan Mode with Shift+Tab twice to begin implementation."

Do not print the full specification in chat unless explicitly asked.