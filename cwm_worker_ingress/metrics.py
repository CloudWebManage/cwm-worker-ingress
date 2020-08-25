from collections import defaultdict
from cwm_worker_ingress import config
import json


class Metrics:

    def __init__(self):
        self.metrics = defaultdict(int)

    def send(self, metric):
        self.metrics[metric] += 1


def save(metrics_tcp, metrics_udp, uptime_seconds):
    with open(config.METRICS_SAVE_PATH, "a") as f:
        json.dump({
            "tcp": dict(metrics_tcp.metrics),
            "udp": dict(metrics_udp.metrics),
            "uptime": uptime_seconds
        }, f)
        f.write("\n")
