"""Minimal request, response and routing helpers on top of WSGI."""

import json
import re


class BadRequest(Exception):
    """The request body could not be understood."""


class Request:
    def __init__(self, environ, conn, base_url=""):
        self.method = environ["REQUEST_METHOD"].upper()
        self.path = environ.get("PATH_INFO", "/")
        self.headers = {
            key[5:].replace("_", "-").lower(): value
            for key, value in environ.items()
            if key.startswith("HTTP_")
        }
        length = int(environ.get("CONTENT_LENGTH") or 0)
        self.body = environ["wsgi.input"].read(length) if length else b""
        self.conn = conn
        self.base_url = base_url
        self.params = {}
        self.user = None
        self.membership = None
        self.team_id = None

    def json(self):
        if not self.body:
            return {}
        try:
            data = json.loads(self.body)
        except ValueError:
            raise BadRequest("Body must be valid JSON")
        if not isinstance(data, dict):
            raise BadRequest("Body must be a JSON object")
        return data


class Response:
    def __init__(self, body=b"", status=200, content_type="text/plain; charset=utf-8"):
        self.body = body
        self.status = status
        self.content_type = content_type


def json_response(data, status=200):
    return Response(json.dumps(data).encode(), status, "application/json")


def html_response(html, status=200):
    return Response(html.encode(), status, "text/html; charset=utf-8")


def no_content():
    return Response(b"", 204)


def error(status, message):
    return json_response({"error": message}, status)


class Router:
    """Routes like ``/api/teams/<team_id>/members/<member_id>``."""

    def __init__(self):
        self._routes = []

    def add(self, method, pattern, handler):
        regex = re.compile("^" + re.sub(r"<(\w+)>", r"(?P<\1>[^/]+)", pattern) + "$")
        self._routes.append((method.upper(), regex, handler))

    def dispatch(self, request):
        path_matched = False
        for method, regex, handler in self._routes:
            match = regex.match(request.path)
            if not match:
                continue
            path_matched = True
            if method != request.method:
                continue
            request.params = match.groupdict()
            try:
                return handler(request)
            except BadRequest as exc:
                return error(400, str(exc))
        if path_matched:
            return error(405, "Method not allowed")
        return error(404, "Not found")
