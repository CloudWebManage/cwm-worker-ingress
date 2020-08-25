import json

with open('.metrics') as f:
  metrics = json.loads(f.readlines()[-1])

assert metrics['tcp'] == {}
for k, v in {
  'reply_success': 2,
  'worker is in error state': 1,
  'reply_error': 6,
  'wait for domain availability': 6,
  'failed to get availability': 5,
  'success after wait': 1
}.items():
    assert metrics['udp'][k] == v, "udp[{}] expected {} actual {}".format(k, v, metrics['udp'][k])
assert metrics['uptime'] > 15
