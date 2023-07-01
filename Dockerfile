FROM python:3.9-slim AS builder

RUN set -xeu; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*;

RUN python3 -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY ./ui/ /shaa
RUN pip install /shaa

FROM python:3.9-slim AS final
COPY --from=builder /opt/venv /opt/venv
COPY ./inputrc /root/.inputrc
COPY ./ansible/roles /root/.ansible/roles

RUN ln -s /opt/venv/lib/python3.9/site-packages/shaa_shell /shaa_shell

RUN set -xeu; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        ssh \
        sshpass \
        ; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*;

ENV PATH="/opt/venv/bin:$PATH"
