# Functional Requirements

## 1. Paste Management

- Users can create text pastes with syntax highlighting.
    
- Users select the content type or programming language manually.
    
- Maximum content size: **1 MB per paste**.
    
- Authenticated users have full CRUD access to their own pastes.
    
- Only the paste owner can update, delete, or manage a paste.
    
- Authenticated users can access their paste history.
    

## 2. User Types and Paste Creation

### Anonymous Users

- Anonymous users can create public pastes without an account.
    
- Each anonymous paste receives a unique identifier, preferably a UUID.
    
- Each IP address can create a maximum of **10 anonymous pastes**.
    
- Anonymous pastes expire after **10 minutes** and are permanently deleted by a background scheduled job.
    
- Anonymous users can only create and share pastes. They cannot update, delete, or manage them.
    

### Authenticated Users

- Authenticated users can create an unlimited number of pastes.
    
- The **1 MB content limit** still applies.
    
- Authenticated users can create public, private, and password-protected pastes.
    

## 3. Authentication and Authorization

- Authentication is based on JWT access and refresh tokens.
    
- Refresh tokens support rotation and blacklisting.
    
- Authorization enforces ownership and permission rules.
    

## 4. Paste Access Levels

### Public

- Anyone with the paste link can view the paste.
    
- No account is required.
    

### Private

- Only the authenticated owner can access the paste.
    

### Password-Protected

- Only authenticated users can create password-protected pastes.
    
- Anyone with the paste link and the correct password can view the content.
    
- An account is not required to view a password-protected paste.
    
- Only the owner can set, change, or remove the password.
    

## 5. Expiration and Data Retention

### Anonymous Pastes

- Anonymous pastes expire after **10 minutes**.
    
- Expired anonymous pastes are permanently deleted by a background scheduled job.
    

### Authenticated Pastes

- Owners can set an expiration between **1 minute and 24 hours**.
    
- Once expired, a paste becomes inaccessible to viewers.
    
- The owner can still update an expired paste's expiry during its **24-hour retention period**, calculated from its `expires_at` timestamp.
    
- Updating an expired paste does not extend its retention period or change its `expires_at` timestamp.
    
- An expired paste becomes eligible for permanent deletion once **24 hours have elapsed since its** `**expires_at**` **timestamp**.
    
- A background scheduled job performs the deletion. The actual deletion may occur after the eligibility threshold.
    

**Deletion condition:** An authenticated paste is eligible for permanent deletion when `expires_at` is set and `expires_at + 24 hours <= current_timestamp`.

# Non-Functional Requirements

## 1. Security

- Passwords must be stored using secure password hashing. Tokens, passwords, and paste contents must not be exposed in application logs.
    
- Authentication and authorization must prevent unauthorized access to protected resources.
    
- User input must be validated, and common web vulnerabilities must be mitigated.
    
- Sensitive configuration and secrets must be kept out of source control.
    

## 2. Reliability

- Successful operations must not leave data in a partially saved or inconsistent state.
    
- Expiration and deletion jobs must tolerate retries and temporary failures.
    
- Expired pastes must become inaccessible immediately after expiration, regardless of when physical deletion occurs.
    

## 3. Availability and Recovery

- The application should remain stable during normal operation and recover gracefully from unexpected errors.
    
- Background-job failures must be detectable and recoverable.
    

## 4. Maintainability

- Code must have clear separation of responsibilities and explicit business rules.
    
- Configuration must be separated from application code.
    
- Changes to one component should not require unnecessary changes to unrelated components.
    

## 5. Testing

- Core business rules must have automated test coverage.
    
- Unit and integration tests must cover authentication, authorization, access levels, rate limits, expiration, and deletion behavior.
    
- Security-sensitive scenarios and error cases must be tested.
    
- Tests must be repeatable and isolated from external services wherever practical.
    

## 6. Observability

- Application errors and background-job failures must be logged.
    
- Logs must support debugging without exposing sensitive data or paste contents.
    
- Failures in scheduled jobs must be identifiable and diagnosable.