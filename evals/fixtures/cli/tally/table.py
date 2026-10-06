"""Render a Summary as a text table."""


def _money(amount):
    return f"{amount:,.2f}"


def format_table(summary):
    if summary.count == 0:
        return "No entries."
    rows = [(item.category, str(item.count), _money(item.total)) for item in summary.categories]
    rows.append(("total", str(summary.count), _money(summary.total)))
    header = ("category", "entries", "amount")
    widths = [max(len(row[i]) for row in rows + [header]) for i in range(3)]

    def line(row):
        return f"{row[0]:<{widths[0]}}  {row[1]:>{widths[1]}}  {row[2]:>{widths[2]}}"

    rule = "  ".join("-" * width for width in widths)
    period = f"{summary.first_day.isoformat()} to {summary.last_day.isoformat()}"
    return "\n".join([period, "", line(header), rule, *map(line, rows[:-1]), rule, line(rows[-1])])
