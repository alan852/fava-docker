# syntax=docker/dockerfile:1

# Stage 1: Build dependencies in isolated virtual environment
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=0 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_WARN_SCRIPT_LOCATION=1

# Install build dependencies reusing apt cache
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY ./requirements.txt /tmp/requirements.txt

# Install python dependencies with pip cache mount and binary wheel preference
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefer-binary -r /tmp/requirements.txt \
    && find /opt/venv -type d -name "__pycache__" -prune -exec rm -rf {} +

# Stage 2: Minimal runtime image
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    FAVA_HOST="0.0.0.0" \
    HOME="/home/beancount-user"

# Install runtime dependencies reusing apt cache
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    git \
    dumb-init \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --gid 1000 beancount-user \
    && adduser --uid 1000 --gid 1000 --disabled-password --gecos "" beancount-user \
    && mkdir -p /home/beancount-user && chmod 777 /home/beancount-user \
    && chmod 666 /etc/passwd /etc/group \
    && git config --system --add safe.directory '*'

COPY --from=builder /opt/venv /opt/venv
COPY --chmod=755 start_services.sh auto_commit.py repayment_notify.py /scripts/

EXPOSE 5000
WORKDIR /workspace

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:5000").read()' || exit 1

USER beancount-user

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["/scripts/start_services.sh"]
