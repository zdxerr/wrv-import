# -*- coding: utf-8 -*-
"""
Remove all contents from a SQS-Databes and create new path roots.
"""

import pymssql

class SQSDatabase:
    tables = [
        'component',
        'files',
        'images',
        'integration_label',
        'LabelIDNames',
        'TestCases',
        'TestCasesName',
        'TestCasesReferenceLinks',
        'TestCasesResultDBFiles',
        'TestCasesResultDescription',
        'TestCasesResultFiles',
        'TestCasesResults',
        'TestCasesResultsReferenceLinks',
        'TestComponentsResults',
        'TestGroups',
        'TestGroupsResults',
        'TestSteps',
        'TestStepsResults',
        'TestStepsResultsPRs',
        'TLIDName',
        'tmp',
        'Updatepath',
        'user_lastview',
        'user_message',
        # keep user settings for now
        # 'user_settings',
    ]
    def __init__(self, host, user, password, database):
        print "Connecting to %s:" % (host, ),
        try:
            self.c = pymssql.connect(host=host, user=user, password=password,
                                     database=database)
        except Exception, exc:
            print "FAILED", exc
        else:
            print "OK"

    def __del__(self):
        self.c.close()
        print "Connection closed."

    def clear(self):
        tables = list(self.tables)
        cur = self.c.cursor()

        while tables:
            table = tables.pop(0)
            print "Trying to delete contents of table %r:" % (table, ),
            try:
                cur.execute('DELETE FROM '+ table)
                self.c.commit()
            except Exception, exc:
                print "FAILED", exc
                tables.append(table)
            else:
                print "OK"

    def __insert_node(self, path, level=0, parrent=None, tlid1=0, tlid2=0):
        cur = self.c.cursor()
        path_str = '/'.join(path[:level + 1])
        if level == 0:
            cur.execute('SELECT max(prtcid) FROM TLIDName')
            last_id = cur.fetchone()[0]

            if not last_id:
                last_id = 0
            id = last_id + 0x100
        elif level < 2:
            cur.execute('SELECT max(prtcid) FROM TLIDName WHERE ' \
                        'prtcid BETWEEN %d AND %d + 255',
                        (parrent, parrent))
            last_id = cur.fetchone()[0]
            id = last_id + 1
        elif level < 6:
            shift_chld = (5 - level) * 8    # used to get child id
            shift_prnt = shift_chld + 8     # used to get parent id

            mask = 0xffffffff >> shift_prnt
            mask = mask << shift_prnt

            rangeMin = tlid1 & mask
            rangeMax = rangeMin
            rangeMax += (0xff << shift_chld)

            cur.execute('SELECT max(tlid1) FROM TLIDName WHERE prtcid = %d ' \
                        'AND tlid1 >= %d AND tlid1 <= %d',
                        (parrent, rangeMin, rangeMax))
            last_tlid1 = cur.fetchone()[0]

            if (last_tlid1 >> shift_chld) & 0xff == 255:
                # range of possible nodes is full :(
                raise Exception

            id = parrent
            tlid1 = last_tlid1 >> shift_chld
            tlid1 += 1
            tlid1 = tlid1 << shift_chld
        elif level < 10:
            shift_chld = (9 - level) * 8    # used to get child id
            shift_prnt = shift_chld + 8     # used to get parent id

            mask = 0xffffffff >> shift_prnt
            mask = mask << shift_prnt

            rangeMin = tlid2 & mask
            rangeMax = rangeMin
            rangeMax += (0xff << shift_chld)

            cur.execute('SELECT max(tlid2) FROM TLIDName WHERE prtcid = %d ' \
                        'AND tlid1 = %d AND tlid2 >= %d AND tlid2 <= %d',
                (parrent, tlid1, rangeMin, rangeMax))
            last_tlid2 = cur.fetchone()[0]

            if (last_tlid2 >> shift_chld) & 0xff == 255:
                # range of possible nodes is full :(
                raise Exception
            id = parrent
            tlid2 = last_tlid2 >> shift_chld
            tlid2 += 1
            tlid2 = tlid2 << shift_chld
        else:
            raise ValueError("path too long", path_str)


        print "Trying to add %r:" % (path_str, ),
        q = '''INSERT INTO TLIDName (prtcid, tlid1, tlid2, leaf, path, name,
                                     UpdateTime, Status)
               VALUES (%d, %d, %d, 0, %s, %s, %s, %s)'''
        try:
            cur.execute(q, (id, tlid1, tlid2, path_str,
                        path[level], '', ''))
            self.c.commit()

        except Exception, exc:
            print "FAILED", exc
        else:
            print "OK"
            cur.execute('SELECT prtcid, tlid1, tlid2 FROM TLIDName ' \
                        'WHERE path = %s', ('/'.join(path[:level + 1]), ))
            return cur.fetchone()

    def insert_path(self, path):
        if isinstance(path, basestring):
            path = path.strip('/').split('/')
        if not isinstance(path, list):
            raise TypeError

        parrent, tlid1, tlid2 = None, 0, 0
        for level, node in enumerate(path):
            parrent, tlid1, tlid2 = self.__insert_node(path, level, parrent,
                                                       tlid1, tlid2)
        pass

if __name__ == '__main__':
    db = SQSDatabase('VM-DB-DEV1\SQL2008', 'SQS_CRTI', 'cvb7bwwm', 'SQS_CRTI_BTP')
    db.clear()
    db.insert_path('RTIxxxMM/subfolder/second/third/fourth/fives/six/seven/ei')
