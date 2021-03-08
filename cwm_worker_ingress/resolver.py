import dnslib
import time
import datetime

from cwm_worker_ingress import config
from cwm_worker_ingress import record


class Resolver:

    def __init__(self, read_redis_pool, write_redis_pool, metrics, logs):
        self.read_redis_pool = read_redis_pool
        self.write_redis_pool = write_redis_pool
        self.metrics = metrics
        self.logs = logs

    def _reply_success(self, request, reply, ipv4):
        self.logs.debug("reply_success: {}".format(ipv4))
        generated = record.Record(dnslib.A, ipv4)
        reply.add_answer(generated.as_rr(request.q.qname))

    def _reply_error(self, request, reply, msg):
        self.logs.debug("reply_error: {}".format(msg))
        generated = record.Record(dnslib.A, "127.0.0.1")
        reply.add_answer(generated.as_rr(request.q.qname))

    def _wait_for_domain_availability(self, domain):
        self.logs.debug("wait_for_domain_availability: {}".format(domain))
        config.set_domain_initialize(self.write_redis_pool, domain)
        start_time = datetime.datetime.now()
        while True:
            time.sleep(config.WAIT_FOR_DOMAIN_AVAILABILITY_REFRESH_SECONDS)
            ipv4 = config.get_domain_ipv4(self.read_redis_pool, domain)
            if ipv4:
                return ipv4
            elif config.is_domain_error(self.read_redis_pool, domain):
                self.logs.debug("wait_for_domain_availability: domain is in error state")
                return None
            elif (datetime.datetime.now() - start_time).total_seconds() >= int(
                    config.WAIT_FOR_DOMAIN_AVAILABILITY_MAX_WAIT_SECONDS):
                self.logs.debug("wait_for_domain_availability: waited too long")
                return None

    def resolve(self, request, handler):
        start_time = datetime.datetime.now()
        reply = request.reply()
        if request.q.qtype == dnslib.QTYPE.A:
            domain = str(request.q.qname)[:-1]
            if domain and len(domain) > 2:
                if domain.startswith("__echo__"):
                    self.logs.debug("Echo domain: {}".format(domain), 1)
                    self._reply_success(request, reply, domain.replace("__echo__", ""))
                else:
                    self.logs.debug("Resolving: {}".format(domain))
                    ipv4 = config.get_domain_ipv4(self.read_redis_pool, domain)
                    if ipv4:
                        self.logs.debug("success_cached (domain={})".format(domain), 1, start_time=start_time)
                        self._reply_success(request, reply, ipv4)
                        self.metrics.resolver_success_cached(start_time, domain)
                    elif config.is_domain_error(self.read_redis_pool, domain):
                        self.logs.debug("error_cached (domain={})".format(domain), 1, start_time=start_time)
                        self._reply_error(request, reply, "worker is in error state (domain={})".format(domain))
                        self.metrics.resolver_error_cached(start_time, domain)
                    else:
                        ipv4 = self._wait_for_domain_availability(domain)
                        if ipv4:
                            self.logs.debug("success (domain={})".format(domain), 1, start_time=start_time)
                            self._reply_success(request, reply, ipv4)
                            self.metrics.resolver_success(start_time, domain)
                        else:
                            self.logs.debug("error (domain={})".format(domain), 1, start_time=start_time)
                            self._reply_error(request, reply, "failed to get availability (domain={})".format(domain))
                            self.metrics.resolver_error(start_time, domain)
            else:
                self.logs.debug("invalid domain (domain={})".format(domain), 8, start_time=start_time)
                self.metrics.resolver_invalid_domain(start_time)
        else:
            self.logs.debug("Unhandled request type: {}".format(request.q.qtype), 9, start_time=start_time)
            self.metrics.resolver_unhandled_request_type(start_time)
        return reply
