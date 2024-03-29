#!/usr/bin/env bash

DOMAIN=test.domain.available &&\
tests/redis_clear.sh "${DOMAIN}" &&\
redis-cli set "hostname:available:${DOMAIN}" "" >/dev/null &&\
tests/assert_domain.sh "${DOMAIN}" "127.0.0.1" "6" &&\
exit 0
