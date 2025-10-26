FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=stimul_ico.settings

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /app/backend
COPY frontend /app/frontend
COPY README.md requirements.txt /app/
COPY setup.sh /app/setup.sh
RUN chmod +x /app/setup.sh

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

COPY test_app.py /app/test_app.py

# Railway will provide PORT via environment variable
EXPOSE $PORT

CMD ["/app/entrypoint.sh"]
