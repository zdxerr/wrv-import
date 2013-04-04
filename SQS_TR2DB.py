# -*- coding: utf-8 -*-

import _Configuration

import copy
import os
from datetime import time

import cfg

import SQSDB



logPath = os.path.join(_Configuration.logPath, _Configuration.foldername)

def logUpdate(txt):
    logPath = os.path.join(_Configuration.logPath, _Configuration.foldername)
    fa = open(os.path.join(logPath, "CRTITA-DBImport.UPDATE.csv"),"a")
    fa.write(txt)
    fa.close()


def ImportData(db, ts_root, folderpath, prodDBEntry):

    scriptnamedict = {}

    def fillZero(val):
        if len(val) == 1:
            val = "0" + val
        return val

    def getTimeStr(timeval):

        ltstr = time.localtime(_Configuration.gb_StartTime)
        mm = fillZero(str(ltstr[1]))
        dd = fillZero(str(ltstr[2]))

        # MichaelRo - unused
        #hh    = fillZero(str(ltstr[3]))
        #min   = fillZero(str(ltstr[4]))
        #ss    = fillZero(str(ltstr[5]))

        tstr = str(ltstr[0])+"/"+mm+"/"+dd  # +" "+hh+":"+min+":"+ss
        return tstr

    # Read the common information about the test from common fields of the
    # test case results.

    # @param  testRes  Unpickled crtita_result file.
    # @return  (sslabel,display_label) for correspondent fields in DB
    # LabelIDNames table.

    def getCommonTestData(testRes):
        try:
            testEnv = testRes["EnvInfo"]
            testRunCfg = testRes["TestrunConfig"]

            # MichaelRo
            # dispLabel  = testRunCfg["TestDescription"]
            dispLabel = cfg.getTestDisplayLabel(testRes)

            summary = testRes["Summary"]
            startTime = summary["Start time"]
            endTime = summary["End time"]
            _Configuration.gb_StartTime = \
                time.mktime(time.strptime(startTime, "%a, %d %b %Y %H:%M:%S"))
            if endTime.lower().find("finished") >= 0:
                _Configuration.gb_EndTime = _Configuration.gb_StartTime + 3600
            else:
                _Configuration.gb_EndTime = \
                    time.mktime(time.strptime(endTime,
                                "%a, %d %b %Y %H:%M:%S"))

            # set global variables in _Configuration.py, some CRTITA-versions
            # deliver numbers at key-start
            if 'Operating system' in testEnv:
                _Configuration.gb_OSWhileTestExec = \
                    testEnv.get('Operating system')
                _Configuration.gb_CRTITAVersion = testEnv.get('CRTITA version')
                _Configuration.gb_PythonVer = testEnv.get('Python version')
            if '6Operating system' in testEnv:
                _Configuration.gb_CRTITAVersion = \
                    testEnv.get('1CRTITA package version')
                _Configuration.gb_FrameVersion = testEnv.get('2Frame version')

                for k in testEnv.keys():
                    if k.find("3Extensions")>=0:
                        hstr = k[len("3Extensions\\"):]
                        _Configuration.gb_Extensions = _Configuration.gb_Extensions + ["Ext. " + hstr + ": " + testEnv[k]]
                    if k.find("4Libraries")>=0:
                        hstr = k[len("4Libraries\\"):]
                        _Configuration.gb_Libraries = _Configuration.gb_Libraries + ["Lib. " + hstr + ": " + testEnv[k]]
                _Configuration.gb_PythonVer         = testEnv["5Python version"]
                _Configuration.gb_OSWhileTestExec   = testEnv["6Operating system"]

            _Configuration.gb_TestScriptCtrlParameter = testRunCfg["TestScriptCtrlParameter"]
            _Configuration.gb_TestScriptParameter   = testRunCfg["TestScriptParameter"]
            _Configuration.m_StartNextTest          = _Configuration.gb_StartTime
            # set the label as identifier for the DB
            timestr = getTimeStr(_Configuration.gb_StartTime)
            if prodDBEntry.find('CFG')>0:
                nbstr = 'CFG_'
            else:
                nbstr = 'IMPL_'
            if dispLabel.lower().find("trigger")>=0:
                dblabel  = nbstr+dispLabel[len("TRIGGER/REPETITION:"):-1].strip(" \r\n./")[:25]+": "+timestr
                dispLabel= dispLabel[len("TRIGGER/REPETITION:"):-1].strip(" \r\n./")[:38]+": "+timestr
            elif dispLabel.lower().find("nightly")>=0:
                dispLabel= "NightlyBuild: " + timestr
                dblabel  = nbstr+dispLabel
            #elif dispLabel.lower().find("smoke")>=0:
            #    dispLabel= "Smoke-Test: " + timestr
            #    dblabel  = nbstr+dispLabel
            else:
                dispLabel= dispLabel.strip(" \r\n./")[:38]+": "+timestr
                dblabel  = nbstr+dispLabel
        except:
            dblabel = dispLabel
            debug("Exception handling global CRTITA-Testdata.", Level=1, Fcn="CRTITA2DB",NoTB = False)
        return dblabel,dispLabel

    #   read and convert the execution time from a test script
    def getExecTimeAsString(testResult):
        result = "01:00:01"
        hstr = testResult["execTime"].strip(']')
        hstr = hstr.split('[')
        if len(hstr) > 2:
            result = hstr[2]
        return result

    def getTSTypeAsString(path, testResult):
        result = "NUnit"
        # calculate filetype
        if string.lower(path[-1:]) == "m":
            result = "M"
        elif string.lower(path[-2:]) == "py":
            result = "executePython"
            tstypes = testResult["logDataList"]
            for i in range(len(tstypes)):
                logFileName = tstypes[i]["ID"]
                if logFileName.lower().startswith("crtita_nunit"):
                    # MichaelRo - unused
                    # tstype = "NUnit"
                    break
        return result

    ##   @param  tcPreName  NOT USED
    def createOrUpdateCrashed(tcomprid, testResult, path, tcnum, tcPreName,
                              groupName, prtcid, tlid1, tlid2, labelid, oswt,
                              starttime, stoptime):
        tcnid = None
        tcrid = None

        #version    = "1.00.00"     # muss noch geschickt geholt werden
        #ssver      = 1             # muss noch geschickt geholt werden
        #author     = "<unknown>"   # muss noch geschickt geholt werden
        # version, ssver, author, date = \
        #     StoreCRTITAResults2DB.getScriptInformation(scriptnamedict, path)
        status = 2             # crashed

        # MichaelRo - unused
        #g_comment  = ""
        #tc_comment = ""
        #stepValue  = ""

        tstype = getTSTypeAsString(path, testResult)
        tcaseName = "Crash-Dummy-Name"
        comment = "Complete Script has crashed! No Testcases computable ..."
        ts_ok, ts_fail, ts_crash, ts_no = 0, 0, 0, 0
        if testResult["status"] == 3:
            status = 4       # bedeutet "blocked" in WRV
            ts_no = 1
            comment = "Script aborted during initialization!" \
                      "No Testcases/Teststeps computable ..."
        else:
            ts_crash = 1

        tcListEntry = {'ScreenShots': [], 'status': status,
                       'tcName': tcaseName, 'tcNum': 0, 'userData': {}}

        # MichaelRo
        ## tcName = tcPreName+tcListEntry["tcName"]
        ## tcName = tcListEntry["tcName"]
        tcName = cfg.getTestCaseName(tcListEntry)

        testDescription = tcName

        tgid = db.createGetTestGroupID([prtcid, tlid1, tlid2], groupName)
        tgrid = db.setGetTestGroupResultID(tcomprid, tgid, "")
        found = False

        if not found:
            # Copy Test Case and TestSteps to DataBase, if not exists
            tcnid = db.GetTestCasesNameIdByName(tgid,path+ " : "+str(tcnum))
            if tcnid==-1:
                tcnid = db.AddTestCaseName(tgid,path+ " : "+str(tcnum))

            tcid = StoreCRTITAResults2DB.StoreTestCaseAndSteps(db,tcnid,tcListEntry,tstype,date, starttime, stoptime, scriptnamedict, path, testDescription, author, version)

            # testcaseresult is already in DB?
            tcrid = db.GetTestCasesResultIDByTGRID(tgrid,tcnid)
            if tcrid==-1:
                tcrid = db.AddTestCaseResult( tcnid, ssver, labelid, oswt, tcName, author, date, version, starttime, stoptime, status)
            else:
                db.UpdateTestCaseResult( tcrid, ssver, oswt, author, date, version, starttime, stoptime, status)

            tcb = StoreCRTITAResults2DB.fillTraceBack(testResult)

            TestSteps = db.FindTestStepsByTcid(tcid) # returns struct of POS,TCID,ID,TITLE
            if (TestSteps != None) and (TestSteps != []) and (TestSteps != {}):
                for tStep in TestSteps:
                    ts_pos = tStep[0]
                    i      = tStep[2]
                    text   = tStep[3]
                    found = db.FindTestStepResult(i,tcrid)
                    if found == False:
                        #  AddTestStepResult(self,pos,tcrid,tcid,ts_pos,logText,result,id,time,comment,tcb,g_comment="",tc_comment="",type="",stepValue=""):
                        db.AddTestStepResult(i,tcrid,tcid,ts_pos,tcb,status,i,starttime,comment,tcb,"","",tstype,text)
            else:
                found = db.FindTestStepResult(1,tcrid)
                if found == False:
                    db.AddTestStepResult(1,tcrid,tcid,1,tcb,status,1,starttime,comment,tcb,"","",tstype,"StepResult, created by Importer ...")

            db.UpdateTestCaseResultStatistic(tcrid,ts_ok,ts_fail,ts_crash,ts_no)

            db.AddTestCasesResultFiles(tcrid,labelid,testResult)

        # tgrid = db.setGetTestGroupResultID(tcomprid,tgid,"")
        return tgrid
        #debug("Project    : "+ssResultPath+"     Label : "+verLabel, Level=1, Fcn="CRTITA2DB",NoTB = True)





    ##
    ##   Analyse and store the given test script results and information.
    ##
    ##   @remark   Called only once from ImportData().
    ##
    ##   @param    path        Relative path to testscript, key for crtita_result['TestResult'], for example: "001_dyn_event\Test001\at_01_fibex20\t_dsfr_pdu_dyn_event_test.py".
    ##   @param    groupName   Last dir from test case TLIDName path before at-dir, for example: "Test001".
    ##   @param    tcPreName   NOT USED LATER.
    ##   @param    labelid     Test label ID for total test, links to LabelIDNames DB table entry.
    ##   @param    testResult  Test case result to store, crtita_result['TestResult'][path][0].
    ##   @param    prtcid      With tlid* key to TLIDName table entry for this test case.
    ##   @param    tlid1       "
    ##   @param    tlid2       "
    ##
    ##   @return   Author.
    ##

    def analyseResult(path,groupName,tcPreName,labelid,testResult,prtcid,tlid1,tlid2):
        try:

            # collect some information from the test results
            # m_execTime = getExecTimeAsString(testResult)

            # get OS/Matlab version String - OS from crtita_result['EnvInfo'], MATLAB (if any) version from Conf.txt
            oswt = WRV_Helper.getOS(_Configuration.gb_OSWhileTestExec, _Configuration.gb_MATLABVer)

            # get test run times from crtita_result['TestResult'][path][0] ['execTime'] / ['testDuration']
            starttime, stoptime, runtime = StoreCRTITAResults2DB.getTimeInformation(testResult)

            # get "1.00.00" , 1 , author or "<unknown>" , date or "2011-07-01 00:00:00"
            version, ssver, author, date = StoreCRTITAResults2DB.getScriptInformation(scriptnamedict, path) #@UnusedVariable

            # check if the Result is already checked in, if not, create new result entry
            tcomprid = db.GetTestComponentResultID([prtcid,tlid1,tlid2],labelid,oswt,"",_Configuration.gb_StartTime)
            if None == tcomprid:
                tcomprid = db.createGetTestComponentResultID([prtcid,tlid1,tlid2],labelid,oswt,"",_Configuration.gb_StartTime)

            # get extensions and libraries as one info string, if found in crtita_result['EnvInfo']
            envdescr = StoreCRTITAResults2DB.getEnvDescription()

            # gb_StartTime from crtita_result['Summary']['Start time'] (Python floating point time())
            db.updateTestComponentResult_ResDesc(tcomprid,testResult,oswt,_Configuration.gb_StartTime, envdescr, author)

            #  'NUnit' or 'M' or 'executePython' (all steps must have the same type)
            tstype = getTSTypeAsString(path,testResult)

            tgrid = -1

            # -------------------------------------------------
            # Run over all TestCases for this group (script), if exists
            fileIds = []
            tcList = testResult["tcList"]
            tcComment = testResult["comment"]
            if (tcList != None) and (tcList != []):   # one ore more test cases exist

                # to optimize db-access
                tgid  = db.createGetTestGroupID([prtcid, tlid1, tlid2], groupName)   # get or add TestGroups DB entry
                tgrid = db.setGetTestGroupResultID(tcomprid,tgid,"")                 # get or add TestGroupResult DB entry

                for i in range(len(tcList)):

                    tcListEntry     = tcList[i]
                    tcnid           = None
                    tcrid           = None

                    # MichaelRo
                    # tcName          = tcListEntry["tcName"]
                    tcName          = cfg.getTestCaseName(tcListEntry)

                    testDescription = tcName

                    # get/add test case name from/to DB table TestCasesName, name is "<path> : <n>", n consecutive number 1 ..
                    tcnid = db.GetTestCasesNameIdByName(tgid,path + " : "+str(i+1))
                    if tcnid==-1:
                        tcnid = db.AddTestCaseName(tgid,path+ " : "+str(i+1))

                    #   Add TestCases Entry and TestSteps entry/entries.
                    #
                    #   db              - database object
                    #   tcnid           - TestCasesName table entry ID
                    #   tcListEntry     - test case result dict - crtita_result['testResult'][<path>][0]['tcList'][n]
                    #   tstype          - 'NUnit' or 'M' or 'executePython'
                    #   date            - date from scriptnamedict or fixed "2011-07-01 00:00:00" if not found
                    #   starttime       - test start time "2010/11/11 11:11:11.111"
                    #   stoptime        - test stop time "2010/11/11 11:11:11.111"
                    #   scriptnamedict  - {path: author, ... } or {path: [author,date], ... }
                    #   path            - relative path to testscript, key for crtita_result['TestResult']
                    #   testDescription - one or more lines test description, crtita_result['testResult'][<path>][0]['tcList'][n]['tcName']
                    #   author          - author from scriptnamedict[path] or '<unknown>'
                    #   version         - "1.00.00"
                    #
                    StoreCRTITAResults2DB.StoreTestCaseAndSteps(db,tcnid,tcListEntry,tstype,date,starttime,stoptime,scriptnamedict,path, testDescription, author, version)

                    # Copy Test Case Results to DataBase
                    #
                    #   db              - database object
                    #   tgrid           - TestGroups table entry ID.
                    #   tcnid           - TestCasesName table entry ID
                    #   labelid         - LabelIDNames table etry ID.
                    #   oswt            - OS/Matlab version String
                    #   path            - relative path to testscript, key for crtita_result['TestResult']
                    #   tcName          - test case description (one or more lines)
                    #   tcListEntry     - test case result dict - crtita_result['testResult'][<path>][0]['tcList'][n]
                    #   tstype          - 'NUnit' or 'M' or 'executePython'
                    #   starttime       - test start time "2010/11/11 11:11:11.111"
                    #   stoptime        - test stop time "2010/11/11 11:11:11.111"
                    #   runtime         - test run time ""443.13 Sek."
                    #   scriptnamedict  - {path: author, ... } or {path: [author,date], ... }
                    #   tcComment       - component / script comment - crtita_result[‘testResult'][<path>][0][‘comment’]
                    #
                    tcrid = StoreCRTITAResults2DB.StoreTestCaseResult(db,tgrid,tcnid,labelid,oswt,path,tcName,tcListEntry,tstype,starttime,stoptime,runtime,scriptnamedict,tcComment)

                    # ----------------------------------------------------------------------------
                    # Add additional Logfiles to TestCaseResult
                    #
                    if i==0:
                        fileIds = db.AddTestCasesResultFiles(tcrid,labelid,testResult)
                    else:
                        db.AddTestCasesResultFilesReference(tcrid,labelid,testResult,fileIds)

                    # -----------------------------------------
                    # Add additional Information to TestCaseResult
                    #
                    StoreCRTITAResults2DB.StoreMainTest(db,testResult,tcnid,tgrid)

            # probably the test was crashed or excluded ... no testcase and no steps exists!
            else:
                # no entry for excluded testscripts!
                tgrid = createOrUpdateCrashed(tcomprid,testResult,path,1,tcPreName,groupName,prtcid,tlid1,tlid2,labelid,oswt,starttime, stoptime)

            # -------------------------------------------------------------------------
            # Update Test Group Results in the DataBase
            #
##            if tgrid>0:
##                db.UpdateTestGroupResult(tgrid)

            # calculate the next start-time
            #calculateNextStartTime(m_execTime)

            return author
        except:
            debug("Exception handling CRTITA-Result file.", Level=1, Fcn="CRTITA2DB",NoTB = False)
            return "Exception occured - No author computed!"





    ##
    ##   Get test case path for WRV hierarchy view only, not for test case file access (no real path).
    ##
    ##   Replace \ with /, prepend /<productname>/
    ##   (assuming that prodDBEntry has a leading /).
    ##
    ##   Ensure that result contains at least 3 elements, otherwise duplicate
    ##   testgroup to keep WRV running - a CRTITA test result key has at least
    ##   3 elements: <testgroup>, <at-dir>, <scriptname>, with prepended
    ##   /<productname> = '', 'productname' only one more element is
    ##   necessary to reach 6 elements after splitting and 3 after skipping
    ##   leading '' and trailing <at-dir>, scriptname.
    ##
    ##   If a part (from root) of the path is an existing leaf in the DB, i.e.
    ##   contains a test case, this cannot contain more test cases (paths) in sub
    ##   directories (per definition). Then the leaf path (truncated result)
    ##   is returned.
    ##
    ##   @param   ResultName  Key from crtita_result TestResult[<key>],
    ##                        i.e. path to test script, no leading/trailing / or \.
    ##
    ##   @return  Test case path with product name, without at-dir and script name.
    ##

    def getTLIDNameFromTestResult(Resultname):
        ssTCP = prodDBEntry+"/"+Resultname.replace("\\","/")
        subElements = string.split(ssTCP,"/")
        i = 0
        ss = "/"
        limit = 3
        if len(subElements) <= 5:                # ensure min 6 elements ('', productname, testgroup, testgroup, at-dir, scriptname)
            subElements.insert(2,subElements[2])

        # check each part of the path from root if it is an existing leaf in DB, if so, return it
        while i<len(subElements)-limit:
            i += 1
            if (db.CheckTLIDNameIsLeaf(ss) == True):
                break
            ss = ss + subElements[i] + "/"       # i >= 1, subElements[1] = productname

        return ss





    ##
    ##   Get test group name from test result file and test case part of test case path.
    ##
    ##   The test group is normally the directory name over the at-directory:
    ##   /<product name>/<root dir>/ ... /<testgroup>/<at-dir>/<script name>,
    ##   exactly it is the last dir in the test case TLIDName table entry,
    ##   which may be a higher dir in case of existing tests in different
    ##   dir levels of the same path.
    ##
    ##   The test case part is normally '',<at-dir>,<script name>.
    ##
    ##   Uses global prodDBEntry "/<product name>".
    ##
    ##   @TODO tcpart erroneous on <testgroup> duplication in getTLIDNameFromTestResult()
    ##   @TODO tcpart erroneous if leaf = 1 dir (already in DB) contain other test sub dirs
    ##
    ##   @remark  Called only once from ImportData().
    ##
    ##   @param   ssResultPath  Path to test script = key for crtita_result['TestResult'], for example "031_static_mux_pdu\Test001\at_001_fibex31\t_fibex31_static_mux_pdu.py"
    ##   @param   ssTLIDName    DB test case path with leading product name, without at-dir and script name, for example "/FRCP/031_static_mux_pdu/Test001/"
    ##
    ##   @return  (<group name, @see cfg.getTestGroupName()>,['', ... ,<at-dir>,<script name>])
    ##

    def getGroupName(ssResultPath, ssTLIDName):

        ssTCPath    = prodDBEntry + "/" + ssResultPath.replace("\\","/")  # /<product name>/ + path from TestResult key, without trailing /
        ssTCP       = ssTCPath[len(ssTLIDName) - 1:]                      # test case part, remove leaf path -> "/ ... /<at-dir>/<script name>"
        tcpart      = ssTCP.split("/")                                    # -> ['', ... ,'<at-dir>','<script name>']

        return cfg.getTestGroupName(ssResultPath,ssTLIDName),tcpart

    # Get test case name from test case path parts list.
    # @remark  Called once from ImportData() with tcpart from getGroupname().
    # @param   name   tcpart from getGroupname()
    # @return  (Erroneous) Test case name (NOT USED from caller).

    def getTestCaseName(name):
        i = 2
        hstr = ""
        while i < len(name):
            hstr = hstr + name[i] + "/"
            i += 1
        return hstr

    #
    # Ab hier wird die Liste der TestSuiten geholt.
    #
    # ssTestCasesPaths => Liste der TestSuiten
    # Ergibt die Struktur der Datenbank!!!!!
    print "TEST"

    Res = crtita_result.CRTITAResultFileClass(ts_root + "\crtita_result")
    Res.Load()
    CompleteContent = Res.GetResult()

    # MichaelRo
    cfg.cfgInit(CompleteContent)
    scriptnamedict = cfg.getScriptInfo(_Configuration.FI_AddInfoFolder,folderpath)

    # mr TEST
    # return

    TestResults = CompleteContent["TestResult"]                                # get test results from complete result
    verlabel, displabel = getCommonTestData(CompleteContent)                   # get common test data _Configuration and labels

    timestamp = time.strftime("%d/%m/%y %H:%M:%S",time.localtime(_Configuration.gb_StartTime))  # Starttime of complete  testrun

    labelid = db.createGetLabelID(verlabel,displabel,timestamp)                # create new LabelIDNames DB entry or get ID for existing (update time)
    ssTestCasesPaths = TestResults.keys()                                      # get all test case script paths from test result
    testCasesCount = len(ssTestCasesPaths)

    debug("Root Path: "+str(ts_root), Level=0, Fcn="CRTITA2DB", NoTB = True)
    debug("Number of Root Projects: "+str(testCasesCount), Level=0, Fcn="CRTITA2DB",NoTB = True)

    #return

    if len(ssTestCasesPaths) > 0:

        ###
        #
        #   Get DB compatible directory structure from
        #
        #     - crtita_result['TestResult'][<key>] keys
        #     - PRODUCTNAME entry in Cont.txt
        #
        #   and store it in TLIDName table in DB. "DB compatible":
        #
        #     - at-dir and script name discarded
        #     - if part of path already exist as leaf in DB, discard rest
        #     - if path is too short, insert dummy dir
        #

        tPath = ""
        ssTLIDNames = []
        ssTestCasesPaths.sort();
        for ssTCP in ssTestCasesPaths:
            ssTLIDName = getTLIDNameFromTestResult(ssTCP)       # get DB compatible leaf path (if part of path found as leaf in DB, or path has not enough elements)
            if tPath != ssTLIDName:                             # avoid duplicates
                tPath = ssTLIDName
                ssTLIDNames.append(ssTLIDName)
                db.checkAddTLIDNameByPath(tPath)                # INSERT path and all path parts not in DB as TLIDName entries in DB
                db.setTLIDNameStatus(tPath,"Wait for Update")   # set status for leaf path only, regardless if new or path already in DB

        #
        ###



        ###
        #
        #    For all components (scripts (groups) with test cases) ...
        #

        ssResultPathCount     = 0
        ssTestCasesPathsCount = str(len(ssTestCasesPaths))
        ssTLIDName            = ""
        ssResultPath          = ""
        tscres                = None

        for ssResultPath in ssTestCasesPaths:

            startt = time.time()
            startnr= _Configuration.gb_SQLStatements

            ssTLIDName          = getTLIDNameFromTestResult(ssResultPath)      # get leaf test path from test case path and TLIDName DB table
            ssGroupName, tcPart = getGroupName(ssResultPath, ssTLIDName)       # <group name>, tcpart ['', ... ,<at-dir>,<script name>]
            ssTestCaseName      = getTestCaseName(tcPart)                      # NOT USED: '.../<at-dir>/<script name>/'
            ssResultPathCount  += 1

            debug("-----------------------------------------------------------", Level=0, Fcn="CRTITA2DB",NoTB = True)
            debug("P a t h : "+ssTLIDName+" ("+str(ssResultPathCount)+"/"+ssTestCasesPathsCount+")", Level=0, Fcn="CRTITA2DB",NoTB = True)

            db.setTLIDNameStatus(ssResultPath,"Update Started")                # set leaf path's Status in DB table TLIDName
            prtcid,tlid1,tlid2 = db.getTLIDbyPath(ssTLIDName)                  # get leaf test path's key (prtcid/tlid1/tlid2) in DB table TLIDName

            debug("T L I D : "+str(prtcid)+" "+str(tlid1)+" "+str(tlid2), Level=0, Fcn="CRTITA2DB",NoTB = True)
            debug("TestCase: "+str(ssResultPath)+" "+str(ssGroupName)+" "+str(ssTestCaseName), Level=0, Fcn="CRTITA2DB",NoTB = True)

            tscres = TestResults[ssResultPath][0]                              # result for one test script, one or more test cases
            if tscres != None:
                if prtcid != -1:                                               # can this happen? (only if TLIDName table in DB is changed from another running process)

                    # status: -2:"execution disabled", -1:"excluded", 0:"passed", 1:"failed",  2:"aborted",  3:"aborted during initialization", 4:"aborted during cleanup", 5:"user defined abort"
                    if tscres["status"] >= 0:

                        # for not excluded/disabled test cases

                        # ssResultPath        -  relative path to testscript, key for crtita_result['TestResult']
                        # ssGroupName         -  last dir before at-dir from test case TLIDName path
                        # ssTestCaseName      -  NOT USED in analyseResult()
                        # labelid             -  test label ID, links to LabelIDNames DB table entry
                        # tscres              -  crtita_result['TestResult'][ssResultpath][0], test case result
                        # prtcid,tlid1,tlid2  -  links to TLIDName DB entry for this test case

                        author = analyseResult(ssResultPath,ssGroupName,ssTestCaseName,labelid,tscres,prtcid,tlid1,tlid2)


                        logUpdate(ssResultPath+";" + author + "\n")
                        #------------------------------------------
                        # Update-Information in die DB eintragen ...
                        db.setTLIDNameUpdateTime(ssTLIDName)
                        db.setTLIDNameStatus(ssTLIDName,"Update finished")

                        #------------------------------------------
                        # Update der Ergebnisse antriggern ...
                        db.UpdateTestComponentsResultsByPath(ssTLIDName, labelid)

                    else:
                        #------------------------------------------
                        # Update-Information in die DB eintragen ...
                        version, ssver, author, date = StoreCRTITAResults2DB.getScriptInformation(scriptnamedict, ssResultPath) #@UnusedVariable
                        logUpdate(ssResultPath+";" + author + "\n")
                        db.setTLIDNameUpdateTime(ssTLIDName)
                        db.setTLIDNameStatus(ssTLIDName,"No Testresult-data found!")

                else:
                    #------------------------------------------
                    # Update-Information in die DB eintragen ...
                    version, ssver, author, date = StoreCRTITAResults2DB.getScriptInformation(scriptnamedict, ssResultPath) #@UnusedVariable
                    logUpdate(ssResultPath+";" + author + "\n")
                    db.setTLIDNameUpdateTime(ssTLIDName)
                    db.setTLIDNameStatus(ssTLIDName,"No Testresult-data found!")
            else:
                #------------------------------------------
                # Update-Information in die DB eintragen ...
                version, ssver, author, date = StoreCRTITAResults2DB.getScriptInformation(scriptnamedict, ssResultPath) #@UnusedVariable
                logUpdate(ssResultPath+";" + author + "\n")
                db.setTLIDNameUpdateTime(ssTLIDName)
                db.setTLIDNameStatus(ssTLIDName,"No Testresult-data found!")
                debug("DB-Importer : "+str(ssResultPath)+" contains no Testresult-data", Level=0, Fcn="CRTITA2DB",NoTB = True)

            endt = time.time()
            endnr= _Configuration.gb_SQLStatements
            print "Imported "+str(ssResultPathCount)+" from "+str(ssTestCasesPathsCount)+": "+str(endt-startt).replace(".",",")+" sec ("+str(endnr-startnr)+" SQL Statements)."
            SQSDB_Logging.logging("Imported "+str(ssResultPathCount)+" from "+str(ssTestCasesPathsCount)+": "+str(endt-startt).replace(".",",")+" sec ("+str(endnr-startnr)+" SQL Statements)", logPath)

            #break  # erst mal nur einen Datensatz schreiben ...

        #
        ###





## @remark Not used.

def sqs2db(ts_root_org,Jobs = ["newImport"],debugFlag=False, inifile = "",label=None):
    # ------------------------------------------------------------------------------
    # Write comment to update log.
    #
    t = time.localtime(time.time())
    logUpdate("Start: "+str(t[2])+"."+str(t[1])+"."+str(t[0])+" "+str(t[3])+":"+str(t[4])+":"+str(t[5])+"\n")
    logUpdate(str(ts_root_org)+":"+str(Jobs)+"\n")


    # ------------------------------------------------------------------------------
    # Open the Data Base.
    #
    db = SQSDB.SQS2SQL(None)
    db.OpenDB(debugFlag)                     # Use productiv DB


    # ##############################################################################
    # Main execution loop
    #
    print "     Jobs",Jobs

    for Job in Jobs:
        debug("Executing Job:"+Job, Level=0, Fcn="CRTITA2DB",NoTB = True)

        ts_root = copy.copy(ts_root_org)

        try:

            # ------------------------------------------------------------------
            # Import Data
            #
            if Job == "newImport":
                debug("ts_root:"+str(ts_root), Level=0, Fcn="CRTITA2DB",NoTB = True)

                #stat = os.stat(ts_root+"\crtita_result")
                #ts_exectimestamp = time.strftime("%d/%m/%y %H:%M:%S",time.localtime(stat.st_mtime))

                ImportData(db,ts_root,label,label)

        except:
            debug("Exception working on Job:"+Job, Level=1, Fcn="CRTITA2DB")
            pass


    # ------------------------------------------------------------------------------
    # Close the Data Base.
    #

    db.CloseDB()
    db = None

    # ------------------------------------------------------------------------------
    # Write comment to update log.
    #

    t = time.localtime(time.time())
    logUpdate("End: "+str(t[2])+"."+str(t[1])+"."+str(t[0])+" "+str(t[3])+":"+str(t[4])+":"+str(t[5])+"\n\n\n")

'''
if __name__ == '__main__':

    print "Argumente: \n", sys.argv, "\n Anzahl: ", len(sys.argv), "\n\n"

    ts_root = _Configuration.FI_ImportPath
    if len(sys.argv)>1:
        ts_root = sys.argv[1]
        if (ts_root[len(ts_root)-1] != "\\"):
            ts_root = ts_root + "\\"
    print "Import-Root: ",ts_root

    prodDBEntry = _Configuration.preDBEntry
    if len(sys.argv)>=2:
        prodDBEntry = sys.argv[2]
        if prodDBEntry.find(_Configuration.prePath)<0:
            prodDBEntry = _Configuration.prePath+prodDBEntry
    print "DB-ProductRoot: ",prodDBEntry

    addinfo = _Configuration.FI_AddInfoFolder + "crtita_scriptresultstatusfile.csv"
    f = open(addinfo)
    try:
        scriptnamedict = {}
        for line in f:
            line= line.strip("\n")+';'
            col = line.split(";")
            # ------------------------------------------------------
            # col[0] = "SCRIPT"
            # col[1] = script-Name
            # col[2] = status
            # col[3] = html-name
            # col[4] = author
            sname   = col[1].strip(" ")
            author  = col[4]
            scriptnamedict[sname] = author
    finally:
        f.close()

    DBImpLog = _Configuration.logPath
    if os.path.exists(DBImpLog)==False:
        os.mkdir(DBImpLog)

    npath = sys.argv[0]
    if npath.find("\\")>=0:
        npath = npath[0:npath.rfind("\\")]
        addPath(npath)

    t = time.localtime(time.time())
    logUpdate("Start: "+str(t[2])+"."+str(t[1])+"."+str(t[0])+" "+str(t[3])+":"+str(t[4])+":"+str(t[5])+"\n")

    # ------------------------------------------------------------------------------
    # Open the Data Base.
    #
    debugFlag=False
    db = SQSDB.SQS2SQL(None)
    db.OpenDB(debugFlag)            # Use productiv DB

    try:
        print "Import is running ..."
        print sys.argv

        #db.EmptyTables()            # nur für die Tests, solange noch nicht alles rund läuft!!!

        stat = os.stat(ts_root+"crtita_result")
        #ts_exectimestamp = time.strftime("%d/%m/%y %H:%M:%S",time.localtime(stat.st_mtime))

        label = None
        ImportData(db,ts_root,prodDBEntry,scriptnamedict)
        print "Import finished!"
    except:
        debug("Exception",1,"XML2DB")
        debug("Exception working on Import data")
        pass

    db.CloseDB()
    db = None
'''
