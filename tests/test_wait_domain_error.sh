#!/usr/bin/env bash

DOMAIN=test.wait.domain.error &&\
tests/redis_clear.sh "${DOMAIN}" &&\
tests/assert_wait_domain.sh "${DOMAIN}" "127.0.0.1" 1 "redis-cli set hostname:error:${DOMAIN} '' >/dev/null" 2 &&\
exit 0
