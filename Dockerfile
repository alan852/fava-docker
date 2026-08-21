# Stage 1: Build dependencies in isolated virtual environment
FROM python:3.12-slim AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends git build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY ./requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt

# Stage 2: Minimal runtime image
FROM python:3.12-slim AS runtime

RUN apt-get update \
    && apt-get install -y --no-install-recommends git dumb-init \
    && rm -rf /var/lib/apt/lists/*

RUN adduser --uid 1245 --disabled-password --gecos "" beancount-user

# Allow git operations across mounted volumes regardless of custom PUID/PGID
RUN git config --system --add safe.directory '*'

COPY --from=builder /opt/venv /opt/venv
COPY start_services.sh /scripts/start_services.sh
RUN chmod +x /scripts/start_services.sh

ENV PATH="/opt/venv/bin:$PATH"
ENV FAVA_HOST="0.0.0.0"
EXPOSE 5000

WORKDIR /workspace

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python3 -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:5000").read()' || exit 1

USER beancount-user

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["/scripts/start_services.sh"]
