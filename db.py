# -*- coding: utf-8 -*-
"""
Remove all contents from a SQS-Databes and create new path roots.
"""

from datetime import datetime

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
        """
        Delete all entries from all tables, except for the user_settings.
        """
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

    def __node_set_leaf(self, cur, path_str, leaf=True):
        """
        Enable/Disable leaf property of a node.
        """
        cur.execute('UPDATE TLIDName SET leaf=%d WHERE path = %s',
                    (1 if leaf else 0, path_str, ))
        self.c.commit()

    def __node_get(self, cur, path_str):
        """
        Lookup node with the specified path.
        """
        cur.execute('SELECT TOP 1 prtcid, tlid1, tlid2 FROM TLIDName ' \
                    'WHERE path = %s', (path_str, ))
        return cur.fetchone()

    def __node_insert(self, cur, path, level=0, parent=None, tlid1=0, tlid2=0):
        """
        Insert a single node from path at <level> using the given parent ids.
        """
        path_str = '/'.join(path[:level + 1])

        # check if path until level already exists
        node = self.__node_get(cur, path_str)
        if node:
            # update to leaf if necessary
            if len(path) - 1 == level:
                self.__node_set_leaf(cur, path_str)
            return node

        if level == 0:
            cur.execute('SELECT max(prtcid) FROM TLIDName')
            last_id = cur.fetchone()[0] or 0
            id = ((last_id >> 8) + 1) << 8

        elif level < 2:
            cur.execute('SELECT max(prtcid) FROM TLIDName WHERE ' \
                        'prtcid BETWEEN %d AND %d + 255',
                        (parent, parent))
            last_id = cur.fetchone()[0]
            id = last_id + 1

        elif level < 6:
            shift_chld = (5 - level) * 8 # used to get child id
            shift_prnt = shift_chld + 8 # used to get parent id

            mask = (0xffffffff >> shift_prnt) << shift_prnt

            range_min = tlid1 & mask
            range_max = range_min + (0xff << shift_chld)

            cur.execute('SELECT max(tlid1) FROM TLIDName WHERE prtcid = %d ' \
                        'AND tlid1 >= %d AND tlid1 <= %d',
                        (parent, range_min, range_max))
            last_tlid1 = cur.fetchone()[0]

            if (last_tlid1 >> shift_chld) & 0xff == 255:
                # range of possible nodes is full :(
                raise Exception

            id = parent
            tlid1 = ((last_tlid1 >> shift_chld) + 1) << shift_chld

        elif level < 10:
            shift_chld = (9 - level) * 8    # used to get child id
            shift_prnt = shift_chld + 8     # used to get parent id

            mask = (0xffffffff >> shift_prnt) << shift_prnt

            range_min = tlid2 & mask
            range_max = range_min + (0xff << shift_chld)

            cur.execute('SELECT max(tlid2) FROM TLIDName WHERE prtcid = %d ' \
                        'AND tlid1 = %d AND tlid2 >= %d AND tlid2 <= %d',
                        (parent, tlid1, range_min, range_max))
            last_tlid2 = cur.fetchone()[0]

            if (last_tlid2 >> shift_chld) & 0xff == 255:
                # range of possible nodes is full :(
                raise Exception

            id = parent
            tlid2 = ((last_tlid2 >> shift_chld) + 1) << shift_chld

        else:
            raise ValueError("path too long", path_str)

        q = 'INSERT INTO TLIDName (prtcid, tlid1, tlid2, leaf, path, name, ' \
            'UpdateTime, Status) VALUES (%d, %d, %d, %d, %s, %s, %s, %s)'

        cur.execute(q, (id, tlid1, tlid2, 1 if len(path) - 1 == level else 0,
                    path_str, path[level], '', ''))
        self.c.commit()

        return self.__node_get(cur, path_str)

    def path(self, path):
        if isinstance(path, basestring):
            path = path.strip('/').split('/')
        if not isinstance(path, list):
            raise TypeError

        cur = self.c.cursor()
        parent, tlid1, tlid2 = None, 0, 0
        for level, node in enumerate(path):
            parent, tlid1, tlid2 = self.__node_insert(cur, path, level, parent,
                                                      tlid1, tlid2)
        self.parrent, self.tlid1, self.tlid2 = parent, tlid1, tlid2

    def __label_get(self, cur, label):
        cur.execute('SELECT labelid FROM LabelIDNames WHERE sslabel=%s',
                    (label, ))
        r = cur.fetchone()
        return r[0] if r else None

    def label(self, label, timestamp=datetime.now()):
        cur = self.c.cursor()

        label_id = self.__label_get(cur, label)
        if label_id:
            return label_id

        cur.execute('SELECT max(labelid) FROM LabelIDNames')
        label_id = (cur.fetchone()[0] or 0) + 1

        q = 'INSERT INTO LabelIDNames (labelid, sslabel, display_label, ' \
            'Date, OfficialLabel) VALUES (%d, %s, %s, %s, 0);'

        cur.execute(q, (label_id, label, label, timestamp))
        self.c.commit()
        self.label_id = label_id
        return label_id

    def components_result(self):
        cur = self.c.cursor()

        cur.execute('SELECT max(tcomprid) FROM TestComponentsResults')
        tcompr_id = (cur.fetchone()[0] or 0) + 1

        q = '''INSERT INTO TestComponentsResults
               (prtcid, tlid1, tlid2, labelid, os, tcomprid,
                tg_ok, cor_tg_ok, tg_fail, cor_tg_fail, tg_crash, cor_tg_crash,
                tg_no, cor_tg_no,
                tc_ok, cor_tc_ok, tc_fail, cor_tc_fail, tc_crash, cor_tc_crash,
                tc_no, cor_tc_no,
                ts_ok, cor_ts_ok, ts_fail, cor_ts_fail, ts_crash, cor_ts_crash,
                ts_no, cor_ts_no,
                comment, rd_comment, date, ShortTestPCDesc, OSWhileTestExec,
                WhoExecTest, TestCandidateVersion, TestCandidateBuildType,
                TestCandidateBuildNumber, TestCandidateSpecialBuild,
                TestCandidateDate, PlatformWhileTestExec, InterfaceToPlatform,
                RemarksToTestExec, StatusOfTestExec, state, invisible,
                cor_ts_exception, cor_ts_blocked, cor_tc_exception,
                cor_tc_blocked, cor_tg_exception, cor_tg_blocked) VALUES
               (%d, %d, %d, %d, %s, %d,
                1, 2, 3, 4, 5, 6, 7, 8,
                1, 2, 3, 4, 5, 6, 7, 8,
                1, 2, 3, 4, 5, 6, 7, 8,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, 0,
                0, 0, 0, 0, 0, 0);'''

        cur.execute(q, (self.parrent, self.tlid1, self.tlid2, self.label_id,
                        "OS", tcompr_id,
                        "kommentar", "kommentar rd",
                        # "October 19, 1962 4:35:47 PM",
                        "100000",
                        "TESTPC", "OSWhileTestExec", "CHristophS",
                        "TestCandidateVersion", "TestCandidateBuildType",
                        "TestCandidateBuildNumber",
                        "TestCandidateSpecialBuild",
                        "October 19, 1962", "PlatformWhileTestExec",
                        "InterfaceToPlatform", "RemarksToTestExec", "0", "0"

                        ))
        self.c.commit()
        return tcompr_id



if __name__ == '__main__':
    data = ('VM-DB-DEV1\SQL2008', 'SQS_CRTI', 'cvb7bwwm', 'SQS_CRTI_BTP')
    db = SQSDatabase(*data)
    db.clear()
    db.path('RTIxxxMM/subfolder/second/third/fourth/fives/six/seven/ei')
    print db.label("HELLOTEST_17_04_2013")
    print db.label("HELLOTEST_17_04_2013")
    print db.label("HELLOTEST_17_04_2013")
    print db.components_result()
