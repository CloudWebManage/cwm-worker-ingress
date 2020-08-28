import time
import datetime

import dnslib.server
from dnslib.server import DNSLogger
import redis

from cwm_worker_ingress import resolver
from cwm_worker_ingress import config
from cwm_worker_ingress import metrics


def main(port):
    start_time = datetime.datetime.now()
    if config.DEBUG:
        print("{} starting server in debug mode on port {}".format(start_time, port), flush=True)
    else:
        print("{} starting server on port {}".format(start_time, port), flush=True)
    print("REDIS_HOST={} REDIS_PORT={}".format(config.REDIS_HOST, config.REDIS_PORT), flush=True)
    read_redis_pool = redis.BlockingConnectionPool(
        max_connections=config.REDIS_READ_POOL_MAX_CONNECTIONS, timeout=config.REDIS_READ_POOL_TIMEOUT,
        host=config.REDIS_HOST, port=config.REDIS_PORT
    )
    write_redis_pool = redis.BlockingConnectionPool(
        max_connections=config.REDIS_WRITE_POOL_MAX_CONNECTIONS, timeout=config.REDIS_WRITE_POOL_TIMEOUT,
        host=config.REDIS_WRITE_HOST, port=config.REDIS_WRITE_PORT
    )
    for pool in (read_redis_pool, write_redis_pool):
        r = redis.Redis(connection_pool=pool)
        assert r.ping()
        r.close()
    if config.REDIS_REPLICA:
        r = redis.Redis(connection_pool=read_redis_pool)
        print("Setting redis to be a replica of {} {}".format(config.REDIS_WRITE_HOST, str(config.REDIS_WRITE_PORT)), flush=True)
        replicaof_res = r.execute_command('REPLICAOF', config.REDIS_WRITE_HOST, str(config.REDIS_WRITE_PORT))
        assert replicaof_res == b'OK', "invalid response from REPLICAOF: %s" % replicaof_res
    if config.DEBUG:
        logger = DNSLogger()
    else:
        logger = DNSLogger("-recv,-send,-request,-reply,-truncated,-error,-data")
    metrics_tcp = metrics.Metrics()
    metrics_udp = metrics.Metrics()
    servers = [
        dnslib.server.DNSServer(
            resolver.Resolver(read_redis_pool, write_redis_pool, metrics_tcp),
            port=int(port), address='localhost', tcp=True, logger=logger
        ),
        dnslib.server.DNSServer(
            resolver.Resolver(read_redis_pool, write_redis_pool, metrics_udp),
            port=int(port), address='localhost', tcp=False, logger=logger
        ),
    ]
    for i, s in enumerate(servers):
        print("starting thread {}".format(i), flush=True)
        s.start_thread()

    last_metrics_time = datetime.datetime.now()
    try:
        while True:
            time.sleep(config.MAIN_PROCESS_REFRESH_SECONDS)
            if (datetime.datetime.now() - last_metrics_time).total_seconds() >= config.METRICS_SAVE_EVERY_SECONDS:
                metrics.save(metrics_tcp, metrics_udp, (datetime.datetime.now() - start_time).total_seconds())
                last_metrics_time = datetime.datetime.now()
    except KeyboardInterrupt:
        pass
    finally:
        for s in servers:
            s.stop()
