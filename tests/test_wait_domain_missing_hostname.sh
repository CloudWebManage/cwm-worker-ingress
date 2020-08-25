#!/usr/bin/env bash

DOMAIN=test.wait.domain.available &&\
tests/redis_clear.sh "${DOMAIN}" &&\
tests/assert_wait_domain.sh "${DOMAIN}" "127.0.0.1" 1 "
  redis-cli set 'worker:available:${DOMAIN}' '' >/dev/null
" 6 &&\
exit 0
