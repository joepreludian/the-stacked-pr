"""The page shell shared by every screen."""

from html import escape

NAV = (
    ("Dashboard", "/"),
    ("Projects", "/projects"),
    ("Settings", "/settings"),
)


def page(title, body, script=None):
    links = "".join(f'<a href="{href}">{escape(label)}</a>' for label, href in NAV)
    script_tag = f'<script src="/static/{escape(script)}" defer></script>' if script else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{escape(title)} · Teamdesk</title>
  <link rel="stylesheet" href="/static/app.css">
  {script_tag}
</head>
<body>
  <nav class="topnav">{links}</nav>
  <main>
    <h1>{escape(title)}</h1>
    {body}
  </main>
</body>
</html>"""


def settings_tabs(team_id, active):
    tabs = (
        ("General", f"/settings/teams/{team_id}/general"),
        ("Team", f"/settings/teams/{team_id}"),
        ("Billing", f"/settings/teams/{team_id}/billing"),
    )
    items = "".join(
        f'<a href="{href}" class="tab{" is-active" if label == active else ""}">{label}</a>'
        for label, href in tabs
    )
    return f'<div class="tabs">{items}</div>'
