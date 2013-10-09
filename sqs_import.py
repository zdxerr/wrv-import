# -*- coding: utf-8 -*-
"""
SQS-Database Importer.
"""

import os.path
import optparse
import itertools
from pprint import pprint

from utilities import find_results

from db import SQSDatabase

__version__ = '$Revision: $'

def import_result(db, result):
    ignore_tags = ('Res', 'RTIxxxMM', 'RTIFlexRay', 'ts_results', 'rti')
    label = db.label(result.label)

    paths = {}
    component_results = {}
    groups = {}
    group_results = {}
    test_cases = {}
    for s in result.sequences:
        path_str = '\\'.join(result.nodes + s.nodes)

        path = paths.get(path_str, db.path(result.nodes + s.nodes))
        paths[path_str] = path

        component_result = component_results[path] = (
            component_results.get(path) or
            db.component_result(path, label, executed_by="Regression Test",
                                os=result.os, pc=result.pc,
                                platform=result.platform))

        group_str = '\\'.join([path_str, s.group])
        group = groups[group_str] = (
            groups.get(group_str) or db.test_group(path, s.group))

        group_result = group_results[group] = (
            group_results.get(group) or
            db.test_group_result(group, component_result))

        test_case = test_cases[(group, s.name)] = (
            test_cases.get((group, s.name)) or
            db.test_case(group, s.name, description=s.comment))

        possible_results = {
            'Ok': 0,
            'Fail': 1,
            'Not Executed': -1,
            'Excluded': -1
        }
        test_case_result = db.test_case_result(
            component_result, group_result, test_case,
            possible_results[s.state],
            start_time=s.start, stop_time=s.end)

        for n, l in enumerate(s.log, 0):
            test_step = db.test_step(test_case, l['name'])
            db.test_step_result(
                component_result, group, test_case, test_case_result,
                test_step,
                l['status'], timestamp=l.get('timestamp') or s.start,
                text=l['message'])

if __name__ == '__main__':
    parser = optparse.OptionParser(usage='usage: %prog [options] <path>',
                                   description=__doc__,
                                   version=__version__)

    parser.add_option('-c', '--clear', dest='clear', default=False,
                      action='store_true', help="Clear database contents")
    parser.add_option('-l', '--list', dest='list', default=False,
                      action='store_true', help="List result files in <path>")

    options, remainder = parser.parse_args()

    login = ('VM-DB-DEV1\SQL2008', 'SQS_CRTI', 'cvb7bwwm', 'SQS_CRTI_BTP')
    db = SQSDatabase(*login)

    if options.clear:
        db.clear()

    for path in remainder:
        for result in find_results(path):
            print result.path
            if not options.list:
                import_result(db, result)
