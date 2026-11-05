
# description:

create a single dummy user in the database.

# allowed tools:

 Read, Bash(python:*)

## Instructions

1. Inspect the project structure before making any changes.
2. Identify:

   * The database technology/ORM being used.
   * The User model/schema.
   * How the application initializes the database.
   * Existing database seed scripts or CLI commands.
   * Required User fields and validation rules.
3. Reuse the application's existing database configuration and User model. Do **not** create a parallel database setup.
4. Create a seed user with sensible development-only values:

   * Name: Any Indian name
   * Email: any random email
   * Password: `password123`
5. Store the password using the same hashing mechanism used by the application. Never store a plaintext password if the application normally hashes passwords.
6. Make the operation **idempotent**:

   * If the email already exists, try another email.
   * Report that the user already exists.
   * Do not overwrite the existing user's password or other data unless explicitly requested.
7. If the project already has a seeding mechanism, integrate with it rather than creating a duplicate mechanism.
8. Keep the implementation limited to what is necessary for seeding the user.
9. Run the appropriate checks/tests after making the changes.
10. Clearly report:

    * What files were changed.
    * How the user can run the seed command.
    * Whether the user was created or already existed.
    * Any tests/checks that were run.

## Safety

* This command is intended for local development/testing.
* Never seed test credentials into a production database.
* Do not expose real user credentials or secrets.
* Do not delete or modify existing users.
* Do not modify production configuration.
* Before executing destructive database operations, stop and ask for confirmation.

## Expected Behavior

When `/seed-user` is invoked, inspect the existing project and implement the seed operation according to the project's architecture rather than assuming a particular framework, ORM, or database.
