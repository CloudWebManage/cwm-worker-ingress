#!/usr/bin/env bash

DOMAIN="${1}"

for KEY in "worker:available:${DOMAIN}" "worker:ingress:hostname:${DOMAIN}" "worker:error:${DOMAIN}" "worker:initialize:${DOMAIN}"; do
  redis-cli del "${KEY}" >/dev/null
done
