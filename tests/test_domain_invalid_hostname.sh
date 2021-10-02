#!/usr/bin/env bash

DOMAIN=test.domain.available &&\
tests/redis_clear.sh "${DOMAIN}" &&\
redis-cli set "hostname:available:${DOMAIN}" "" >/dev/null &&\
redis-cli set "hostname:ingress:hostname:${DOMAIN}" '{"http":"invalid.host.name"}' >/dev/null &&\
tests/assert_domain.sh "${DOMAIN}" "127.0.0.1" "10" &&\
exit 0
