import os
import time

import redis
import dnslib.server
import prometheus_client

from cwm_worker_ingress import resolver
from cwm_worker_ingress import config
from cwm_worker_ingress import metrics
from cwm_worker_ingress import logs


def update_node_health_file(write_redis_pool):
    if config.NODE_HEALTHY_FILENAME != "disabled":
        if config.get_node_healthy(write_redis_pool):
            if not os.path.exists(config.NODE_HEALTHY_FILENAME):
                with open(config.NODE_HEALTHY_FILENAME, "w") as f:
                    f.write("OK")
        elif os.path.exists(config.NODE_HEALTHY_FILENAME):
            os.unlink(config.NODE_HEALTHY_FILENAME)


def main(port=None):
    main_logs = logs.MainLogs(port)
    if port:
        main_logs.info("VDNS_PROTOCOL={}".format(config.VDNS_PROTOCOL))
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
        main_logs.info("Setting redis to be a replica of {} {}".format(config.REDIS_WRITE_HOST, str(config.REDIS_WRITE_PORT)))
        replicaof_res = r.execute_command('REPLICAOF', config.REDIS_WRITE_HOST, str(config.REDIS_WRITE_PORT))
        assert replicaof_res.startswith(b'OK'), "invalid response from REPLICAOF: %s" % replicaof_res
    main_logs.info("Starting prometheus http server on port {}".format(config.PROMETHEUS_METRICS_PORT))
    prometheus_client.start_http_server(config.PROMETHEUS_METRICS_PORT)
    if port:
        servers = [
            *[dnslib.server.DNSServer(
                resolver.Resolver(read_redis_pool, write_redis_pool, metrics.Metrics("tcp"), main_logs.get_resolver_logs("tcp")),
                port=int(port), address='localhost', tcp=True, logger=main_logs.get_dns_logger("tcp")
            ) for _ in range(config.TCP_THREADS)],
            *[dnslib.server.DNSServer(
                resolver.Resolver(read_redis_pool, write_redis_pool, metrics.Metrics("udp"), main_logs.get_resolver_logs("udp")),
                port=int(port), address='localhost', tcp=False, logger=main_logs.get_dns_logger("udp")
            ) for _ in range(config.UDP_THREADS)],
        ]
        for i, s in enumerate(servers):
            main_logs.info("starting thread {} ({})".format(i+1, s.server))
            s.start_thread()
    else:
        print("Not starting any VDNS servers")

    try:
        while True:
            # we use the write_redis_pool here to ensure we have good connection to the source redis pool
            update_node_health_file(write_redis_pool)
            time.sleep(config.MAIN_PROCESS_REFRESH_SECONDS)
    except KeyboardInterrupt:
        pass
    finally:
        for s in servers:
            s.stop()
