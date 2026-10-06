"""Plain-text mail templates.

A template is a ``.txt`` file whose first line is ``Subject: ...``. Values are
filled in with ``$name`` placeholders.
"""

from pathlib import Path
from string import Template

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def render(template, **context):
    """Return ``(subject, body)`` for the named template."""
    text = Template((TEMPLATES_DIR / f"{template}.txt").read_text()).substitute(context)
    first_line, _, rest = text.partition("\n")
    if not first_line.startswith("Subject: "):
        raise ValueError(f"Template {template} must start with a Subject line")
    return first_line[len("Subject: "):].strip(), rest.lstrip("\n")
