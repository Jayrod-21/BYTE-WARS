"""
tests/_auth.py — Shared test helper to authenticate an httpx AsyncClient.

Routes that mutate state now require `Authorization: Bearer <jwt>`.
Tests use this helper to register a user and apply the token as a
default header, so subsequent `client.post(...)` calls authenticate
automatically.
"""


async def login_default_user(client, username: str = "test-user", password: str = "secure-pass-1") -> dict:
    """
    Register `username` (idempotent) and configure the AsyncClient to
    send the resulting JWT on every request.

    Returns the user dict (`{id, username, ...}`) so tests can pass the
    user_id when route bodies still require it.
    """
    resp = await client.post("/api/auth/register", json={
        "username": username,
        "password": password,
    })
    if resp.status_code == 400:
        # Username taken (test re-run without clearing the store).
        resp = await client.post("/api/auth/login", json={
            "username": username,
            "password": password,
        })
    assert resp.status_code in (200, 201), f"auth setup failed: {resp.status_code} {resp.text}"
    body = resp.json()
    client.headers["Authorization"] = f"Bearer {body['token']}"
    return body["user"]
