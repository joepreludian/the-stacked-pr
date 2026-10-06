"""The WSGI application."""

from app.handlers import memberships, password_resets
from app.http import Request, Router
from app.screens import team_members

STATUS_TEXT = {
    200: "OK", 201: "Created", 202: "Accepted", 204: "No Content",
    400: "Bad Request", 401: "Unauthorized", 403: "Forbidden", 404: "Not Found",
    405: "Method Not Allowed", 409: "Conflict", 422: "Unprocessable Entity",
}


def build_router():
    router = Router()
    memberships.register(router)
    password_resets.register(router)
    team_members.register(router)
    return router


def make_app(conn, base_url="http://localhost:8000"):
    router = build_router()

    def app(environ, start_response):
        response = router.dispatch(Request(environ, conn, base_url))
        status = f"{response.status} {STATUS_TEXT.get(response.status, '')}".strip()
        start_response(status, [("Content-Type", response.content_type)])
        return [response.body]

    return app
