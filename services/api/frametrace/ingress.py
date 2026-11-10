"""Bound and spool uploads before Starlette's multipart parser sees the body."""

import tempfile

from starlette.responses import JSONResponse

from .config import settings


class UploadBoundary:
    def __init__(self, app):
        self.app = app
        self.active = 0

    async def __call__(self, scope, receive, send):
        if (
            scope["type"] != "http"
            or scope["method"] != "POST"
            or scope["path"] != "/v1/recognitions"
        ):
            return await self.app(scope, receive, send)
        limit = settings.max_upload_bytes + settings.multipart_overhead_bytes
        headers = dict(scope["headers"])
        raw_length = headers.get(b"content-length")
        if raw_length is not None:
            try:
                length = int(raw_length)
                if length < 0:
                    raise ValueError
            except ValueError:
                return await JSONResponse({"detail": "Invalid Content-Length."}, 400)(
                    scope, receive, send
                )
            if length > limit:
                return await JSONResponse({"detail": "Request exceeds the upload limit."}, 413)(
                    scope, receive, send
                )
        # No await between checking and incrementing on the ASGI event loop.
        if self.active >= settings.max_inflight_uploads:
            return await JSONResponse(
                {"detail": "Uploads are busy; please retry."}, 429, headers={"Retry-After": "5"}
            )(scope, receive, send)
        self.active += 1
        try:
            with tempfile.TemporaryFile(dir=settings.data_dir) as spool:
                size = 0
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    body = message.get("body", b"")
                    size += len(body)
                    if size > limit:
                        return await JSONResponse(
                            {"detail": "Request exceeds the upload limit."}, 413
                        )(scope, receive, send)
                    spool.write(body)
                    if not message.get("more_body", False):
                        break
                spool.seek(0)
                delivered = False

                async def replay():
                    nonlocal delivered
                    if delivered:
                        return await receive()
                    chunk = spool.read(64 * 1024)
                    delivered = spool.tell() == size
                    return {"type": "http.request", "body": chunk, "more_body": not delivered}

                return await self.app(scope, replay, send)
        finally:
            self.active -= 1
