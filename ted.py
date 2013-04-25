# -*- coding: utf-8 -*-

import re

import requests

from test_result_parser import RTITEResult
import find_results
from utilities import timeit, sizeof_fmt

URL = 'http://ted:5000'


@timeit
def reset():
    r = requests.get('{}/{}/'.format(URL, 'reset'))
    assert(r.ok)


@timeit
def create_run(time):
    data = {'time': time}
    r = requests.post('{}/{}/'.format(URL, 'run'), data=data)
    assert(r.ok)
    return r.json['id']


@timeit
def create_sequence(name, tags=[]):
    data = {'name': name, 'tags': " ".join(tags)}
    r = requests.post('{}/{}/'.format(URL, 'sequence'), data=data)
    print "-"*3, name,
    if r.ok:
        print 'OK'
        create_sequence.count += 1
    elif r.status_code == 409:
        print 'EXISTS',
        r = requests.get('{}/{}/'.format(URL, 'sequence'), params={'q': name})
        assert(r.ok)
    else:
        print 'ERROR', r.status_code, r.text
        return None
    return r.json['id']

create_sequence.count = 0


@timeit
def create_result(run_id, sequence_id, time, state):
    data = {'run_id': run_id, 'sequence_id': sequence_id, 'time': time,
            'state': state}
    r = requests.post('{}/{}/'.format(URL, 'result'), data=data)
    assert(r.ok)


@timeit
def create_log(run_id, sequence_id, time, message):
    data = {'run_id': run_id, 'sequence_id': sequence_id, 'time': time,
            'severity': 'Info', 'message': message}
    r = requests.post('{}/{}/'.format(URL, 'log'), data=data)
    assert(r.ok)


@timeit
def main():
    result_path = r'R:\PE\Testdata\CRTI-Test\ImplSW_RLS_2013-A\RTIxxxMM' \
                  r'\Res\INT05\T_01'
    for n, path in enumerate(find_results.results(result_path, 'rtite')):
        result = RTITEResult(path)
        print n, result
        run_id = create_run(result.time)
        for sequence in result.sequences:
            sequence_id = create_sequence(sequence.id,
                                          re.split(r'\W+', sequence.id))
            create_result(run_id, sequence_id, sequence.start, sequence.state)
            for l in sequence.log:
                create_log(run_id, sequence_id, sequence.start, l)


if __name__ == '__main__':
    reset()
    main()
    # timeit.show(False)
    timeit.average()
    print create_sequence.count

    import sys
    print sizeof_fmt(sys.getsizeof(timeit.times))
