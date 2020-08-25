#!/usr/bin/env bash

DOMAIN=test.wait.domain.available &&\
tests/redis_clear.sh "${DOMAIN}" &&\
tests/assert_wait_domain.sh "${DOMAIN}" "172.17.0.1" 1 "
  redis-cli set 'worker:available:${DOMAIN}' '' >/dev/null &&\
  redis-cli set 'worker:ingress:hostname:${DOMAIN}' 'cwm-worker-test.com' >/dev/null
" 2 &&\
exit 0
