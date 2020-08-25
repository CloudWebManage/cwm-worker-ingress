#!/usr/bin/env bash

DOMAIN=test.domain.available &&\
tests/redis_clear.sh "${DOMAIN}" &&\
redis-cli set "worker:available:${DOMAIN}" "" >/dev/null &&\
redis-cli set "worker:ingress:hostname:${DOMAIN}" "cwm-worker-test.com" >/dev/null &&\
tests/assert_domain.sh "${DOMAIN}" "172.17.0.1" "0.5" &&\
exit 0
