import sys

from cwm_worker_ingress import vdns


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "vdns":
            exit(vdns.main(*sys.argv[2:]))
    raise Exception("Invalid invocation (sys.argv={})".format(sys.argv))
