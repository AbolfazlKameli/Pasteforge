# PasteForge API Design

**API Version:** v1  
**Base URL:** `/api/v1`  
**Content-Type:** `application/json`

## 1. Overview

PasteForge provides a RESTful API for creating, retrieving, managing, and sharing text pastes.

The API supports both anonymous and authenticated users, with different access permissions and resource management capabilities.

The API is organized into the following main resources:

- **Authentication:** Registration, login, logout, and token management.
    
- **Users:** Profile management and password operations.
    
- **Pastes:** Paste creation, retrieval, updating, deletion, and expiration management.
    
- **Health:** Application liveness and readiness checks.
    

## 2. General API Conventions

### HTTP Methods

|Method|Purpose|
|---|---|
|GET|Retrieve resources|
|POST|Create resources or perform operations|
|PUT|Replace or update a resource|
|PATCH|Partially update a resource|
|DELETE|Delete a resource|

### Response Structure

Successful responses generally follow a consistent response envelope:

```
{
  "data": {
    "message": "Operation completed successfully."
  }
}
```

Error responses follow this structure:

```
{
  "data": {
    "error": "An error occurred."
  }
}
```

Validation errors use FastAPI's standard validation response structure.

### HTTP Status Codes

|Status|Description|
|---|---|
|200|Successful operation|
|201|Resource successfully created|
|202|Request accepted for processing|
|204|Resource successfully deleted|
|400|Invalid request or business rule violation|
|401|Authentication required or failed|
|403|Permission denied|
|404|Resource not found|
|422|Request validation failed|
|429|Rate limit exceeded|
|503|Service unavailable|

## 3. Authentication

Authentication is based on JWT access and refresh tokens.

Tokens are managed through HTTP cookies.

|Endpoint|Method|Description|Authentication|
|---|---|---|---|
|`/auth/register`|POST|Request registration OTP|Public|
|`/auth/register/verify`|POST|Verify OTP and complete registration|Public|
|`/auth/login`|POST|Authenticate user|Public|
|`/auth/logout`|POST|Terminate current session|Required|
|`/auth/refresh`|POST|Refresh authentication tokens|Refresh token|

### Registration Flow

1. The client submits an email address.
    
2. The server generates and sends an OTP.
    
3. The client submits the OTP and registration credentials.
    
4. The server verifies the OTP and creates the user account.
    

### Login Flow

1. The client submits email and password.
    
2. The server validates credentials.
    
3. The server issues access and refresh tokens through HTTP cookies.
    

### Token Refresh

Refresh tokens support rotation and blacklisting to prevent reuse of invalidated sessions.

## 4. User Management

All profile management endpoints require authentication.

|Endpoint|Method|Description|
|---|---|---|
|`/users/profile`|GET|Retrieve authenticated user's profile|
|`/users/profile`|PUT|Update user profile|
|`/users/profile`|DELETE|Delete user account|
|`/users/profile/email/verify`|POST|Verify and update email|
|`/users/password/reset`|POST|Request password reset OTP|
|`/users/password/set`|POST|Set a new password using OTP|
|`/users/password/change`|POST|Change authenticated user's password|

Users can only manage their own profiles and credentials.

## 5. Paste Management

Paste endpoints are the core of the application.

### 5.1 Create Paste

`POST /pastes/`

Creates a new paste.

**Authentication:** Optional

**Headers:**

```
Idempotency-Key: <UUID>
```

**Request Body:**

```
{
  "content": "print('Hello, PasteForge!')",
  "syntax": "python",
  "access_type": "public",
  "expires_at": null,
  "password": null
}
```

Supported access types:

- `public`
    
- `private`
    
- `password_protected`
    

**Response:** `201 Created`

Returns the created paste, including its identifier, content metadata, timestamps, and owner information.

### 5.2 Retrieve Paste

`GET /pastes/{paste_id}`

Retrieves a paste by its UUID.

**Authentication:** Optional

Access is determined by the paste's access type:

- Public pastes are accessible without authentication.
    
- Private pastes are accessible only to their owners.
    
- Password-protected pastes require password verification through the dedicated endpoint.
    

**Response:** `200 OK`

### 5.3 Retrieve Password-Protected Paste

`POST /pastes/{paste_id}/secret`

Retrieves a password-protected paste.

**Authentication:** Not required.

**Request Body:**

```
{
  "password": "paste-password"
}
```

**Response:** `200 OK`

An invalid password or inaccessible paste must not expose its content.

### 5.4 List Authenticated Pastes

`GET /pastes/`

Retrieves the authenticated user's pastes.

**Authentication:** Required

**Query Parameters:**

|Parameter|Type|Description|
|---|---|---|
|`page`|integer|Page number|
|`per_page`|integer|Number of items per page|
|`access_type`|string|Filter by access type|
|`syntax`|string|Filter by syntax|
|`expired`|boolean|Filter expired pastes|
|`created_after`|datetime|Creation date lower bound|
|`created_before`|datetime|Creation date upper bound|
|`search`|string|Search term|

Default pagination:

- `page = 1`
    
- `per_page = 10`
    
- Maximum `per_page = 100`
    

**Response:** `200 OK`

```
{
  "data": {
    "count": 25,
    "previous_page": null,
    "next_page": 2,
    "last_page": 3,
    "items": []
  }
}
```

### 5.5 Update Paste

`PATCH /pastes/{paste_id}`

Updates an existing paste.

**Authentication:** Required

Only the paste owner can update it.

**Request Body:**

```
{
  "content": "Updated content",
  "syntax": "python",
  "access_type": "private",
  "expires_at": null,
  "password": null,
  "new_password": null
}
```

All fields are optional, allowing partial updates.

**Response:** `200 OK`

### 5.6 Delete Paste

`DELETE /pastes/{paste_id}`

Deletes an existing paste.

**Authentication:** Required

Only the paste owner can delete it.

**Request Body:**

```
{
  "password": null
}
```

The password field is optional and can be used when required by the paste's access policy.

**Response:** `204 No Content`

### 5.7 Update Paste Expiration

`POST /pastes/{paste_id}/expiration`

Updates the expiration timestamp of a paste.

**Authentication:** Required

**Request Body:**

```
{
  "expires_at": "2026-11-24T12:00:00Z",
  "password": null
}
```

Only the paste owner can modify expiration settings.

**Response:** `200 OK`

## 6. Health Checks

Health endpoints are used by infrastructure components to monitor application availability.

|Endpoint|Method|Description|
|---|---|---|
|`/health/live`|GET|Check whether the application process is alive|
|`/health/ready`|GET|Check whether the application and its dependencies are ready|

### Liveness

`GET /health/live`

Returns `200 OK` when the application process is alive.

### Readiness

`GET /health/ready`

Checks the health of:

- PostgreSQL
    
- Redis
    
- Celery workers
    
- Database migrations
    

Returns `200 OK` when the required health checks pass, otherwise `503 Service Unavailable`.

## 7. Access Control

Paste access is governed by ownership and access type.

|Operation|Anonymous User|Authenticated Owner|Other Authenticated User|
|---|---|---|---|
|Create public paste|Yes|Yes|Yes|
|View public paste|Yes|Yes|Yes|
|View private paste|No|Yes|No|
|View protected paste|With password|With password|With password|
|Update paste|No|Yes|No|
|Delete paste|No|Yes|No|
|Change expiration|No|Yes|No|

Anonymous users can create and share pastes but cannot manage them.

## 8. Rate Limiting and Resource Restrictions

The API enforces the following restrictions:

|Rule|Limit|
|---|---|
|Maximum paste content size|1 MB|
|Anonymous paste creation|10 pastes per IP|
|Anonymous creation rate|10 requests per minute|
|Authenticated creation rate|10 requests per minute|
|Anonymous paste lifetime|10 minutes|
|Authenticated paste expiration|1 minute to 24 hours|

Rate limits are enforced at the application/infrastructure level.

Password-protected paste access must also enforce rate limits on failed password attempts.

## 9. Idempotency

Paste creation requires an `Idempotency-Key` UUID header.

The server uses the key and request scope to identify duplicate requests.

- Repeated requests with the same key and request payload must not create duplicate pastes.
    
- Reusing the same key with a different request payload must be rejected.
    
- Completed responses are stored temporarily and can be returned for repeated requests.
    

This mechanism helps prevent duplicate resource creation when clients retry requests.

## 10. Expiration and Data Lifecycle

Paste expiration and physical deletion are handled separately.

**Anonymous pastes:**

- Expire after 10 minutes.
    
- Become inaccessible after expiration.
    
- Are permanently deleted through scheduled background jobs.
    

**Authenticated pastes:**

- Become inaccessible after their expiration timestamp.
    
- Can still be updated by their owner during the 24-hour retention period after expiration.
    
- Every successful update resets `updated_at`.
    
- Become eligible for permanent deletion when expired and not updated for at least 24 hours.
    

Celery scheduled tasks handle background deletion operations.

## 11. Security Considerations

- Passwords and OTP codes must never be stored in plaintext.
    
- JWT tokens are managed through HTTP cookies.
    
- Cookie-based authentication must be protected against CSRF attacks.
    
- Ownership checks must be enforced for protected operations.
    
- Sensitive information must not appear in application logs.
    
- Password verification attempts must be rate-limited.
    
- Request validation must enforce resource constraints.
    
- Expired pastes must never be accessible, even before physical deletion.
    

---

**Document Status:** Based on PasteForge API v1 implementation and current project requirements.