# -*- coding: utf-8 -*-

import os

RESULT_FILES = {
    'rtite': "ts_results",
    'crtita': "crtita_result",
    'testbutler': "maintest.log.xml"
}
IGNORED_FOLDERS = ["TestReport", "HtmlPages", "KwSearchPages", "Icons"]


def results(result_path, result_type=None, ignored_folders=[]):
    ignored_folders += IGNORED_FOLDERS

    if result_type:
        result_files = [RESULT_FILES.get(result_type)]
    else:
        result_files = RESULT_FILES.values()

    for path, folders, files in os.walk(result_path):
        # remove ignored folders from list of folders
        folders[:] = [f for f in folders if f not in ignored_folders]

        # look for test result files
        for f in files:
            if any([result in f.lower() for result in result_files]):
                yield os.path.join(path, f)

if __name__ == '__main__':
    result_path = r"R:\PE\Testdata\CRTI-Test\ImplSW_RLS_2013-A"
    for result in results(result_path, 'crtita'):
        print result
