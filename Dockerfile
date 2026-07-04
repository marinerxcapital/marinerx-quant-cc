# Multi-stage Dockerfile for Railway (Phase 14)
FROM python:3.11-slim AS builder
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml .
RUN uv sync || pip install -e ".[dev]"
COPY . .
# Ensure installed packages are in python path for runtime copy
RUN python -c "import typer; print('deps check ok')"

FROM python:3.11-slim AS runtime
WORKDIR /app
COPY --from=builder /app /app
ENV PYTHONPATH=/app/src:/app/.venv/lib/python3.11/site-packages
ENV PATH="/app/.venv/bin:$PATH"
ENV PORT=8080
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s CMD python -c "
import urllib.request, os, sys
p = os.environ.get('PORT', '8080')
try:
    r = urllib.request.urlopen(f'http://127.0.0.1:{p}/health', timeout=5)
    print(r.read().decode()[:200])
except Exception as e: 
    print('health fail', e)
    sys.exit(1)
" || exit 1
CMD ["python", "main.py", "run", "--interface", "web"]
