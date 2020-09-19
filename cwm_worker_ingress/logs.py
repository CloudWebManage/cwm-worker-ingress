import datetime

from dnslib.server import DNSLogger

from cwm_worker_ingress import config


class ResolverLogs:

    def __init__(self, protocol):
        self.protocol = protocol

    def debug(self, msg, verbosity=5, start_time=None):
        if config.DEBUG and config.DEBUG_VERBOSITY >= verbosity:
            if start_time:
                msg = "{} ({} seconds)".format(msg, (datetime.datetime.now() - start_time).total_seconds())
            print(msg, flush=True)


class MainLogs:

    def __init__(self, port):
        self.start_time = datetime.datetime.now()
        self.last_uptime_seconds = 0
        if config.DEBUG:
            self.info("{} starting server in debug mode on port {} with debug verbosity {}".format(self.start_time, port, config.DEBUG_VERBOSITY))
        else:
            self.info("{} starting server on port {}".format(self.start_time, port))
        self.info("REDIS_HOST={} REDIS_PORT={}".format(config.REDIS_HOST, config.REDIS_PORT))

    def info(self, msg):
        print(msg, flush=True)

    def get_dns_logger(self, protocol):
        if config.DEBUG and config.DEBUG_VERBOSITY > 7:
            return DNSLogger()
        else:
            return DNSLogger("-recv,-send,-request,-reply,-truncated,-error,-data")

    def get_resolver_logs(self, protocol):
        return ResolverLogs(protocol)