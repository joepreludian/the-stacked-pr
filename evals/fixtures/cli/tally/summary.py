"""Turn entries into a summary."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CategoryTotal:
    category: str
    count: int
    total: Decimal


@dataclass(frozen=True)
class Summary:
    count: int
    total: Decimal
    first_day: object  # date, or None when there are no entries
    last_day: object
    categories: tuple  # CategoryTotal, largest total first


def summarize(entries, since=None):
    if since is not None:
        entries = [entry for entry in entries if entry.day >= since]
    totals = {}
    for entry in entries:
        count, total = totals.get(entry.category, (0, Decimal("0")))
        totals[entry.category] = (count + 1, total + entry.amount)
    categories = tuple(
        sorted(
            (CategoryTotal(name, count, total) for name, (count, total) in totals.items()),
            key=lambda item: (-item.total, item.category),
        )
    )
    days = [entry.day for entry in entries]
    return Summary(
        count=len(entries),
        total=sum((entry.amount for entry in entries), Decimal("0")),
        first_day=min(days) if days else None,
        last_day=max(days) if days else None,
        categories=categories,
    )
