FROM python:3.12-slim AS builder

RUN adduser --uid 1245 beancount-user

RUN apt-get update \
    && apt-get install -y git dumb-init \
    && apt-get clean \
    && apt-get autoclean \
    && apt-get autoremove --purge  -y \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /tmp/requirements.txt
RUN python -m venv /opt/venv \
    && pip3 install --no-cache-dir -r /tmp/requirements.txt

COPY start_services.sh /scripts/start_services.sh
RUN chmod +x /scripts/start_services.sh

FROM builder AS runtime

ENV FAVA_HOST="0.0.0.0"
EXPOSE 5000

USER beancount-user 
WORKDIR /workspace

RUN git config --global --add safe.directory /workspace

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD [ "/scripts/start_services.sh" ]
