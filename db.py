# -*- coding: utf-8 -*-
"""
Basic functions to create and remove data from the SQSDatabase, which is used 
by the Web-Result-Viewer.
"""

from datetime import datetime
import time
import logging

import pymssql


class SQSDatabase:
    """Represent the whole database and group operations on it."""

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
        self.con = pymssql.connect(host=host, user=user, password=password,
                                     database=database)


    def __del__(self):
        self.con.close()
        print "Connection closed."

    def clear(self):
        """
        Delete all entries from all tables, except for the user_settings.
        """
        tables = list(self.tables)
        cur = self.con.cursor()

        while tables:
            table = tables.pop(0)
            print "Trying to delete contents of table %r:" % (table, ),
            try:
                # cur.execute('ALTER TABLE ' + table + ' NOCHECK CONSTRAINT ALL')
                # cur.execute('ALTER TABLE ' + table + ' DISABLE TRIGGER ALL')
                cur.execute('DELETE '+ table)
                # cur.execute('TRUNCATE TABLE ' + table)
                self.con.commit()
            except Exception, exc:
                print "FAILED", exc
                try:
                    print "Trying to truncate contents of table %r:" % (table, ),
                    cur.execute('TRUNCATE TABLE ' + table)
                except Exception, exc:
                    print "FAILED", exc
                    tables.append(table)
                else:
                    print "OK"
            else:
                print "OK"
            # finally:
                # cur.execute('ALTER TABLE ' + table + ' CHECK CONSTRAINT ALL')
                # cur.execute('ALTER TABLE ' + table + ' ENABLE TRIGGER ALL')

    def __node_set_leaf(self, cur, path_str, leaf=True):
        """
        Enable/Disable leaf property of a node.
        """
        cur.execute('UPDATE TLIDName SET leaf=%d WHERE path = %s',
                    (1 if leaf else 0, path_str, ))
        self.con.commit()

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
        self.con.commit()

        return self.__node_get(cur, path_str)

    def path(self, path):
        """
        Insert a path, create all nodes that do not exist and set leaf property
        of the last node.
        """
        if isinstance(path, basestring):
            path = path.strip('/').split('/')
        if not isinstance(path, list):
            raise TypeError

        cur = self.con.cursor()
        parent, tlid1, tlid2 = None, 0, 0
        for level, node in enumerate(path):
            parent, tlid1, tlid2 = self.__node_insert(cur, path, level, parent,
                                                      tlid1, tlid2)
        self.parrent, self.tlid1, self.tlid2 = parent, tlid1, tlid2
        return self.parrent, self.tlid1, self.tlid2

    def __label_get(self, cur, label):
        cur.execute('SELECT labelid FROM LabelIDNames WHERE sslabel=%s',
                    (label, ))
        r = cur.fetchone()
        return r[0] if r else None

    def label(self, label, timestamp=datetime.now()):
        """
        Create a label if it does not exist and return its id.
        """
        cur = self.con.cursor()
        q = 'INSERT INTO LabelIDNames (labelid, sslabel, display_label, ' \
            'Date, OfficialLabel) OUTPUT INSERTED.labelid ' \
            'SELECT ISNULL(MAX(labelid), 0) + 1, %s, %s, %s, 0 '\
            'FROM LabelIDNames'

        self.label_id = self.__label_get(cur, label)
        if not self.label_id:
            cur.execute(q, (label, label, str(timestamp)))
            self.label_id = cur.fetchone()[0]
            self.con.commit()
        return self.label_id

    def component_result(self, path, label, timestamp=datetime.now(),
                         executed_by="", os="Unknown", pc="Unknown",
                         candidate=["Unknown", "Unknown", "Unknown", "Unknown",
                         "Unknown"], platform="Unknown", interface="Unknown",
                         remarks="None"):
        """
        Create a new component result.
        """
        cur = self.con.cursor()

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
                0, 0, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, 0, 0,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, 0,
                0, 0, 0, 0, 0, 0 FROM TestComponentsResults'''

        # print time.mktime(timestamp.timetuple())

        params = [path[0], path[1], path[2], label,
                  os[0], "", "",
                  # "October 19, 1962 4:35:47 PM",
                  time.mktime(timestamp.timetuple()),
                  pc, os, executed_by] + \
                  candidate + \
                  [platform, interface, remarks, "0", "0"]

        cur.execute(q, tuple(params))
        tcompr_id = cur.fetchone()[0]
        self.con.commit()
        return tcompr_id

    def __test_group_get(self, cur, path, name):
        cur.execute('SELECT tgid FROM TestGroups WHERE prtcid=%d AND ' \
                    'tlid1=%d AND tlid2=%d AND name=%s',
                    (path[0], path[1], path[2], name))
        r = cur.fetchone()
        return r[0] if r else None

    def test_group(self, path, name):
        cur = self.con.cursor()

        q = '''INSERT INTO TestGroups (prtcid, tlid1, tlid2, tgid, name)
            OUTPUT INSERTED.tgid
            SELECT %d, %d, %d, ISNULL(MAX(tgid), 0) + 1, %s FROM TestGroups'''

        tg_id = self.__test_group_get(cur, path, name)
        if not tg_id:
            cur.execute(q, (path[0], path[1], path[2], name))
            tg_id = cur.fetchone()[0]
            self.con.commit()
        return tg_id

    def __test_group_result_get(self, cur, group, component_result):
        cur.execute('SELECT tgrid FROM TestGroupsResults WHERE tgid=%d AND ' \
                    'tcomprid=%d', (group, component_result))
        r = cur.fetchone()
        return r[0] if r else None


    def test_group_result(self, group, component_result):
        cur = self.con.cursor()
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

        tgr_id = self.__test_group_result_get(cur, group, component_result)
        if not tgr_id:
            cur.execute(q, (group, component_result, 0, 0,
                            0, 0, 0, 0, 0, 0, 0, 0,
                            0, 0, 0, 0, 0, 0, 0, 0,
                            "", "", "",
                            0, 0, 0, 0))
            tgr_id = cur.fetchone()[0]
            self.con.commit()
        return tgr_id

    def __test_case_name_get(self, cur, group, name):
        cur.execute('SELECT tcnid FROM TestCasesName WHERE tgid=%d AND ' \
                    'name=%s', (group, name))
        r = cur.fetchone()
        return r[0] if r else None

    def __test_case_get(self, cur, tcn_id, version):
        cur.execute('SELECT tcid FROM TestCases WHERE tcnid=%s AND ' \
                    'version=%s', (tcn_id, version))
        r = cur.fetchone()
        return r[0] if r else None

    def test_case(self, group, name, timestamp=datetime.now(), version="0",
                  author="Unknown", description=""):
        cur = self.con.cursor()
        q = '''INSERT INTO TestCasesName (tgid, tcnid, name)
               OUTPUT INSERTED.tcnid
               SELECT %d, ISNULL(MAX(tcnid), 0) + 1, %s FROM TestCasesName'''

        tcn_id = self.__test_case_name_get(cur, group, name)
        if not tcn_id:
            cur.execute(q, (group, name))
            tcn_id = cur.fetchone()[0]

        q = '''INSERT INTO TestCases (tcnid, tcid, date, version, ssver, name,
                author, testDescription) OUTPUT INSERTED.tcid
               SELECT %d, ISNULL(MAX(tcid), 0) + 1, %s, %s, %d, %s, %s, %d
               FROM TestCases'''

        tc_id = self.__test_case_get(cur, tcn_id, version)
        if not tc_id:
            cur.execute(q, (tcn_id, timestamp, version, 0, name, author,
                            description))
            tc_id = cur.fetchone()[0]

        self.con.commit()
        return tcn_id, tc_id

    def test_case_result(self, component_result, group_result, test_case,
                         result, start_time="", stop_time="", os=""):
        cur = self.con.cursor()

        logging.debug("Create test case result (%s).",
                      ', '.join(map(str, (component_result, group_result,
                                          test_case, result,))))

        cur.execute('SELECT name, author, date, version, ssver ' \
                    'FROM TestCases WHERE tcid=%d', (test_case[1], ))
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

        cur.execute(q, (test_case[0], ssver, group_result, os,
                        name, author, changedate, version,
                        start_time, stop_time,
                        result, result,
                        0, 0, 0, 0, 0, 0, 0, 0,
                        "", "", "", 0, 0))
        tcr_id = cur.fetchone()[0]

        # not visible in the wrv?
        q = '''INSERT INTO TestCasesResultDescription
               (tcrid, filePath, name, author, changedate, version,
                time, runTime, preparation, totalTime,
                software, hardware, descriptionValue) VALUES
               (%d, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''

        cur.execute(q, (tcr_id, "", "", "", "", "",
                        "", "", "", "",
                        "", "", ""))

        result_colums = {0: 'tc_ok', 1: 'tc_fail', -1: 'tc_no'}
        q = '''UPDATE TestGroupsResults SET {c} = {c} + 1, cor_{c} = cor_{c} + 1
               WHERE tgrid=%d'''.format(c=result_colums[result])
        cur.execute(q, group_result)

        result_colums = {0: 'tc_ok', 1: 'tc_fail', -1: 'tc_no'}
        q = '''UPDATE TestComponentsResults SET {c} = {c} + 1, cor_{c} = cor_{c} + 1
               WHERE tcomprid=%d'''.format(c=result_colums[result])
        cur.execute(q, component_result)

        self.con.commit()
        return tcr_id

    def test_case_result_file(self, test_case_result, name, content):
        cur = self.con.cursor()

        q = '''INSERT INTO TestCasesResultDBFiles
               (fileId, fileType, fileSize, fileNameOrig, fileContent,
                fileContentBig, tcrid)
               OUTPUT INSERTED.fileID
               SELECT ISNULL(MAX(fileId), 0) + 1, %s, %d, %s, %s, %d, %d
               FROM TestCasesResultDBFiles'''

        cur.execute(q, ('txt', len(content), name, content, 0,
                        test_case_result))
        self.tcrf_id = cur.fetchone()[0]
        self.con.commit()

    def test_step(self, test_case, title):
        cur = self.con.cursor()

        q = '''INSERT INTO TestSteps
               (pos, tcid, type, image, logText,
                id, title, stopOnFail, value, wait)
               OUTPUT INSERTED.pos
               SELECT ISNULL(MAX(pos), 0) + 1, %d, %s, %s, %s,
                STR(ISNULL(MAX(pos), 0) + 1), %s, %s, %s,
                %s FROM TestSteps WHERE tcid=%d'''

        cur.execute(q, (test_case[1], "", "", "",
                        title[:254], "", "", "", test_case[1]))
        ts_pos = cur.fetchone()[0]
        self.con.commit()
        return ts_pos

    def test_step_result(self, component_result, group, test_case,
                         test_case_result, test_step,
                         result, timestamp=datetime.now(), text=""):
        cur = self.con.cursor()

        logging.debug("Create test step result (%s).",
                      ', '.join(map(str, (component_result, group, test_case,
                                 test_case_result, test_step, result))))

        q = '''INSERT INTO TestStepsResults
               (pos, tcrid, tcid, ts_pos, logText, result, cor_result,
                id, time, comment, rd_comment, tc_comment, g_comment,
                traceback, state, stepValue, type) VALUES
               (%d, %d, %d, %d, %s, %d, %d,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s)'''

        cur.execute(q, (test_step, test_case_result, test_case[1],
                        str(test_step), text, result, result, str(test_step),
                        timestamp, "", "", "", "", "", "", "", ""))

        result_colums = {0: 'ts_ok', 1: 'ts_fail', -1: 'ts_no'}
        q = '''UPDATE TestCasesResults SET {c} = {c} + 1, cor_{c} = cor_{c} + 1
               WHERE tcrid=%d'''.format(c=result_colums[result])
        cur.execute(q, test_case_result)

        q = '''UPDATE TestGroupsResults SET {c} = {c} + 1, cor_{c} = cor_{c} + 1
               WHERE tgrid=%d'''.format(c=result_colums[result])
        cur.execute(q, group)

        q = '''UPDATE TestComponentsResults SET {c} = {c} + 1, cor_{c} = cor_{c} + 1
               WHERE tcomprid=%d'''.format(c=result_colums[result])
        cur.execute(q, component_result)

        self.con.commit()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    data = ('VM-DB-DEV1\SQL2008', 'SQS_CRTI', 'cvb7bwwm', 'SQS_CRTI_BTP')
    db = SQSDatabase(*data)
    db.clear()
    path = db.path('RTIxxxMM/subfolder/second/third/fourth/fives/six/seven/ei')
    label = db.label("HELLOTEST_17_04_2013")
    # print db.label("HELLOTEST_17_04_2013")
    # print db.label("HELLOTEST_17_04_2013")
    component_result = db.component_result(path, label)
    group = db.test_group(path, 'YOYOYO')
    group_result = db.test_group_result(group, component_result)
    test_case = db.test_case(group, 'my tc', author='me')
    tcr = db.test_case_result(component_result, group_result, test_case, 0)
    ts = db.test_step(test_case, "my test step!")
    tsr = db.test_step_result(component_result, group, test_case, tcr, ts, 0,
                              text="WHAT?")

    exit()

    from test_result_parser import RTITEResult
    import find_results
    result_path = 'R:\\PE\\Testdata\\CRTI-Test\\ImplSW_RLS_2013-A\\RTIxxxMM' \
                  '\\Res\\INT17\\T_01\\ts_results_rti1005.mat'
    # result = RTITEResult(result_path)
    i = 0
    result_path = r"R:\PE\Testdata\CRTI-Test\ImplSW_RLS_2013-A\RTIFlexRay"
    for n, path in enumerate(find_results.results(result_path, 'rtite')):
        start = time.time()
        try:
            result = RTITEResult(path)
            print "{:8d} {!s:<140} {!s:>20}".format(n, result.path, result.start),

            ignore_tags = ('Res', 'RTIxxxMM', 'RTIFlexRay', 'ts_results', 'rti')

            tags = filter(lambda t: not t.startswith(ignore_tags), result.tags)
            tags = map(lambda t: t.replace(' ', '-'), tags)
            print
            print tags
            print [t for t in result.tags if t.lower().startswith('rti')]
            break
            db.label('_'.join(tags))
            db.path([t for t in result.tags if t.lower().startswith('rti')])

            db.component_result(executed_by="Regression Test", os=result.os,
                                pc=result.pc, platform=result.platform)

            for s in result.sequences:
                # print s
                # pprint(s.log)
                db.test_group(s.id.split('\\', 1)[0])
                db.test_group_result()
                db.test_case(s.id, description=s.comment)
                possible_results = {'Ok': 0, 'Fail': 1, 'Not Executed': -1,
                                    'Excluded': -1}
                db.test_case_result(possible_results[s.state],
                                    start_time=s.start, stop_time=s.end)

                for n, l in enumerate(s.log, 0):
                    db.test_step("Stage {}".format(n))
                    # db.test_case_result_file("Stage{}.txt".format(n), l)
                    # print s.teststage_failed,
                    db.test_step_result(1 if s.teststage_failed == n else 0,
                                        timestamp=s.start, text=l)

            state = 'OK'
        except Exception, exc:
            state = 'EXCEPT'
            print exc
        print "{!s:>10} {:10.2f} sec".format(state, time.time() - start)
        i += 1
        if i > 3:
            break

