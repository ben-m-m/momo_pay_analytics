# Authentication Documentation

## Overview

The MoMo SMS REST API uses HTTP Basic Authentication to secure all endpoints. Every request must include valid credentials or the server returns a 401 Unauthorized response.

## How It Works

Basic Auth works by sending a username and password with every HTTP request. The credentials are combined into a single string formatted as `username:password`, then encoded using Base64. This encoded string is sent in the `Authorization` header.

**Important:** Base64 is encoding, not encryption. It can be decoded by anyone who intercepts it. In production, Basic Auth should always be used over HTTPS to protect credentials in transit.

## Credentials

The API ships with two preconfigured user accounts:

| Username | Password    | Role         |
|----------|-------------|--------------|
| admin    | password123 | Administrator|
| user1    | momo2024    | Standard User|

Both accounts have the same level of access to all endpoints. There is no role based permission system in the current version.

## Making Authenticated Requests

### Header Format

```
Authorization: Basic <base64_encoded_credentials>
```

### Encoding Steps

1. Combine username and password with a colon: `admin:password123`
2. Base64 encode the combined string: `YWRtaW46cGFzc3dvcmQxMjM=`
3. Prefix with `Basic ` and place in the Authorization header

### Example with curl

```bash
# Using the -u flag (curl handles encoding automatically)
curl -u admin:password123 http://localhost:8000/transactions

# Using the header directly
curl -H "Authorization: Basic YWRtaW46cGFzc3dvcmQxMjM=" http://localhost:8000/transactions
```

### Example with Python requests

```python
import requests

response = requests.get(
    "http://localhost:8000/transactions",
    auth=("admin", "password123")
)
print(response.json())
```

## Error Responses

### Missing Credentials

If no Authorization header is provided:

```json
{
  "error": "Authentication required. Provide Basic Auth credentials."
}
```

**Status Code:** 401
**Headers:** Includes `WWW-Authenticate: Basic realm="MoMo API"` to prompt the client for credentials.

### Malformed Header

If the Authorization header is present but cannot be decoded:

```json
{
  "error": "Malformed Authorization header."
}
```

**Status Code:** 401

### Invalid Credentials

If the username or password is incorrect:

```json
{
  "error": "Invalid username or password."
}
```

**Status Code:** 401

The error message intentionally does not reveal whether the username or the password was wrong. This is a security practice that prevents attackers from confirming valid usernames through trial and error.

## Implementation Details

The authentication logic lives in the `authenticate()` method of the `MoMoAPIHandler` class. Every HTTP method handler (`do_GET`, `do_POST`, `do_PUT`, `do_DELETE`) calls `self.authenticate()` as its first step. If authentication fails, the method sends the error response and returns `False`, which causes the handler to return early without processing the request.

The credentials are stored in a Python dictionary at the module level. This is suitable for a learning project but would be replaced with a database and hashed passwords (using something like bcrypt) in a production system.