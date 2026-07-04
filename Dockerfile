# Multi-stage Dockerfile for Railway (Phase 14)
FROM python:3.11-slim AS builder
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml .
RUN uv sync || pip install -e ".[dev]"
COPY . .

FROM python:3.11-slim AS runtime
WORKDIR /app
COPY --from=builder /app /app
ENV PYTHONPATH=/app/src
ENV PORT=8080
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s CMD python -c "import urllib.request,os,json; p=os.environ.get('PORT','8080'); r=urllib.request.urlopen(f'http://127.0.0.1:{p}/health'); print(r.read())" || exit 1
CMD ["python", "main.py", "run", "--interface", "web"]
