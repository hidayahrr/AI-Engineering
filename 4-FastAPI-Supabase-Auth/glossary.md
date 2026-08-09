# Glossary FastAPI-Supabase-Auth

## Identity Provider (IdP)

An external service (like Supabase, Auth0, or Firebase) that manages user accounts, passwords, and security tokens so your server doesn't have to.

## JSON Web Token (JWT)

A compact, URL-safe secure string used to transfer claims (like "this is User ID 123") between two parties. It is cryptographically signed so it cannot be tampered with.

## Bearer Token

A security token given to the client. The server grants access to anyone who "bears" (presents) this token, usually in the format:

```text
Authorization: Bearer <token>
```

## Authorization Header

A standard HTTP header used by clients to send credentials/tokens to a server (e.g. `Authorization: Bearer eyJhbGciOi...`).

## Authentication (AuthN)

The process of verifying who a user is (e.g., matching email & password).

## Authorization (AuthZ)

The process of verifying what a user is allowed to do (e.g., checking if an authenticated user has permission to view a page).

## Middleware

A function in web frameworks that intercepts incoming requests before they reach your main route handler. Excellent for checking if a user is logged in.

## Environment Variables

Configuration settings stored outside of your source code (typically in a `.env` file) used to keep private API credentials and database keys safe.

## Refresh Token

A special long-lived token used to obtain a new Access Token (JWT) once the current one expires, without forcing the user to log in again.