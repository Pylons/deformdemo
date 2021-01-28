FROM python:3.9-alpine as base

FROM base as builder

RUN mkdir /wheelhouse

COPY . /app
WORKDIR /app

RUN apk add git gcc musl-dev python3-dev libffi-dev openssl-dev
RUN pip install --upgrade pip setuptools
RUN pip wheel -r requirements-dev.txt --wheel-dir=/wheelhouse

FROM base

LABEL maintainer "Steve Piercy <web@stevepiercy.com>" \
      org.label-schema.name = "Deform Demo" \
      org.label-schema.description = "Demonstration application for Deform, a Python library for generating HTML forms." \
      org.label-schema.vendor = "Pylons Project" \
      org.label-schema.docker.cmd = "docker run -d -p 8000:8523 deformdemo3:latest"

RUN adduser -s /bin/false -D -H pylons \
    && apk --no-cache add \
    tini \
    su-exec

COPY --from=builder /wheelhouse /wheelhouse

RUN pip install --pre --no-cache-dir --no-index --find-links=/wheelhouse deformdemo

WORKDIR /app

COPY demo.ini mini.ini /app/
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["pserve", "/app/demo.ini"]
EXPOSE 8523
