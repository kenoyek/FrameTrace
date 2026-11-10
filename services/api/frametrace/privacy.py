class PrivateResponses:
    """Recognition and history responses must not enter browser or intermediary caches."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        async def private_send(message):
            if message["type"] == "http.response.start":
                headers = [
                    (key, value)
                    for key, value in message.get("headers", [])
                    if key.lower() not in {b"cache-control", b"vary"}
                ]
                message = dict(
                    message,
                    headers=headers
                    + [(b"cache-control", b"no-store"), (b"vary", b"Authorization")],
                )
            await send(message)

        private = scope["type"] == "http" and scope.get("path", "").startswith("/v1/")
        await self.app(scope, receive, private_send if private else send)
