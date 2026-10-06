"""JSON API for requesting a password reset."""

from app.http import error, json_response
from app.mail import password_reset as reset_mail
from app.models import password_reset


def request_reset(request):
    email = str(request.json().get("email", "")).strip().lower()
    if "@" not in email:
        return error(422, "email is required")
    row = request.conn.execute(
        "SELECT id, email, name FROM users WHERE lower(email) = ?", (email,)
    ).fetchone()
    if row is not None:
        token = password_reset.create(request.conn, row["id"])
        reset_mail.send(request.conn, dict(row), token, request.base_url)
    # Same answer either way, so the endpoint cannot be used to find accounts.
    return json_response({"ok": True}, 202)


def register(router):
    router.add("POST", "/api/password-resets", request_reset)
