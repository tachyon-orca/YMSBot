FROM python:3.16.0a1-slim-trixie@sha256:df293ba3b89f458e1aad6051b62ff1c4fad7b3b52b8147ae9cc4b667f9cf2741

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir --only-binary=:all: --require-hashes -r /tmp/requirements.txt \
    && python -m pip check

CMD ["python", "bot.py"]
