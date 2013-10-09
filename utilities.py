# -*- coding: utf-8 -*-

import os
import time
from math import fsum

from test_result_parser import RTITEResult, CRTITAResult


RESULT_FILE_TYPES = {
    'ts_results': RTITEResult,
    'crtita_res': CRTITAResult,
    # 'testbutler': "maintest.log.xml"
}
IGNORED_FOLDERS = ["TestReport", "HtmlPages", "KwSearchPages", "Icons"]


def find_results(result_path):
    """Return all results in a certain path."""
    if os.path.isdir(result_path):
        for path, folders, files in os.walk(result_path):
            # remove ignored folders from list of folders
            folders[:] = [f for f in folders if f not in IGNORED_FOLDERS]

            for f in files:
                f_short = f[:10].lower()
                if f_short in RESULT_FILE_TYPES:
                    yield RESULT_FILE_TYPES[f_short](os.path.join(path, f))

    elif os.path.isfile(result_path):
        f_short = os.path.basename(result_path)[:10].lower()
        if f_short in RESULT_FILE_TYPES:
            yield RESULT_FILE_TYPES[f_short](result_path)


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

        try:
            timeit.times[fn.__name__] += end - start
            timeit.times[fn.__name__] /= 2
        except:
            timeit.times[fn.__name__] = end - start

        if timeit.verbose:
            print "> timeit: {:>50} {:16.6f} seconds.".format(c, end - start)

        if result:
            return result
    return wrapped

timeit.verbose = False
timeit.times = {}


def average():
    for fn, time in timeit.times.iteritems():
        print "> timeit: {:>50} {:16.6f} seconds.".format(fn, time)


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
