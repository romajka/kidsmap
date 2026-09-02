FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc curl gettext default-libmysqlclient-dev libpq-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# Translation binaries must live in the web image. Release tasks run in a
# temporary container, so compiling them only there leaves Gunicorn with the
# Russian fallback catalogue after a restart.
RUN python manage.py compilemessages --ignore .venv --ignore venv

EXPOSE 8000

CMD ["./scripts/start-server.sh"]
