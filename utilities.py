# -*- coding: utf-8 -*-

import time
from math import fsum


def timeit(fn):
    """
    A simple decorator to meassure the execution of times of function calls.
    """
    def wrapped(*args, **kwargs):
        start = time.time()
        result = fn(*args, **kwargs)
        end = time.time()

        arg_list = ['{!r}'.format(v) for v in args] + \
            ['{}={!r}'.format(k, v) for k, v in kwargs.items()]
        c = '{}({})'.format(fn.__name__, ', '.join(arg_list))
        c = (c[:48] + '..') if len(c) > 48 else c

        timeit.times.append({'call': c, 'function': fn.__name__,
                             'args': args, 'kwargs': kwargs, 'start': start,
                             'end': end, 'time': end - start})

        if timeit.verbose:
            timeit.show()

        if result:
            return result
    return wrapped

timeit.verbose = False
timeit.times = []


def show(last=True):
    for t in timeit.times[-1 if last else 0:]:
        print "> timeit: {call:>50} {time:16.6f} seconds.".format(**t)

timeit.show = show


def average():
    function_times = {}
    for t in timeit.times:
        if t['function'] not in function_times:
            function_times[t['function']] = []
        function_times[t['function']].append(t['time'])
    for k, times in function_times.iteritems():
        average = fsum(times) / len(times)
        print "> timeit: {:>50} {:16.6f} seconds.".format(k, average)


timeit.average = average


def sizeof_fmt(num):
    """
    Returns a human readable string representation of `num` bytes.
    """
    for x in ['bytes', 'KB', 'MB', 'GB']:
        if num < 1024.0 and num > -1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


@timeit
def test(*args, **kwargs):
    time.sleep(0.6)

if __name__ == '__main__':
    test("Hello World!", test=True, a=False, b=u'VALUE')
    test()
    timeit.show(False)
    timeit.average()

    print sizeof_fmt(999**9)
