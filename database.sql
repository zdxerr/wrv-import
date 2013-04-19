


INSERT INTO LabelIDNames (labelid, sslabel, display_label, Date, OfficialLabel) VALUES (1, "testsslabel", "test_displaylabel", "23/09/11 15:24:38", 0);

INSERT INTO TestComponentsResults (prtcid, tlid1, tlid2, labelid, os, tcomprid,
    tg_ok, cor_tg_ok, tg_fail, cor_tg_fail, tg_crash, cor_tg_crash, tg_no, cor_tg_no,
    tc_ok, cor_tc_ok, tc_fail, cor_tc_fail, tc_crash, cor_tc_crash, tc_no, cor_tc_no,
    ts_ok, cor_ts_ok, ts_fail, cor_ts_fail, ts_crash, cor_ts_crash, ts_no, cor_ts_no,
    comment, rd_comment, date, ShortTestPCDesc, OSWhileTestExec, WhoExecTest, TestCandidateVersion, TestCandidateBuildType, TestCandidateBuildNumber, TestCandidateSpecialBuild, TestCandidateDate, PlatformWhileTestExec, InterfaceToPlatform, RemarksToTestExec, StatusOfTestExec, state, invisible, cor_ts_exception, cor_ts_blocked, cor_tc_exception, cor_tc_blocked, cor_tg_exception, cor_tg_blocked) VALUES (256, 0, 0, 1, "WindowsXP", 1,
1, 2, 3, 4, 5, 6, 7, 8,
1, 2, 3, 4, 5, 6, 7, 8,
1, 2, 3, 4, 5, 6, 7, 8,
"Kommentar", "RDCOMMENT", "October 19, 1962 4:35:47 PM", "TESTPC", "OSWhileTestExec", "CHristophS", "TestCandidateVersion", "TestCandidateBuildType", "TestCandidateBuildNumber", "TestCandidateSpecialBuild", "October 19, 1962", "PlatformWhileTestExec", "InterfaceToPlatform", "RemarksToTestExec", "0", "0", 0,
0, 0, 0, 0, 0, 0
);



INSERT INTO TestGroups (prtcid, tlid1, tlid2, tgid, name) VALUES (256, 0, 0, 1, "mytest");
INSERT INTO TestGroupsResults (tgrid, tgid, tcomprid, tgResult, cor_tgResult,
    tc_ok, cor_tc_ok, tc_fail, cor_tc_fail, tc_crash, cor_tc_crash, tc_no, cor_tc_no,
    ts_ok, cor_ts_ok, ts_fail, cor_ts_fail, ts_crash, cor_ts_crash, ts_no, cor_ts_no,
    comment, rd_comment, state,
    cor_ts_exception, cor_ts_blocked, cor_tc_exception, cor_tc_blocked) VALUES (1, 1, 1, 0, 0,
    1, 2, 3, 4, 5, 6, 7, 8,
    1, 2, 3, 4, 5, 6, 7, 8,
    "my comment", "my rd comment", "0",
    5, 6, 7, 8
);

INSERT INTO TestCasesName (tgid, tcnid, name) VALUES (1, 1, "mytestcasename");
INSERT INTO TestCases (tcnid, tcid, date, version, ssver, name, author, testDescription) VALUES (1, 1, "03.01.1987", 1, 2, "tc", "ChristophS", "description");

INSERT INTO TestCasesResults (tcnid, ssver, tgrid, tcrid, os, name, author, changedate, version, startTime, stopTime, tcResult, cor_tcResult,
    ts_ok, cor_ts_ok, ts_fail, cor_ts_fail, ts_crash, cor_ts_crash, ts_no, cor_ts_no,
    comment, rd_comment, state, cor_ts_exception, cor_ts_blocked) VALUES (1, 0, 1, 1, "os", "name", "author", "17.04.2013", "1.1.1", "2010/11/11 11:11:11.111", "2010/11/11 12:12:12.12", 0, 0,
    1, 2, 3, 4, 5, 6, 7, 8,
    "tcr comment", "tcr rd comment", 3, 1, 2);

INSERT INTO TestCasesResultDescription (tcrid, filePath, name, author, changedate, version, time, runTime, preparation, totalTime, software, hardware, descriptionValue) VALUES (1, "mytest.py", "mytest", "me", "04.01.1987", "1.2.3", "2010/11/15 11:11:11.111", "00:05:00", "00:00:00", "2010/11/15 15:11:11.111", "", "", "");

INSERT INTO TestSteps (pos, tcid, type, image, logText, id, title, stopOnFail, value, wait) VALUES (1, 1, "type", "", "Mein neuer Teststep", "1", "myteststep", "", "", "");

INSERT INTO TestStepsResults (pos, tcrid, tcid, ts_pos, logText, result, cor_result, id, time, comment, rd_comment, tc_comment, g_comment, traceback, state, stepValue, type) VALUES (1, 1, 1, 1, "Beschreibung des resultats", 1, 1, "1", "2013/01/11 11:11:11.111", "c1", "c2", "c3", "c4", "traceback", 1, 0, "type");


# alter database

select * from INFORMATION_SCHEMA.COLUMNS where TABLE_NAME='LabelIDNames'

ALTER TABLE LabelIDNames ALTER COLUMN labelid int PRIMARY KEY IDENTITY

DROP TABLE LabelIDNames;

CREATE TABLE LabelIDNames
(
   labelid  int IDENTITY(1,1) PRIMARY KEY,
   sslabel varchar(60),
   display_label varchar(60),
   Date varchar(60),
   OfficialLabel bit
)
