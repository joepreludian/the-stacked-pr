"""Settings > Team: the list of members and their roles."""

from html import escape

from app.auth import require_team_role
from app.http import html_response
from app.models import membership
from app.screens.layout import page, settings_tabs


def _role_cell(member, can_manage):
    if not can_manage:
        return escape(member["role"].capitalize())
    options = "".join(
        f'<option value="{role}"{" selected" if role == member["role"] else ""}>'
        f"{role.capitalize()}</option>"
        for role in membership.ROLES
    )
    return f'<select class="js-role" aria-label="Role for {escape(member["name"])}">{options}</select>'


def _row(member, can_manage, current_user_id):
    you = ' <span class="badge">You</span>' if member["user_id"] == current_user_id else ""
    remove = (
        '<button type="button" class="js-remove link-danger">Remove</button>' if can_manage else ""
    )
    return f"""
      <tr data-member-id="{member["id"]}" data-member-name="{escape(member["name"])}">
        <td>{escape(member["name"])}{you}</td>
        <td>{escape(member["email"])}</td>
        <td>{_role_cell(member, can_manage)}</td>
        <td class="actions">{remove}</td>
      </tr>"""


def render(team_id, members, viewer):
    can_manage = viewer["role"] == "admin"
    rows = "".join(_row(member, can_manage, viewer["user_id"]) for member in members)
    count = f"{len(members)} member" + ("" if len(members) == 1 else "s")
    body = f"""
    {settings_tabs(team_id, "Team")}
    <section id="team-members" data-team-id="{team_id}">
      <header class="section-header">
        <h2>Members</h2>
        <p class="muted">{count}</p>
      </header>
      <p class="error" role="alert" hidden></p>
      <table class="data-table">
        <thead>
          <tr><th>Name</th><th>Email</th><th>Role</th><th></th></tr>
        </thead>
        <tbody>{rows}
        </tbody>
      </table>
    </section>"""
    return page("Team settings", body, script="team_members.js" if can_manage else None)


@require_team_role()
def show(request):
    members = membership.list_for_team(request.conn, request.team_id)
    return html_response(render(request.team_id, members, request.membership))


def register(router):
    router.add("GET", "/settings/teams/<team_id>", show)
