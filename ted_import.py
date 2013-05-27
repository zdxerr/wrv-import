# -*- coding: utf-8 -*-
"""
TED-Database Importer.
"""

import re

import requests

from utilities import find_results, timeit, sizeof_fmt

URL = 'http://ted:5000'

s = requests.Session()
s.headers = {'accept': 'application/json'}

@timeit
def reset():
    r = s.get('{}/{}/'.format(URL, 'reset'))
    assert(r.ok)


@timeit
def create_run(name, description, tags=[]):
    data = {'name': name, 'description': description, 'tags': " ".join(tags)}
    r = s.post('{}/{}/'.format(URL, 'run'), data=data)
    assert(r.ok)
    return r.json['id']


@timeit
def create_sequence(name, tags=[]):
    data = {'name': name, 'tags': " ".join(tags)}
    r = s.post('{}/{}/'.format(URL, 'sequence'), data=data)
    print "-"*3, name,
    if r.ok:
        print 'OK'
        create_sequence.count += 1
        return r.json['id']
    elif r.status_code == 409:
        print 'EXISTS'
        r = s.get('{}/{}/'.format(URL, 'sequence'), params={'q': name})
        if not r.ok:
            print r.text
        assert(r.ok)
        return r.json['sequences'][0]['id']
    else:
        print 'ERROR', r.status_code, r.text
        return None

create_sequence.count = 0


@timeit
def create_result(run_id, sequence_id, time, state):
    data = {'run_id': run_id, 'sequence_id': sequence_id, 'time': time,
            'state': state}
    r = s.post('{}/{}/'.format(URL, 'result'), data=data)
    assert(r.ok)


@timeit
def create_log(run_id, sequence_id, time, message, severity='Info'):
    data = {'run_id': run_id, 'sequence_id': sequence_id, 'time': time,
            'severity': severity, 'message': message}
    r = s.post('{}/{}/'.format(URL, 'log'), data=data)
    assert(r.ok)


@timeit
def main():
    result_path = r'R:\PE\Testdata\CRTI-Test\ImplSW_RLS_2013-A\RTIxxxMM' \
                  r'\Res\INT05\T_01'
    for n, result in enumerate(find_results(result_path)):
        print n, result, result.start
        run_id = create_run(result.name, result.description, result.tags)

        for sequence in result.sequences:
            sequence_id = create_sequence(sequence.id,
                                          re.split(r'\W+', sequence.id))
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
