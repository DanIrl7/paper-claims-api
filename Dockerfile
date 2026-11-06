FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CLAIMS_DB=/data/claims.db

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY tests ./tests

# Run as a non-root user, and keep the SQLite database in a directory that user owns.
RUN adduser --disabled-password --gecos "" appuser \
    && mkdir -p /data \
    && chown appuser /data
USER appuser

VOLUME ["/data"]
EXPOSE 8000

CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
