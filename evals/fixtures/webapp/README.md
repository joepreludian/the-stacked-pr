# Teamdesk

A small team workspace app. It uses only the Python standard library: WSGI,
`sqlite3` and `unittest`. There is nothing to install.

## Layout

| Path | What lives there |
|---|---|
| `app/db.py` | SQLite connection and the migration runner |
| `app/http.py` | Request, response and router helpers |
| `app/auth.py` | Who is signed in, and role checks |
| `app/models/` | Data access, one module per table |
| `app/handlers/` | JSON API endpoints |
| `app/mail/` | Outgoing mail queue, messages and templates |
| `app/screens/` | Server-rendered pages |
| `app/static/` | Browser JavaScript for those pages |
| `migrations/` | Numbered SQL files, applied in order |
| `tests/` | `unittest` suites |

## Conventions

- Handlers stay thin: validate input, call a model function, shape the response.
- Every email goes through `app/mail/queue.py`. Nothing sends mail inside a request.
- A screen is a module in `app/screens/` plus, when it needs behaviour, one file in `app/static/`.
- Sign-in is handled by the proxy in front of the app, which sets `X-User-Id`.

## Tests

```bash
python3 -m unittest discover -s tests
```
