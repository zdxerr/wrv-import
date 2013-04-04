import os
import shutil
from pprint import pprint

import crtita_result

import _Configuration

import SQS_TR2DB
import SQSDB

WORKING_FOLDER = 'E:\\wrv-work'

if os.path.isdir(WORKING_FOLDER):
    shutil.rmtree(WORKING_FOLDER)
os.makedirs(WORKING_FOLDER)


def insert_result(result_file):
    db = SQSDB.SQS2SQL(None)
    db.OpenDB(True)

    # SQS_TR2DB.ImportData(db, ts_root, folderpath, _Configuration.prePath +
    #                      prodDBEntry)

    result = crtita_result.CRTITAResultFileClass(result_file)
    result.Load()
    for key in result.GetResult():
        print key

    db.CloseDB()


def main():
    import find_results
    result_path = r"R:\PE\Testdata\CRTI-Test\ImplSW_RLS_2013-A"
    for result_file in find_results.results(result_path, 'crtita'):
        print "Found result at %r." % (result_file, )

        # copy result file
        relpath = os.path.relpath(result_file, result_path)
        path, filename = os.path.split(relpath)
        new_path = os.path.join(WORKING_FOLDER, path)
        os.makedirs(new_path)
        result_file_copy = os.path.join(new_path, filename)
        shutil.copyfile(result_file, result_file_copy)

        insert_result(result_file_copy)
        break

if __name__ == '__main__':
    main()
