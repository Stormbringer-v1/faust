"""
Request ID middleware — pure ASGI (no BaseHTTPMiddleware).

BaseHTTPMiddleware causes event loop issues with asyncpg in tests
because it creates tasks on a different event loop.
This pure ASGI implementation avoids that entirely.
"""

import uuid

from starlette.types import ASGIApp, Receive, Scope, Send


class RequestIDMiddleware:
    """
    Pure ASGI middleware that injects X-Request-ID into each request/response.

    - Reads X-Request-ID from incoming request headers (allows client-supplied IDs).
    - Falls back to a new UUID4 if absent.
    - Stores on scope["state"]["request_id"] for use in logging.
    - Adds X-Request-ID to the response headers.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Extract or generate the request ID
        headers = dict(scope.get("headers", []))
        request_id = (
            headers.get(b"x-request-id", b"").decode() or str(uuid.uuid4())
        )

        # Stash on scope state for logging access
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["request_id"] = request_id

        # Wrap send to inject header into responses
        async def send_with_request_id(message):
            if message["type"] == "http.response.start":
                headers_list = list(message.get("headers", []))
                headers_list.append(
                    (b"x-request-id", request_id.encode())
                )
                message = {**message, "headers": headers_list}
            await send(message)

        await self.app(scope, receive, send_with_request_id)
