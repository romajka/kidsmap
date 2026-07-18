FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc curl gettext default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system --gid 10001 kidsmap \
    && adduser --system --uid 10001 --ingroup kidsmap --home /app --no-create-home kidsmap

COPY requirements /app/requirements
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements/production.txt

COPY . /app

RUN mkdir -p /app/media /app/staticfiles \
    && chown -R kidsmap:kidsmap /app

USER kidsmap

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl --fail --silent --show-error --header "X-Forwarded-Proto: https" http://127.0.0.1:8000/healthz || exit 1

CMD ["./scripts/start-server.sh"]
