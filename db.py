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

    def insert_root(self, name):
        cur = self.c.cursor()
        cur.execute('SELECT max(prtcid) FROM TLIDName')
        last_id = cur.fetchone()[0]

        if not last_id:
            last_id = 0
        id = last_id + 0x100
        print "Trying to add root %r:" % (name, ),
        q = '''INSERT INTO TLIDName (prtcid, tlid1, tlid2, leaf, path, name,
                                     UpdateTime, Status)
               VALUES (%d, 0, 0, 0, %s, %s, %s, %s)'''
        try:
            cur.execute(q, (id, r'/%s/' % (name), name, '', ''))
            self.c.commit()
        except Exception, exc:
            print "FAILED", exc
        else:
            print "OK"

if __name__ == '__main__':
    db = SQSDatabase('VM-DB-DEV1\SQL2008', 'SQS_CRTI', 'cvb7bwwm', 'SQS_CRTI_BTP')
    db.clear()
    for r in ('RTIxxxMM', 'RTIFlexRay', ):
        db.insert_root(r)
