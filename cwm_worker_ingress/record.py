import datetime

import dnslib


TYPE_LOOKUP = {
    dnslib.A: dnslib.QTYPE.A,
    dnslib.AAAA: dnslib.QTYPE.AAAA,
    dnslib.CNAME: dnslib.QTYPE.CNAME,
    dnslib.MX: dnslib.QTYPE.MX,
    dnslib.NS: dnslib.QTYPE.NS,
    dnslib.SOA: dnslib.QTYPE.SOA,
    dnslib.TXT: dnslib.QTYPE.TXT,
}


EPOCH = datetime.datetime(1970, 1, 1)
SERIAL = int((datetime.datetime.utcnow() - EPOCH).total_seconds())


class Record:
    def __init__(self, rdata_type, *args, rtype=None, rname=None, ttl=None, **kwargs):
        if isinstance(rdata_type, dnslib.RD):
            # actually an instance, not a type
            self._rtype = TYPE_LOOKUP[rdata_type.__class__]
            rdata = rdata_type
        else:
            self._rtype = TYPE_LOOKUP[rdata_type]
            if rdata_type == dnslib.SOA and len(args) == 2:
                # add sensible times to SOA
                args += ((
                    SERIAL,  # serial number
                    60 * 60 * 1,  # refresh
                    60 * 60 * 3,  # retry
                    60 * 60 * 24,  # expire
                    60 * 60 * 1,  # minimum
                ),)
            rdata = rdata_type(*args)

        if rtype:
            self._rtype = rtype
        self._rname = rname
        self.kwargs = dict(
            rdata=rdata,
            ttl=self.sensible_ttl() if ttl is None else ttl,
            **kwargs,
        )

    def try_rr(self, q):
        if q.qtype == dnslib.QTYPE.ANY or q.qtype == self._rtype:
            return self.as_rr(q.qname)

    def as_rr(self, alt_rname):
        return dnslib.RR(rname=self._rname or alt_rname, rtype=self._rtype, **self.kwargs)

    def sensible_ttl(self):
        if self._rtype in (dnslib.QTYPE.NS, dnslib.QTYPE.SOA):
            return 60 * 60 * 24
        else:
            return 10

    @property
    def is_soa(self):
        return self._rtype == dnslib.QTYPE.SOA

    def __str__(self):
        return '{} {}'.format(dnslib.QTYPE[self._rtype], self.kwargs)
