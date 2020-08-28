#!/usr/bin/env bash

DOMAIN="${1}"
EXPECTED_IP="${2}"
EXPECTED_TIME="${3}"

echo assert_domain DOMAIN=$DOMAIN EXPECTED_IP=$EXPECTED_IP EXPECTED_TIME=$EXPECTED_TIME
if ! OUTPUT="$(/usr/bin/time -f "%e" python3 -m dnslib.client --server 127.0.0.1:10053 "${DOMAIN}" --short 2>&1)"; then
  echo "${OUTPUT}"
  echo DNS Lookup failed
  exit 1
fi
echo DNS Lookup completed
if [ "$(echo "${OUTPUT}" | head -n1)" != "${EXPECTED_IP}" ]; then
  echo "${OUTPUT}"
  echo "expected ip: ${EXPECTED_IP}"
  exit 1
fi
if [ "$(expr "$(echo "${OUTPUT}" | tail -1)" '>' "${EXPECTED_TIME}")" == "1" ]; then
  echo "${OUTPUT}"
  echo "expected to complete in less then ${EXPECTED_TIME} seconds"
  exit 1
fi
exit 0
