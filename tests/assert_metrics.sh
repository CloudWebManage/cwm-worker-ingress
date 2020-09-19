#!/usr/bin/env bash

curl localhost:8080 | grep 'resolver_request_latency_count{domain="",protocol="udp",status="success"} 1.0' &&\
curl localhost:8080 | grep 'resolver_request_latency_count{domain="",protocol="udp",status="success_cached"} 1.0' &&\
curl localhost:8080 | grep 'resolver_request_latency_count{domain="",protocol="udp",status="error_cached"} 1.0' &&\
curl localhost:8080 | grep 'resolver_request_latency_count{domain="",protocol="udp",status="error"} 5.0'
