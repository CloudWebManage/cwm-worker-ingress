#!/usr/bin/env bash

DOMAIN=test.domain.error &&\
tests/redis_clear.sh "${DOMAIN}" &&\
redis-cli set "hostname:error:${DOMAIN}" "" >/dev/null &&\
tests/assert_domain.sh "${DOMAIN}" "127.0.0.1" "0.5" &&\
exit 0
