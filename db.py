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
        q = 'INSERT INTO LabelIDNames (labelid, sslabel, display_label, ' \
            'Date, OfficialLabel) OUTPUT INSERTED.labelid ' \
            'SELECT ISNULL(MAX(labelid), 0) + 1, %s, %s, %s, 0 '\
            'FROM LabelIDNames'

        self.label_id = self.__label_get(cur, label)
        if not self.label_id:
            cur.execute(q, (label, label, str(timestamp)))
            self.label_id = cur.fetchone()[0]
            self.c.commit()
        return self.label_id

    def components_result(self):
        cur = self.c.cursor()

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
                cor_tc_blocked, cor_tg_exception, cor_tg_blocked)
               OUTPUT INSERTED.tcomprid
               SELECT %d, %d, %d, %d, %s, ISNULL(MAX(tcomprid), 0) + 1,
                3, 4, 3, 4, 3, 4, 3, 4,
                3, 4, 3, 4, 3, 4, 3, 4,
                0, 0, 0, 0, 0, 0, 0, 0,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, 0,
                0, 0, 0, 0, 0, 0 FROM TestComponentsResults'''

        cur.execute(q, (self.parrent, self.tlid1, self.tlid2, self.label_id,
                        "OS",
                        "kommentar", "kommentar rd",
                        # "October 19, 1962 4:35:47 PM",
                        "100000",
                        "TESTPC", "OSWhileTestExec", "CHristophS",
                        "TestCandidateVersion", "TestCandidateBuildType",
                        "TestCandidateBuildNumber",
                        "TestCandidateSpecialBuild",
                        "October 19, 1962", "PlatformWhileTestExec",
                        "InterfaceToPlatform", "RemarksToTestExec", "0", "0"))
        self.tcompr_id = cur.fetchone()[0]
        self.c.commit()
        return self.tcompr_id

    def __test_group_get(self, cur, name):
        cur.execute('SELECT tgid FROM TestGroups WHERE prtcid=%d AND ' \
                    'tlid1=%d AND tlid2=%d AND name=%s',
                    (self.parrent, self.tlid1, self.tlid2, name))
        r = cur.fetchone()
        return r[0] if r else None

    def test_group(self, name):
        cur = self.c.cursor()

        q = '''INSERT INTO TestGroups (prtcid, tlid1, tlid2, tgid, name)
            OUTPUT INSERTED.tgid
            SELECT %d, %d, %d, ISNULL(MAX(tgid), 0) + 1, %s FROM TestGroups'''

        self.tg_id = self.__test_group_get(cur, name)
        if not self.tg_id:
            cur.execute('SELECT max(tgid) FROM TestGroups')
            tg_id = (cur.fetchone()[0] or 0) + 1

            cur.execute(q, (self.parrent, self.tlid1, self.tlid2, name))
            self.tg_id = cur.fetchone()[0]
            self.c.commit()
        return self.tg_id

    def __test_group_result_get(self, cur):
        cur.execute('SELECT tgrid FROM TestGroupsResults WHERE tgid=%d AND ' \
                    'tcomprid=%d', (self.tg_id, self.tcompr_id))
        r = cur.fetchone()
        return r[0] if r else None

    def test_group_result(self):
        cur = self.c.cursor()
        q = '''INSERT INTO TestGroupsResults
               (tgrid, tgid, tcomprid, tgResult, cor_tgResult,
                tc_ok, cor_tc_ok, tc_fail, cor_tc_fail, tc_crash, cor_tc_crash,
                tc_no, cor_tc_no,
                ts_ok, cor_ts_ok, ts_fail, cor_ts_fail, ts_crash, cor_ts_crash,
                ts_no, cor_ts_no,
                comment, rd_comment, state,
                cor_ts_exception, cor_ts_blocked, cor_tc_exception,
                cor_tc_blocked)
               OUTPUT INSERTED.tgrid
               SELECT ISNULL(MAX(tgrid), 0) + 1, %d, %d, %d, %d,
                %d, %d, %d, %d, %d, %d, %d, %d,
                %d, %d, %d, %d, %d, %d, %d, %d,
                %s, %s, %s,
                %d, %d, %d, %d FROM TestGroupsResults'''

        self.tgr_id = self.__test_group_result_get(cur)
        if not self.tgr_id:
            cur.execute(q, (self.tg_id, self.tcompr_id, 0, 0,
                            0, 0, 0, 0, 0, 0, 0, 0,
                            0, 0, 0, 0, 0, 0, 0, 0,
                            "comm", "cmmrd", "3",
                            0, 0, 0, 0))
            self.tgr_id = cur.fetchone()[0]
            self.c.commit()
        return self.tgr_id

    def __test_case_name_get(self, cur, name):
        cur.execute('SELECT tcnid FROM TestCasesName WHERE tgid=%d AND ' \
                    'name=%s', (self.tg_id, name))
        r = cur.fetchone()
        return r[0] if r else None

    def __test_case_get(self, cur, version):
        cur.execute('SELECT tcid FROM TestCases WHERE tcnid=%s AND ' \
                    'version=%s', (self.tcn_id, version))
        r = cur.fetchone()
        return r[0] if r else None

    def test_case(self, name, timestamp=datetime.now(), version="0",
                  author="Unknown", description=""):
        cur = self.c.cursor()
        q = '''INSERT INTO TestCasesName (tgid, tcnid, name)
               OUTPUT INSERTED.tcnid
               SELECT %d, ISNULL(MAX(tcnid), 0) + 1, %s FROM TestCasesName'''

        self.tcn_id = self.__test_case_name_get(cur, name)
        if not self.tcn_id:
            cur.execute(q, (self.tg_id, name))
            self.tcn_id = cur.fetchone()[0]

        q = '''INSERT INTO TestCases (tcnid, tcid, date, version, ssver, name,
                author, testDescription) OUTPUT INSERTED.tcid
               SELECT %d, ISNULL(MAX(tcid), 0) + 1, %s, %s, %d, %s, %s, %d
               FROM TestCases'''

        self.tc_id = self.__test_case_get(cur, version)
        if not self.tc_id:
            cur.execute(q, (self.tcn_id, timestamp, version, 0, name, author,
                            description))
            self.tc_id = cur.fetchone()[0]

        self.c.commit()
        return self.tcn_id, self.tc_id

    def test_case_result(self, result, start_time="", stop_time=""):
        cur = self.c.cursor()

        cur.execute('SELECT name, author, date, version, ssver ' \
                    'FROM TestCases WHERE tcid=%d', (self.tc_id, ))
        name, author, changedate, version, ssver = cur.fetchone()

        q = '''INSERT INTO TestCasesResults
               (tcnid, ssver, tgrid, tcrid, os,
                name, author, changedate, version, startTime, stopTime,
                tcResult, cor_tcResult,
                ts_ok, cor_ts_ok, ts_fail, cor_ts_fail, ts_crash, cor_ts_crash,
                ts_no, cor_ts_no,
                comment, rd_comment, state, cor_ts_exception, cor_ts_blocked)
               OUTPUT INSERTED.tcrid
               SELECT %d, %d, %d, ISNULL(MAX(tcrid), 0) + 1, %s,
                       %s, %s, %s, %s, %s, %s,
                       %d, %d,
                       %d, %d, %d, %d, %d, %d, %d, %d,
                       %s, %s, %s, %d, %d FROM TestCasesResults'''

        cur.execute(q, (self.tcn_id, ssver, self.tgr_id, "myOS",
                        name, author, changedate, version,
                        start_time, stop_time,
                        result, result,
                        0, 0, 0, 0, 0, 0, 0, 0,
                        "r comment", "r comment rd", "3", 0, 0))
        self.tcr_id = cur.fetchone()[0]

        # not visible in the wrv?
        q = '''INSERT INTO TestCasesResultDescription
               (tcrid, filePath, name, author, changedate, version,
                time, runTime, preparation, totalTime,
                software, hardware, descriptionValue) VALUES
               (%d, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''

        cur.execute(q, (self.tcr_id, "", "", "", "", "",
                        "", "", "", "",
                        "", "", ""))
        self.c.commit()
        return self.tcr_id

    def test_step(self, title):
        cur = self.c.cursor()

        q = '''INSERT INTO TestSteps
               (pos, tcid, type, image, logText,
                id, title, stopOnFail, value, wait)
               OUTPUT INSERTED.pos
               SELECT ISNULL(MAX(pos), 0) + 1, %d, %s, %s, %s,
                STR(ISNULL(MAX(pos), 0) + 1), %s, %s, %s,
                %s FROM TestSteps WHERE tcid=%d'''

        cur.execute(q, (self.tc_id, "type", "", "logTEXT",
                        title, "", "value", "", self.tc_id))
        self.ts_pos = cur.fetchone()[0]
        self.c.commit()
        return self.ts_pos

    def test_step_result(self, result, timestamp=datetime.now()):
        cur = self.c.cursor()

        q = '''INSERT INTO TestStepsResults
               (pos, tcrid, tcid, ts_pos, logText, result, cor_result,
                id, time, comment, rd_comment, tc_comment, g_comment,
                traceback, state, stepValue, type) VALUES
               (%d, %d, %d, %d, %s, %d, %d,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s)'''

        cur.execute(q, (self.ts_pos, self.tcr_id, self.tc_id, str(self.ts_pos),
                        "logtext", result, result, str(self.ts_pos),
                        timestamp, "comm", "rd_comment", "tc_comment",
                        "g_comment", "traceback", "state", "stepValue",
                        "type"))
        self.c.commit()
        return self.ts_pos


if __name__ == '__main__':
    data = ('VM-DB-DEV1\SQL2008', 'SQS_CRTI', 'cvb7bwwm', 'SQS_CRTI_BTP')
    db = SQSDatabase(*data)
    db.clear()
    db.path('RTIxxxMM/subfolder/second/third/fourth/fives/six/seven/ei')
    print db.label("HELLOTEST_17_04_2013")
    # print db.label("HELLOTEST_17_04_2013")
    # print db.label("HELLOTEST_17_04_2013")
    print db.components_result()
    print db.test_group('YOYOYO')
    print db.test_group_result()
    print db.test_case('my tc', author='me')
    print db.test_case_result(0)
    print db.test_step("my test step!")
    print db.test_step_result(0)
