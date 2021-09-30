#!/usr/bin/env bash

DOMAIN="${1}"
EXPECTED_IP="${2}"
SECONDS_BEFORE_EVAL="${3}"
EVAL_SCRIPT="${4}"
EXPECTED_TIME="${5}"

TEMPFILE=`mktemp`

/usr/bin/time -f "%e" python3 -m dnslib.client --server localhost:10053 "${DOMAIN}" --short > $TEMPFILE 2>&1 &
PID=$!
sleep "${SECONDS_BEFORE_EVAL}"
eval "${EVAL_SCRIPT}"

if ! wait $PID; then
  cat $TEMPFILE
  rm -f $TEMPFILE
  echo DNS Lookup failed
  exit 1
fi
if [ "$(cat $TEMPFILE | head -n1)" != "${EXPECTED_IP}" ]; then
  cat $TEMPFILE
  rm -f $TEMPFILE
  echo "expected ip: ${EXPECTED_IP}"
  exit 1
fi
if [ "$(expr "$(cat $TEMPFILE | tail -1)" '>' "${EXPECTED_TIME}")" == "1" ]; then
  cat $TEMPFILE
  rm -f $TEMPFILE
  echo "expected to complete in less than ${EXPECTED_TIME} seconds"
  exit 1
fi
rm -f $TEMPFILE
exit 0
