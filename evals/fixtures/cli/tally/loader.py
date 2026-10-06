"""Read and validate an expenses CSV."""

import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

REQUIRED = ("date", "category", "amount")


class LoadError(Exception):
    """The file could not be used. The message is safe to show to the user."""


@dataclass(frozen=True)
class Entry:
    day: date
    category: str
    amount: Decimal
    note: str = ""


def load(path):
    try:
        handle = open(path, newline="")
    except OSError as exc:
        raise LoadError(f"Cannot read {path}: {exc.strerror}")
    with handle:
        reader = csv.DictReader(handle)
        missing = [name for name in REQUIRED if name not in (reader.fieldnames or [])]
        if missing:
            raise LoadError(f"{path} is missing columns: {', '.join(missing)}")
        return [_entry(row, line) for line, row in enumerate(reader, start=2)]


def _entry(row, line):
    try:
        day = date.fromisoformat(row["date"].strip())
    except ValueError:
        raise LoadError(f"Line {line}: date must look like 2026-01-31")
    try:
        amount = Decimal(row["amount"].strip())
    except InvalidOperation:
        raise LoadError(f"Line {line}: amount must be a number")
    category = row["category"].strip().lower()
    if not category:
        raise LoadError(f"Line {line}: category is empty")
    return Entry(day, category, amount, (row.get("note") or "").strip())
