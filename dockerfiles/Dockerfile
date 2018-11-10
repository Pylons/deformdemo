FROM python:3.6-alpine as base

FROM base as builder

RUN mkdir /wheelhouse

COPY . /app
WORKDIR /app

RUN pip wheel -r requirements.txt --wheel-dir=/wheelhouse

FROM base

LABEL maintainer "Erico Andrei <ericof@gmail.com>" \
      org.label-schema.name = "Deform Demo" \
      org.label-schema.description = "Demonstration application for Deform, a Python lib for generating HTML forms." \
      org.label-schema.vendor = "Pylons Project" \
      org.label-schema.docker.cmd = "docker run -d -p 8000:8522 deformdemo:latest"

RUN adduser -s /bin/false -D -H pylons \
    && apk --no-cache add \
    tini \
    su-exec

COPY --from=builder /wheelhouse /wheelhouse

RUN pip install --no-cache-dir --no-index --find-links=/wheelhouse deformdemo

WORKDIR /app

COPY demo.ini mini.ini /app/
COPY dockerfiles/entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/sbin/tini", "--", "/usr/local/bin/entrypoint.sh"]

EXPOSE 8522
