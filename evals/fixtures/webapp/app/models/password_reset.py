"""Password reset tokens."""

import secrets
from datetime import datetime, timedelta, timezone

TTL_HOURS = 2


def _now():
    return datetime.now(timezone.utc)


def create(conn, user_id):
    token = secrets.token_urlsafe(32)
    expires_at = (_now() + timedelta(hours=TTL_HOURS)).isoformat()
    conn.execute(
        "INSERT INTO password_resets (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, expires_at),
    )
    conn.commit()
    return token


def find_valid(conn, token):
    row = conn.execute(
        "SELECT * FROM password_resets WHERE token = ? AND used_at IS NULL", (token,)
    ).fetchone()
    if row is None or datetime.fromisoformat(row["expires_at"]) <= _now():
        return None
    return dict(row)
