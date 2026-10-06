"""Shared test setup: an in-memory database with one team, and a WSGI caller."""

import io
import json

from app import db
from app.models import membership
from app.server import make_app

ADA, BO, CY, DEE = 1, 2, 3, 4  # admin, member, viewer, not on the team
TEAM = 1


def make_env():
    conn = db.connect()
    db.migrate(conn)
    conn.execute("INSERT INTO teams (id, name) VALUES (?, 'Acme')", (TEAM,))
    for user_id, name in ((ADA, "Ada"), (BO, "Bo"), (CY, "Cy"), (DEE, "Dee")):
        conn.execute(
            "INSERT INTO users (id, email, name) VALUES (?, ?, ?)",
            (user_id, f"{name.lower()}@example.com", name),
        )
    conn.commit()
    membership.add(conn, TEAM, ADA, "admin")
    membership.add(conn, TEAM, BO, "member")
    membership.add(conn, TEAM, CY, "viewer")
    return conn, make_app(conn, base_url="https://teamdesk.test")


def call(app, method, path, user_id=None, body=None):
    raw = json.dumps(body).encode() if body is not None else b""
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "CONTENT_LENGTH": str(len(raw)),
        "wsgi.input": io.BytesIO(raw),
    }
    if user_id is not None:
        environ["HTTP_X_USER_ID"] = str(user_id)
    captured = {}

    def start_response(status, headers):
        captured["status"] = int(status.split()[0])
        captured["headers"] = dict(headers)

    data = b"".join(app(environ, start_response))
    if captured["headers"].get("Content-Type", "").startswith("application/json") and data:
        return captured["status"], json.loads(data)
    return captured["status"], data.decode()
