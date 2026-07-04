# Multi-stage Dockerfile for Railway (Phase 14)
FROM python:3.11-slim AS builder
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY pyproject.toml .
COPY src ./src
RUN pip install --no-cache-dir .
COPY . .
RUN python -c "import typer, fastapi, uvicorn; print('deps ok in builder')"

FROM python:3.11-slim AS runtime
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app/src
ENV PORT=8080
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s CMD python -c "import urllib.request,os,sys;p=os.environ.get('PORT','8080');try:r=urllib.request.urlopen('http://127.0.0.1:'+p+'/health',timeout=5);print('ok') except Exception as e:print('fail',e);sys.exit(1)" || exit 1
CMD ["python", "main.py", "run", "--interface", "web"]
