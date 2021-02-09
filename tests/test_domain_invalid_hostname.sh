#!/usr/bin/env bash

DOMAIN=test.domain.available &&\
tests/redis_clear.sh "${DOMAIN}" &&\
redis-cli set "worker:available:${DOMAIN}" "" >/dev/null &&\
redis-cli set "worker:ingress:hostname:${DOMAIN}" '{"http":"invalid.host.name"}' >/dev/null &&\
tests/assert_domain.sh "${DOMAIN}" "127.0.0.1" "6" &&\
exit 0
