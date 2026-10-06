"""Who is signed in, and what they may do in a team.

The proxy in front of the app owns the session and sets ``X-User-Id`` on every
authenticated request.
"""

from functools import wraps

from app.http import error
from app.models import membership


def current_user(request):
    user_id = request.headers.get("x-user-id", "")
    if not user_id.isdigit():
        return None
    row = request.conn.execute(
        "SELECT id, email, name FROM users WHERE id = ?", (int(user_id),)
    ).fetchone()
    return dict(row) if row else None


def require_team_role(*roles):
    """Require a signed-in member of the team in the URL.

    With no arguments any member is allowed. With roles, the member must hold
    one of them. People outside the team get 404, so team ids cannot be probed.
    """

    def decorator(handler):
        @wraps(handler)
        def wrapped(request):
            user = current_user(request)
            if user is None:
                return error(401, "Sign in required")
            team_id = request.params.get("team_id", "")
            if not team_id.isdigit():
                return error(404, "Team not found")
            member = membership.find_for_user(request.conn, int(team_id), user["id"])
            if member is None:
                return error(404, "Team not found")
            if roles and member["role"] not in roles:
                return error(403, "You do not have permission to do that")
            request.user = user
            request.membership = member
            request.team_id = int(team_id)
            return handler(request)

        return wrapped

    return decorator
