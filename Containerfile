FROM docker.io/library/python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      libreoffice-writer \
      fonts-noto-core \
      fontconfig \
      poppler-utils \
      zip unzip \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md /app/
COPY outline_gen /app/outline_gen
RUN pip install --no-cache-dir -e /app

WORKDIR /work
ENTRYPOINT ["tone9"]
