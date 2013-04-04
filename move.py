# -*- coding: utf-8 -*-


import shutil

import find_results
import test_result_parser

WRV_IMPORT_PATH = r'I:\WRV_Import_CRTI-BTP'

if __name__ == '__main__':
    result_path = r"R:\PE\Testdata\CRTI-Test\ImplSW_RLS_2013-A"
    for result in find_results.results(result_path, 'testbutler'):
        r = test_result_parser.TestbutlerResult(result_path)
        print result
        print r
        # os.makedirs()
