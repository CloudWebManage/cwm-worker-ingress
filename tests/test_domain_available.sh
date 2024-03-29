#!/usr/bin/env bash

DOMAIN=test.domain.available &&\
tests/redis_clear.sh "${DOMAIN}" &&\
redis-cli set "hostname:available:${DOMAIN}" "" >/dev/null &&\
redis-cli set "hostname:ingress:hostname:${DOMAIN}" '{"http":"cwm-worker-test-http.com"}' >/dev/null &&\
tests/assert_domain.sh "${DOMAIN}" "172.17.0.1" "0.5" &&\
exit 0
