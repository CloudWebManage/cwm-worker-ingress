#!/usr/bin/env bash

! redis-cli ping >/dev/null && echo failed redis ping && exit 1

ALL_RES=0
for TEST in tests/test_*.sh; do
    echo "-- ${TEST}"
    if $TEST; then
        echo OK
    else
        echo FAILED
        ALL_RES=1
    fi
done
[ "${ALL_RES}" != "0" ] && exit 1

echo "-- tests/assert_metrics.py"
sleep 7
! python3 tests/assert_metrics.py && echo FAILED && exit 1
echo OK
