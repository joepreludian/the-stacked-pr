"""The password reset email."""

from app.mail import queue
from app.mail.templates import render
from app.models.password_reset import TTL_HOURS


def send(conn, user, token, base_url):
    subject, body = render(
        "password_reset",
        name=user["name"],
        link=f"{base_url}/reset-password?token={token}",
        hours=TTL_HOURS,
    )
    return queue.enqueue(conn, user["email"], subject, body)
