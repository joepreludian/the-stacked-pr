"""Team memberships: who belongs to a team, and with which role."""

ROLES = ("admin", "member", "viewer")

_SELECT = """
    SELECT m.id, m.team_id, m.role, m.created_at,
           u.id AS user_id, u.email, u.name
    FROM memberships m
    JOIN users u ON u.id = m.user_id
"""


class LastAdminError(Exception):
    """The change would leave the team without an admin."""


def list_for_team(conn, team_id):
    rows = conn.execute(_SELECT + " WHERE m.team_id = ? ORDER BY u.name", (team_id,))
    return [dict(row) for row in rows]


def find(conn, team_id, membership_id):
    row = conn.execute(
        _SELECT + " WHERE m.team_id = ? AND m.id = ?", (team_id, membership_id)
    ).fetchone()
    return dict(row) if row else None


def find_for_user(conn, team_id, user_id):
    row = conn.execute(
        _SELECT + " WHERE m.team_id = ? AND u.id = ?", (team_id, user_id)
    ).fetchone()
    return dict(row) if row else None


def add(conn, team_id, user_id, role="member"):
    if role not in ROLES:
        raise ValueError(f"Unknown role: {role}")
    cursor = conn.execute(
        "INSERT INTO memberships (team_id, user_id, role) VALUES (?, ?, ?)",
        (team_id, user_id, role),
    )
    conn.commit()
    return find(conn, team_id, cursor.lastrowid)


def _admin_count(conn, team_id):
    return conn.execute(
        "SELECT COUNT(*) FROM memberships WHERE team_id = ? AND role = 'admin'", (team_id,)
    ).fetchone()[0]


def _guard_last_admin(conn, current):
    if current["role"] == "admin" and _admin_count(conn, current["team_id"]) == 1:
        raise LastAdminError()


def change_role(conn, team_id, membership_id, role):
    if role not in ROLES:
        raise ValueError(f"Unknown role: {role}")
    current = find(conn, team_id, membership_id)
    if current is None:
        return None
    if role != "admin":
        _guard_last_admin(conn, current)
    conn.execute("UPDATE memberships SET role = ? WHERE id = ?", (role, membership_id))
    conn.commit()
    return find(conn, team_id, membership_id)


def remove(conn, team_id, membership_id):
    current = find(conn, team_id, membership_id)
    if current is None:
        return False
    _guard_last_admin(conn, current)
    conn.execute("DELETE FROM memberships WHERE id = ?", (membership_id,))
    conn.commit()
    return True
