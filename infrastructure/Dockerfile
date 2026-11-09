# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm
RUN --mount=type=secret,id=proxy_ca,target=/run/secrets/proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export SSL_CERT_FILE=/run/secrets/proxy_ca; fi; \
    apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY services/api/pyproject.toml services/api/requirements.lock /app/
RUN --mount=type=secret,id=proxy_ca,target=/run/secrets/proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export PIP_CERT=/run/secrets/proxy_ca; fi; \
    pip install --no-cache-dir -r requirements.lock
COPY --chown=10001:10001 services/api/frametrace /app/frametrace
RUN useradd --create-home --uid 10001 app && mkdir -p /app/var && chown app:app /app/var
USER app
EXPOSE 8000
CMD ["uvicorn", "frametrace.app:app", "--host", "0.0.0.0", "--port", "8000"]
