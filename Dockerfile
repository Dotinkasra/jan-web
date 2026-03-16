FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY module ./module
COPY web ./web

RUN pip install --upgrade pip && pip install \
    fastapi==0.115.6 \
    jinja2==3.1.5 \
    python-multipart==0.0.20 \
    rich==13.9.4 \
    uvicorn==0.34.0

EXPOSE 8080

CMD ["sh", "-c", "uvicorn web.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
