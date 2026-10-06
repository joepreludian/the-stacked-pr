# tally

A small command-line tool that summarises expense CSV files. Standard library only.

```bash
python3 -m tally report sample.csv
python3 -m tally report sample.csv --since 2026-02-01
```

## Layout

| Path | What lives there |
|---|---|
| `tally/__main__.py` | Argument parsing and the `report` command |
| `tally/loader.py` | Reads and validates the CSV |
| `tally/summary.py` | Turns entries into a `Summary` |
| `tally/table.py` | Renders a `Summary` as a text table |
| `tests/` | `unittest` suites |

## Tests

```bash
python3 -m unittest discover -s tests
```
