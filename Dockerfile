FROM python:3.13.0a3-alpine AS builder

RUN : \
    && apk update \
    && apk add --no-cache \
        gcc \
        musl-dev \
        openssl-dev \
        libffi-dev \
    && apk cache clean \
    && :

RUN python3 -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /shaa

RUN \
    --mount=type=bind,target=.,source=./ui/,rw \
    --mount=type=cache,target=/root/.cache/pip \
    pip install .

FROM python:3.13.0a3-alpine AS final

RUN : \
    && apk update \
    && apk add --no-cache \
        openssh-client \
        sshpass \
    && apk cache clean \
    && :

RUN adduser -D shaa

COPY ./ansible/roles /home/shaa/.ansible/roles

RUN chown -R shaa:shaa /home/shaa/

COPY ./ansible/vault-password.py /opt/shaa/

RUN chown -R shaa:shaa /opt/shaa/

RUN chmod +x /opt/shaa/vault-password.py

COPY --from=builder /opt/venv /opt/venv

USER shaa

ENV PATH="/opt/venv/bin:$PATH"

ENTRYPOINT [ "shaa-shell" ]
