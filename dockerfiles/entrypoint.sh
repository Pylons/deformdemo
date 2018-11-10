#!/bin/sh
set -e

if [ "${1}" == "mini" ]; then
  CONFIG=/app/mini.ini
else
  CONFIG=/app/demo.ini
fi

exec su-exec pylons pserve "${CONFIG}"
