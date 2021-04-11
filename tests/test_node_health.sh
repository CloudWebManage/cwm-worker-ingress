#!/usr/bin/env bash

redis-cli del "node:healthy:testnode0" &&\
sleep 1 &&\
if [ -e .node_healthy ]; then echo FAILED: .node_healthy file exists after redis cleared && exit 1; fi &&\
redis-cli set "node:healthy:testnode0" "" &&\
sleep 1 &&\
if [ "$(cat .node_healthy)" != "OK" ]; then echo FAILED: .node_healthy not ok after redis key set && exit 1; fi &&\
redis-cli del "node:healthy:testnode0" &&\
sleep 1 &&\
if [ -e .node_healthy ]; then echo FAILED: .node_healthy file exists after redis key deleted && exit 1; fi &&\
exit 0
