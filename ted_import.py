# -*- coding: utf-8 -*-
"""
TED-Database Importer.
"""

import re
from pprint import pprint
import requests

from concurrent.futures import ThreadPoolExecutor
from requests_futures.sessions import FuturesSession

from print_c import print_c
from utilities import find_results, timeit, sizeof_fmt

URL = 'http://ted:5000'

s = requests.Session()
s.headers = {'accept': 'application/json'}

s2 = FuturesSession(max_workers=10)

@timeit
def reset():
    print_c("Reset: ", end='')
    r = s.get('{}/{}/'.format(URL, 'reset'))
    if r.ok:
        print_c("OK", color='green')
    else:
        print_c("FAILED", color='red')
    assert(r.ok)


@timeit
def create_run(name, description, machine=None, integration=None):
    print_c("Create run `{}`: ".format(name), end='')
    data = {'name': name, 'description': description, 'Machine': machine,
            'Integration': integration}
    r = s.post('{}/{}/'.format(URL, 'run'), data=data)
    if r.ok:
        print_c("OK", color='green')
    else:
        print_c("FAILED", color='red')
    assert(r.ok)
    return r.json()['id']


sequence_ids = {}
@timeit
def create_sequence(name):
    print_c("Create run `{}`: ".format(name), end='')
    if name in sequence_ids:
        print_c("FOUND", color='blue')
        return sequence_ids[name]

    data = {'name': name}
    r = s.post('{}/{}/'.format(URL, 'sequence'), data=data)
    if r.ok:
        print_c("OK", color='green')
        create_sequence.count += 1
        sequence_ids[name] = r.json()['id']
        return r.json()['id']
    elif r.status_code == 409:
        print_c("EXISTS", color='purple')
        r = s.get('{}/{}/'.format(URL, 'sequence'), params={'q': name})
        if not r.ok:
            print r.text
        assert(r.ok)
        return r.json()['sequences'][0]['id']
    else:
        print_c("FAILED", color='red')
        return None

create_sequence.count = 0


@timeit
def create_result(run_id, sequence_id, time, state):
    print_c("Create result `{}`: ".format(state), end='')
    data = {'run_id': run_id, 'sequence_id': sequence_id, 'time': time,
            'state': state}
    r = s.post('{}/{}/'.format(URL, 'result'), data=data)
    if r.ok:
        print_c("OK", color='green')
    else:
        print_c("FAILED", color='red')
    assert(r.ok)


@timeit
def create_log(run_id, sequence_id, time, message, severity='Info'):
    data = {'run_id': run_id, 'sequence_id': sequence_id, 'time': time,
            'severity': severity, 'message': message}
    r = s2.post('{}/{}/'.format(URL, 'log'), data=data)
    # assert(r.ok)


@timeit
def main():
    result_path = r'R:\PE\Testdata\CRTI-Test\ImplSW_RLS_2013-B\RTIxxxMM\Res'
                  # r'\RTIxxxMM' \
                  # r'\Res\INT05'
    for n, result in enumerate(find_results(result_path)):
        run_id = create_run(result.name, result.description, result.pc, 
                            result.integration)
        sequence_id = create_sequence('Run')
        create_log(run_id, sequence_id, result.start, "Start")
        create_log(run_id, sequence_id, result.end, "End")

        for sequence in result.sequences:
            sequence_id = create_sequence(sequence.id)
            create_result(run_id, sequence_id, sequence.start, sequence.state)
            for l in sequence.log:
                create_log(run_id, sequence_id, l['timestamp'], l['message'],
                           ('Error' if any(w in l['message'].lower()
                                          for w in ('fail', 'error'))
                            else 'Info'))


if __name__ == '__main__':
    reset()
    main()
    timeit.average()

    print create_sequence.count

    import sys
    print sizeof_fmt(sys.getsizeof(timeit.times))
