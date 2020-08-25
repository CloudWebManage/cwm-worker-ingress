import dnslib
import time
import datetime

from cwm_worker_ingress import config
from cwm_worker_ingress import record


def reply_success(request, reply, ipv4):
    if config.DEBUG:
        print("reply_success: {}".format(ipv4), flush=True)
    generated = record.Record(dnslib.A, ipv4)
    reply.add_answer(generated.as_rr(request.q.qname))


def reply_error(request, reply, msg):
    if config.DEBUG:
        print("reply_error: {}".format(msg), flush=True)
    generated = record.Record(dnslib.A, "127.0.0.1")
    reply.add_answer(generated.as_rr(request.q.qname))


def wait_for_domain_availability(read_redis_pool, write_redis_pool, domain):
    if config.DEBUG:
        print("wait_for_domain_availability: {}".format(domain), flush=True)
    config.set_domain_initialize(write_redis_pool, domain)
    start_time = datetime.datetime.now()
    while True:
        time.sleep(config.WAIT_FOR_DOMAIN_AVAILABILITY_REFRESH_SECONDS)
        ipv4 = config.get_domain_ipv4(read_redis_pool, domain)
        if ipv4:
            return ipv4
        elif config.is_domain_error(read_redis_pool, domain):
            if config.DEBUG:
                print("wait_for_domain_availability: domain is in error state", flush=True)
            return None
        elif (datetime.datetime.now() - start_time).total_seconds() >= int(config.WAIT_FOR_DOMAIN_AVAILABILITY_MAX_WAIT_SECONDS):
            if config.DEBUG:
                print("wait_for_domain_availability: waited too long", flush=True)
            return None


class Resolver:

    def __init__(self, read_redis_pool, write_redis_pool, metrics):
        self.read_redis_pool = read_redis_pool
        self.write_redis_pool = write_redis_pool
        self.metrics = metrics

    def resolve(self, request, handler):
        reply = request.reply()
        if request.q.qtype == dnslib.QTYPE.A:
            domain = str(request.q.qname)[:-1]
            if config.DEBUG:
                print("Resolving: {}".format(domain), flush=True)
            ipv4 = config.get_domain_ipv4(self.read_redis_pool, domain)
            if ipv4:
                reply_success(request, reply, ipv4)
                self.metrics.send('reply_success')
            elif config.is_domain_error(self.read_redis_pool, domain):
                reply_error(request, reply, "worker is in error state (domain={})".format(domain))
                self.metrics.send('worker is in error state')
                self.metrics.send('reply_error')
            else:
                self.metrics.send('wait for domain availability')
                ipv4 = wait_for_domain_availability(self.read_redis_pool, self.write_redis_pool, domain)
                if ipv4:
                    reply_success(request, reply, ipv4)
                    self.metrics.send('success after wait')
                    self.metrics.send('reply_success')
                else:
                    reply_error(request, reply, "failed to get availability (domain={})".format(domain))
                    self.metrics.send('failed to get availability')
                    self.metrics.send('reply_error')
        elif config.DEBUG:
            print("Unhandled request type: {}".format(request.q.qtype), flush=True)
            self.metrics.send('unhandled request type')
            self.metrics.send('reply_none')
        return reply
