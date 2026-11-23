# Core Tables
The database consists of two core entities: `Users` and `Pastes`. The schema follows **Third Normal Form (3NF)**, with BCNF compatibility under the current functional dependencies and business rules.

## 1. Users
Stores user account information and authentication credentials.

| Field        | Type / Constraint     | Description                             |
| ------------ | --------------------- | --------------------------------------- |
| `id`         | UUID, PK              | Unique user identifier                  |
| `email`      | UNIQUE, NOT NULL      | User's email address                    |
| `password`   | NOT NULL              | Hashed authentication password          |
| `is_active`  | BOOLEAN, NOT NULL     | Indicates whether the account is active |
| `created_at` | TIMESTAMPTZ, NOT NULL | Account creation timestamp              |
| `updated_at` | TIMESTAMPTZ, NOT NULL | Last modification timestamp             |

## 2. Pastes
Stores paste content, ownership information, access policies, and expiration timestamps.

| Field         | Type / Constraint     | Description                                                |
| ------------- | --------------------- | ---------------------------------------------------------- |
| `id`          | UUID, PK, NOT NULL    | Unique paste identifier                                    |
| `content`     | TEXT, NOT NULL        | Paste content                                              |
| `syntax`      | VARCHAR(50), NULL     | Syntax highlighting language                               |
| `size_bytes`  | BIGINT, NOT NULL      | Size of the paste content in bytes                         |
| `access_type` | ENUM, NOT NULL        | Access level: `public`, `private`, or `password_protected` |
| `password`    | VARCHAR, NULL         | Password associated with a password-protected paste        |
| `expires_at`  | TIMESTAMPTZ, NOT NULL | Scheduled expiration timestamp                             |
| `created_at`  | TIMESTAMPTZ, NOT NULL | Paste creation timestamp                                   |
| `updated_at`  | TIMESTAMPTZ, NOT NULL | Last modification timestamp                                |
| `owner_id`    | UUID, FK, NULL        | References `Users.id`; NULL for anonymous pastes           |
### Constraints and Design Notes
- **Primary Key:** `id` is the primary key and uses UUID.
- **Ownership:** `owner_id` references `Users.id` and is nullable to support anonymous paste creation.
- **Foreign Key Behavior:** Updates and deletions on the referenced user are cascaded to associated paste records through `ON UPDATE CASCADE` and `ON DELETE CASCADE`.
- **Access Types:** `access_type` is restricted to `public`, `private`, and `password_protected` through a PostgreSQL ENUM type.
- **Expiration:** `expires_at` is a non-nullable timestamp with timezone support.
- **Password:** `password` is nullable and uses a variable-length string column.
- **Indexes:**
    - `ix_pastes_expires_at`: Non-unique index on `expires_at`.
    - `ix_pastes_expires_at_anonymous`: Non-unique partial index on `expires_at` for records where `owner_id IS NULL`.
    - `ix_pastes_expires_at_authenticated`: Non-unique partial index on `expires_at` for records where `owner_id IS NOT NULL`.
    - `ix_pastes_access_type`: Non-unique index on `access_type`.
    - `ix_pastes_created_at`: Non-unique index on `created_at`.
    - `ix_pastes_syntax`: Non-unique index on `syntax`.
    - `ix_pastes_updated_at`: Non-unique index on `updated_at`.

# Authentication & Session Management Tables

## 1. OTP
Stores hashed one-time passwords associated with email addresses, including verification attempts and expiration timestamps.

| Field         | Type / Constraint              | Description                                  |
| ------------- | ------------------------------ | -------------------------------------------- |
| `id`          | INTEGER, PK, NOT NULL          | Unique OTP record identifier                 |
| `email`       | VARCHAR(255), UNIQUE, NOT NULL | Email address associated with the OTP record |
| `hashed_code` | VARCHAR(128), NOT NULL         | Hashed one-time password                     |
| `attempts`    | INTEGER, NOT NULL              | Number of verification attempts              |
| `expires_at`  | TIMESTAMPTZ, NOT NULL          | OTP expiration timestamp                     |
### Constraints and Design Notes
- **Primary Key:** `id` uniquely identifies each OTP record.
- **Email Uniqueness:** Each email address can have only one OTP record at a time.
- **Password Security:** OTP codes are stored as hashes rather than plaintext.
- **Expiration:** `expires_at` determines when an OTP becomes invalid.
- **Verification Attempts:** `attempts` tracks the number of verification attempts.
## 2. OTP Blacklist
Stores email addresses temporarily blocked from OTP operations, along with an optional expiration timestamp.

| Field        | Type / Constraint     | Description                                            |
| ------------ | --------------------- | ------------------------------------------------------ |
| `id`         | INTEGER, PK, NOT NULL | Unique blacklist record identifier                     |
| `email`      | VARCHAR(50), NOT NULL | Email address associated with the blacklist record     |
| `expires_at` | TIMESTAMPTZ, NULL     | Optional expiration timestamp for the blacklist record |
### Constraints and Design Notes
- **Primary Key:** `id` uniquely identifies each blacklist record.
- **Email Index:** A non-unique index is created on `email` to improve lookup performance.
- **Expiration:** `expires_at` represents the optional expiration timestamp of a blacklist record.
- **Email Uniqueness:** No unique constraint is defined on `email`, so multiple records can reference the same email address.
## 3. Token Obtain Pair
Stores token pair session records associated with users, including session identifiers and token pair status.

| Field      | Type / Constraint      | Description                                       |
| ---------- | ---------------------- | ------------------------------------------------- |
| `id`       | INTEGER, PK, NOT NULL  | Unique token pair record identifier               |
| `sid`      | UUID, UNIQUE, NOT NULL | Unique session identifier                         |
| `status`   | ENUM, NOT NULL         | Token pair status: `active` or `blacklisted`      |
| `owner_id` | UUID, FK, NOT NULL     | References `Users.id`; identifies the token owner |
### Constraints and Design Notes
- **Primary Key:** `id` uniquely identifies each token pair record.
- **Session Uniqueness:** `sid` has a unique constraint to ensure each session identifier is unique.
- **Token Status:** `status` is restricted to the `active` and `blacklisted` enum values.
- **Ownership:** `owner_id` references `Users.id` and cannot be NULL.
- **Referential Integrity:** Deleting a user automatically deletes their associated token pair records through `ON DELETE CASCADE`.
- **Owner Index:** A non-unique index is created on `owner_id` to improve queries filtering token pair records by user.
# Anonymous Usage Tracking
## 1. Anonymous Usage
Tracks anonymous usage by storing a hashed IP address and its associated usage counter.

| Field     | Type / Constraint             | Description                                         |
| --------- | ----------------------------- | --------------------------------------------------- |
| id        | INTEGER, PK, NOT NULL         | Unique anonymous usage record identifier            |
| hashed_ip | VARCHAR(64), UNIQUE, NOT NULL | Hashed IP address used to identify anonymous users  |
| counter   | SMALLINT, NOT NULL            | Usage counter associated with the hashed IP address |
### Constraints and Design Notes
- `id` is the primary key.
- `hashed_ip` has a unique constraint, so each hashed IP address can have only one record.
- `counter` stores the usage count and is defined as `SMALLINT`.
- IP addresses are stored in hashed form rather than as plain text.
- The migration does not define a default value or check constraint for `counter`.
- The migration does not define `created_at` or `updated_at` columns.
# Idempotency
## 1. Idempotency Records
Stores idempotency records, including request identifiers, request hashes, processing status, and response data.

| Field           | Type / Constraint      | Description                                |
| --------------- | ---------------------- | ------------------------------------------ |
| id              | UUID, PK, NOT NULL     | Unique idempotency record identifier       |
| scope_key       | VARCHAR(128), NOT NULL | Scope associated with the idempotency key  |
| key             | UUID, NOT NULL         | Idempotency key                            |
| request_hash    | VARCHAR(64), NOT NULL  | Hash of the request                        |
| status          | ENUM, NOT NULL         | Record status: `processing` or `completed` |
| response_status | INTEGER, NULL          | HTTP response status code                  |
| response_body   | JSONB, NULL            | Response body stored as JSONB              |
| created_at      | TIMESTAMPTZ, NOT NULL  | Record creation timestamp                  |
| expires_at      | TIMESTAMPTZ, NOT NULL  | Record expiration timestamp                |
### Constraints and Design Notes
- `id` is the primary key and uses UUID as its type.
- The combination of `scope_key` and `key` must be unique.
- `status` is restricted to `processing` and `completed`.
- The `ck_idempotency_response_state` check constraint enforces the following conditions:
    - When `status` is `processing`, both `response_status` and `response_body` must be `NULL`.
    - When `status` is `completed`, both `response_status` and `response_body` must be `NOT NULL`.
- A non-unique index is created on `expires_at` for expiration-based queries.
- `response_body` uses PostgreSQL `JSONB`.
- Both `created_at` and `expires_at` are non-nullable timestamp fields with timezone support.
