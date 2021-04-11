import os
import json
import socket
from contextlib import contextmanager

import redis


# the workloads protocol this vdns is serving
VDNS_PROTOCOL = os.environ.get("VDNS_PROTOCOL") or 'http'

# how long to wait between checks for domain availability
WAIT_FOR_DOMAIN_AVAILABILITY_REFRESH_SECONDS = float(os.environ.get("WAIT_FOR_DOMAIN_AVAILABILITY_REFRESH_SECONDS") or "0.01")

# how long to wait for domain availability before giving up
WAIT_FOR_DOMAIN_AVAILABILITY_MAX_WAIT_SECONDS = int(os.environ.get("WAIT_FOR_DOMAIN_AVAILABILITY_MAX_WAIT_SECONDS") or "5")

REDIS_READ_POOL_MAX_CONNECTIONS = int(os.environ.get("REDIS_READ_POOL_MAX_CONNECTIONS") or "50")
REDIS_READ_POOL_TIMEOUT = int(os.environ.get("REDIS_READ_POOL_TIMEOUT") or "5")

REDIS_WRITE_POOL_MAX_CONNECTIONS = int(os.environ.get("REDIS_WRITE_POOL_MAX_CONNECTIONS") or "50")
REDIS_WRITE_POOL_TIMEOUT = int(os.environ.get("REDIS_WRITE_POOL_TIMEOUT") or "5")

# how long to wait between main process checks for kill signals
MAIN_PROCESS_REFRESH_SECONDS = float(os.environ.get("MAIN_PROCESS_REFRESH_SECONDS") or "0.1")

DEBUG = os.environ.get("DEBUG") == "yes"

# higher numbers = more debug logs
DEBUG_VERBOSITY = int(os.environ.get("DEBUG_VERBOSITY") or "1")

REDIS_HOST = os.environ.get("REDIS_HOST") or "localhost"
REDIS_PORT = int(os.environ.get("REDIS_PORT") or "6379")
REDIS_WRITE_HOST = os.environ.get("REDIS_WRITE_HOST")
REDIS_WRITE_PORT = int(os.environ.get("REDIS_WRITE_PORT") or "6379")
if REDIS_WRITE_HOST:
    REDIS_REPLICA = True
else:
    REDIS_REPLICA = False
    REDIS_WRITE_HOST, REDIS_WRITE_PORT = REDIS_HOST, REDIS_PORT
REDIS_KEY_WORKER_AVAILABLE = "worker:available:{}"
REDIS_KEY_WORKER_INGRESS_HOSTNAME = "worker:ingress:hostname:{}"
REDIS_KEY_WORKER_ERROR = "worker:error:{}"
REDIS_KEY_WORKER_INITIALIZE = "worker:initialize:{}"

PROMETHEUS_METRICS_PORT = int(os.environ.get("PROMETHEUS_METRICS_PORT") or "8088")
PROMETHEUS_METRICS_WITH_DOMAIN_LABEL = os.environ.get("PROMETHEUS_METRICS_WITH_DOMAIN_LABEL") == "yes"

TCP_THREADS = int(os.environ.get("TCP_THREADS", 0))
UDP_THREADS = int(os.environ.get("UDP_THREADS", 5))

REDIS_KEY_NODE_HEALTHY_SUFFIX = os.environ.get("REDIS_KEY_NODE_HEALTHY_SUFFIX") or "testnode0"
REDIS_KEY_NODE_HEALTHY = (os.environ.get("REDIS_KEY_NODE_HEALTHY") or "node:healthy") + ":" + REDIS_KEY_NODE_HEALTHY_SUFFIX
NODE_HEALTHY_FILENAME = os.environ.get("NODE_HEALTHY_FILENAME") or ".node_healthy"


@contextmanager
def get_redis(redis_pool):
    r = redis.Redis(connection_pool=redis_pool)
    try:
        yield r
    finally:
        r.close()


def get_domain_internal_hostname(redis_pool, domain):
    """returns the domain's internal_hostname if domain is available for receiving connections else returns None"""
    hostname = None
    with get_redis(redis_pool) as r:
        if r.exists(REDIS_KEY_WORKER_AVAILABLE.format(domain)):
            hostname = r.get(REDIS_KEY_WORKER_INGRESS_HOSTNAME.format(domain))
    if hostname:
        try:
            return json.loads(hostname.decode())[VDNS_PROTOCOL]
        except:
            return None
    else:
        return None


def get_domain_ipv4(redis_pool, domain):
    """returns the domain's ipv4 if domain is available for receiving connections else returns None"""
    internal_hostname = get_domain_internal_hostname(redis_pool, domain)
    if internal_hostname:
        try:
            return socket.gethostbyname(internal_hostname)
        except socket.gaierror:
            return None
    else:
        return None


def is_domain_error(redis_pool, domain):
    with get_redis(redis_pool) as r:
        return r.exists(REDIS_KEY_WORKER_ERROR.format(domain)) > 0


def set_domain_initialize(redis_pool, domain):
    with get_redis(redis_pool) as r:
        r.set(REDIS_KEY_WORKER_INITIALIZE.format(domain), "")


def get_node_healthy(redis_pool):
    with get_redis(redis_pool) as r:
        return r.exists(REDIS_KEY_NODE_HEALTHY)
