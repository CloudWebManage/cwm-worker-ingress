import sys
import subprocess


def main(num_processes):
    num_processes = int(num_processes)
    processes = {}
    print(f'starting {num_processes} processes')
    for process_num in range(1, num_processes+1):
        processes[process_num] = subprocess.Popen([
            'nslookup', '-port=10053', 'foobar.com', '-', '127.0.0.1'
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print('waiting for processes to terminate')
    for process_num, process in processes.items():
        returncode = process.wait()
        print(f'{process_num}: returncode {returncode} output {process.stdout.read()}')


main(*sys.argv[1:])
