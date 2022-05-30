import sys
import datetime
import subprocess
from pprint import pprint
from collections import defaultdict


def main(num_processes):
    num_processes = int(num_processes)
    processes = {}
    print(f'starting {num_processes} processes')
    for process_num in range(1, num_processes+1):
        processes[process_num] = subprocess.Popen([
            'nslookup', '-port=10053', 'foobar.com', '-', '127.0.0.1'
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    start_time = datetime.datetime.now()
    print('waiting for processes to terminate')
    stats = defaultdict(int)
    for process_num, process in processes.items():
        returncode = process.wait()
        output = process.stdout.read().decode()
        if returncode == 0:
            if 'Address: 127.0.0.1' in output:
                stats['success'] += 1
            else:
                raise Exception(f'Success with unknown output: {output}')
        elif 'connection timed out; no servers could be reached' in output:
            stats['timed out'] += 1
            if not stats['seconds to first timeout']:
                stats['seconds to first timeout'] = (datetime.datetime.now() - start_time).total_seconds()
        else:
            raise Exception(f'Failed with unknown output: {output}')
    pprint(dict(stats))


main(*sys.argv[1:])
