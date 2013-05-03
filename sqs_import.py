# -*- coding: utf-8 -*-
"""
SQS-Database Importer.
"""

import os.path
import optparse
import itertools

from test_result_parser import RTITEResult, CRTITAResult

from db import SQSDatabase

__version__ = '$Revision: $'

RESULT_FILE_TYPES = {
    'ts_results': RTITEResult,
    'crtita_res': CRTITAResult,
    # 'testbutler': "maintest.log.xml"
}
IGNORED_FOLDERS = ["TestReport", "HtmlPages", "KwSearchPages", "Icons"]


def find_results(result_path):
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


def import_result(db, result):
    ignore_tags = ('Res', 'RTIxxxMM', 'RTIFlexRay', 'ts_results', 'rti')
    db.label(result.label)
    db.path(result.nodes)
    db.component_result(executed_by="Regression Test", os=result.os,
                        pc=result.pc, platform=result.platform)

    for s in result.sequences:
        db.test_group(s.id.split('\\', 1)[0])
        db.test_group_result()
        db.test_case(s.id, description=s.comment)
        possible_results = {
            'Ok': 0,
            'Fail': 1,
            'Not Executed': -1,
            'Excluded': -1
        }
        db.test_case_result(possible_results[s.state],
                            start_time=s.start, stop_time=s.end)
        for n, l in enumerate(s.log, 0):
            db.test_step(l['name'])
            db.test_step_result(
                l['status'], timestamp=l.get('timestamp') or s.start,
                text=l['message'])
    # db.label('_'.join(tags))
    # db.path([t for t in result.tags if t.lower().startswith(('rti', 'crtita'))])
    # db.component_result(executed_by="Regression Test", os=result.os,
    #                     pc=result.pc, platform=result.platform)
    # for s in result.sequences:
    #     db.test_group(s.id.split('\\', 1)[0])
    #     db.test_group_result()
    #     db.test_case(s.id, description=s.comment)
    #     possible_results = {'Ok': 0, 'Fail': 1, 'Not Executed': 2}
    #     db.test_case_result(possible_results[s.state], start_time=s.start,
    #                         stop_time=s.end)

    #     for n, l in enumerate(s.log, 0):
    #         db.test_step(l['name'])
    #         # db.test_case_result_file("Stage{}.txt".format(n), l)
    #         # print s.teststage_failed,
    #         db.test_step_result(l['status'], timestamp=s.start,
    #                             text=l['message'])


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
            if options.list:
                continue
            import_result(db, result)


    exit()

    result_path = r'R:\PE\Testdata\CRTI-Test\ImplSW_RLS_2013-A' \
                  r'\RTIFlexRay'
                  # r'\Res\INT13\T_01_RFT\TS4\Result' \
                  # r'\crtita_result'

    login = ('VM-DB-DEV1\SQL2008', 'SQS_CRTI', 'cvb7bwwm', 'SQS_CRTI_BTP')
    db = SQSDatabase(*login)
    db.clear()
    exit()

    i = 0
    for n, path in enumerate(find_results.results(result_path, 'crtita')):
        result = CRTITAResult(path)
        print result,

        ignore_tags = ('Res', 'RTIxxxMM', 'RTIFlexRay', 'ts_results', 'rti')

        tags = filter(lambda t: not t.startswith(ignore_tags), result.tags)
        tags = map(lambda t: t.replace(' ', '-'), tags)

        db.label('_'.join(tags))
        db.path([t for t in result.tags if t.lower().startswith(('rti', 'crtita'))])
        db.component_result(executed_by="Regression Test", os=result.os,
                            pc=result.pc, platform=result.platform)
        for s in result.sequences:
            db.test_group(s.id.split('\\', 1)[0])
            db.test_group_result()
            db.test_case(s.id, description=s.comment)
            possible_results = {'Ok': 0, 'Fail': 1, 'Not Executed': 2}
            db.test_case_result(possible_results[s.state], start_time=s.start,
                                stop_time=s.end)

            for n, l in enumerate(s.log, 0):
                db.test_step(l['name'])
                # db.test_case_result_file("Stage{}.txt".format(n), l)
                # print s.teststage_failed,
                db.test_step_result(l['status'], timestamp=s.start,
                                    text=l['message'])
        print "OK"
        i += 1
        if i > 3:
            break

