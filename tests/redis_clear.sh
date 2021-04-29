#!/usr/bin/env bash

DOMAIN="${1}"

for KEY in "hostname:available:${DOMAIN}" "hostname:ingress:hostname:${DOMAIN}" "hostname:error:${DOMAIN}" "hostname:initialize:${DOMAIN}"; do
  redis-cli del "${KEY}" >/dev/null
done
