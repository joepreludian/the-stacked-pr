"""JSON API for the members of a team."""

from app.auth import require_team_role
from app.http import error, json_response, no_content
from app.models import membership


def _public(row):
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "email": row["email"],
        "name": row["name"],
        "role": row["role"],
        "joined_at": row["created_at"],
    }


def _member_id(request):
    raw = request.params.get("member_id", "")
    return int(raw) if raw.isdigit() else None


@require_team_role()
def list_members(request):
    rows = membership.list_for_team(request.conn, request.team_id)
    return json_response({"members": [_public(row) for row in rows]})


@require_team_role("admin")
def update_member(request):
    role = request.json().get("role")
    if role not in membership.ROLES:
        return error(422, "role must be one of: " + ", ".join(membership.ROLES))
    member_id = _member_id(request)
    if member_id is None:
        return error(404, "Member not found")
    try:
        updated = membership.change_role(request.conn, request.team_id, member_id, role)
    except membership.LastAdminError:
        return error(409, "A team must keep at least one admin")
    if updated is None:
        return error(404, "Member not found")
    return json_response({"member": _public(updated)})


@require_team_role("admin")
def remove_member(request):
    member_id = _member_id(request)
    if member_id is None:
        return error(404, "Member not found")
    try:
        removed = membership.remove(request.conn, request.team_id, member_id)
    except membership.LastAdminError:
        return error(409, "A team must keep at least one admin")
    if not removed:
        return error(404, "Member not found")
    return no_content()


def register(router):
    router.add("GET", "/api/teams/<team_id>/members", list_members)
    router.add("PATCH", "/api/teams/<team_id>/members/<member_id>", update_member)
    router.add("DELETE", "/api/teams/<team_id>/members/<member_id>", remove_member)
