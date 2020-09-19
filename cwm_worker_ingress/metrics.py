import datetime

from prometheus_client import Histogram

from cwm_worker_ingress import config


_h_resolver_request_latency = Histogram('resolver_request_latency', 'resolver request latency', ["protocol", "domain", "status"])


class Metrics:

    def __init__(self, protocol):
        self.labels = [protocol]

    def resolver_success_cached(self, start_time, domain):
        if not config.PROMETHEUS_METRICS_WITH_DOMAIN_LABEL:
            domain = ""
        _h_resolver_request_latency.labels(*self.labels, domain, "success_cached").observe((datetime.datetime.now() - start_time).total_seconds())

    def resolver_error_cached(self, start_time, domain):
        if not config.PROMETHEUS_METRICS_WITH_DOMAIN_LABEL:
            domain = ""
        _h_resolver_request_latency.labels(*self.labels, domain, "error_cached").observe((datetime.datetime.now() - start_time).total_seconds())

    def resolver_success(self, start_time, domain):
        if not config.PROMETHEUS_METRICS_WITH_DOMAIN_LABEL:
            domain = ""
        _h_resolver_request_latency.labels(*self.labels, domain, "success").observe((datetime.datetime.now() - start_time).total_seconds())

    def resolver_error(self, start_time, domain):
        if not config.PROMETHEUS_METRICS_WITH_DOMAIN_LABEL:
            domain = ""
        _h_resolver_request_latency.labels(*self.labels, domain, "error").observe((datetime.datetime.now() - start_time).total_seconds())

    def resolver_unhandled_request_type(self, start_time):
        domain = ""
        _h_resolver_request_latency.labels(*self.labels, domain, "unhandled_request_type").observe((datetime.datetime.now() - start_time).total_seconds())

    def resolver_invalid_domain(self, start_time):
        domain = ""
        _h_resolver_request_latency.labels(*self.labels, domain, "invalid_domain").observe((datetime.datetime.now() - start_time).total_seconds())
