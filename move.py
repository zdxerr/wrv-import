# -*- coding: utf-8 -*-

import os
import shutil

import find_results
import test_result_parser

WRV_IMPORT_PATH = r'I:\WRV_Import_CRTI-BTP'


def get_id():
    id = 0
    path = os.path.join(WRV_IMPORT_PATH, '_done')
    for filename in os.listdir(path):
        if os.path.isdir(os.path.join(path, filename)):
            try:
                id = max(int(filename.split(' ', 1)[1]), id)
            except:
                pass
    return id

result_file_format = '''
Result = %s
Label = %s
end
'''


if __name__ == '__main__':
    result_path = r"R:\PE\Testdata\CRTI-Test\ImplSW_RLS_2013-A"
    last_id = get_id()
    for result_file_path in find_results.results(result_path, 'testbutler'):
        last_id += 1
        result_dir_path = os.path.dirname(result_file_path)
        print result_dir_path,
        result = 'Result %d' % (last_id)
        new_result_path = os.path.join(WRV_IMPORT_PATH, result)
        rel_path, l = os.path.split(result_dir_path[len(result_path)+1:])
        new_path = os.path.join(new_result_path, rel_path)
        print new_path
        shutil.copytree(result_dir_path, new_path)
        label = ' '.join(['ImplSW_RLS_2013-A', l])
        f = open(os.path.join(WRV_IMPORT_PATH, result + '.txt'), 'a')
        f.write(result_file_format % (new_result_path, label))
        f.close()
