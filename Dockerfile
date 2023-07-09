FROM python:3.9-alpine AS builder

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
# COPY ./ui/ /shaa
RUN \
    --mount=type=bind,target=.,source=./ui/,rw \
    --mount=type=cache,target=/root/.cache/pip \
    pip install .

FROM python:3.9-alpine AS final
COPY --from=builder /opt/venv /opt/venv

RUN : \
    && apk update \
    && apk add --no-cache \
        openssh-client \
        sshpass \
    && apk cache clean \
    && :


RUN ln -s /opt/venv/lib/python3.9/site-packages/shaa_shell /shaa_shell

RUN adduser -D shaa

COPY ./ansible/roles /home/shaa/.ansible/roles

RUN chown -R shaa:shaa /home/shaa/

USER shaa

ENV PATH="/opt/venv/bin:$PATH"

ENTRYPOINT [ "shaa-shell" ]
