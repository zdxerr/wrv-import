# -*- coding: utf-8 -*-
# ##############################################################################
#
#                                S Q S D B
#
# This script contains the direct access functions for the data base.
#
# Limitation: - All ' are replaced by &amp;
#             - PyMsSql doesn't support bigint
#
# Author: Marek Roehm
#

Date    = "24.06.2009"
Version =  "2.00.03"

"""
ToDo:
    -


History:
    2.00.03 - MR - Improve AddTestCasesResultDescription
                 - Improve TestStep Search for Unicode DB
    2.00.02 - MR - Unterstuetzung f�tCase Kommentare zwischen den TestCases
    2.00.01 - MR - Optimierung f�code Datenbank
    2.00.00 - MR - Anpassungen f�ssql 1.00.02
                   und MSSQL 2005
                   und Unicode
                   - SQLStatementResult
                     - Autocommit ist per default False
                   - Vereinheitlichung der Datei f�ort
                     aus SS und aus Dateien
    1.04.00 - MR - Changes to support direkt DB import:
                   Fixing wrong Statistic:
                   - UpdateTestComponentsResults
                   - UpdateTestCaseResultTCRID
                   - help_getResults
                   - UpdateTestGroupResult
                   Fix missing TestCandidate Info:
                   - updateTestComponentResult_ResDesc
    1.03.02 - MR - Anpassung f�e Datenbank
    1.03.01 - MR - updateTestComponentResult_ResDesc
                    - Fix Problem with OSWhileTestExec,ShortTestPCDesc...
    1.03.00 - MR - Add a table: TestCasesResultDescription
                   and change another table: TestStepsResults
                   - AddTestCasesResultDescription
    1.02.02 - MR - Use old Server
    1.02.01 - MR - Use new Server
    1.02.01 - MR - Fix some problemes
                    - Split update command to avoid lenght problem
                      (Should fix date problem)
                    - Update TEstComponentsResults, fix None Problem
    1.02.00 - MR - Use new Server
    1.01.19 - MR - Update: Calculate Statistics.
    1.01.18 - MR - Change Update TestComponents
    1.01.17 - MR - Correct Data Error
    1.01.16 - MR - Use Debug DB
    1.01.15 - MR - Convert TextCasesNames to dbstrings
    1.01.14 - MR - Fix lenght problem of Label Names
    1.01.13 - MR - Update "saveUserInfo"
                 - Update Label Time only if time > 0
    1.01.12 - MR - createGetLabelID uses dbString to convert Label
    1.01.11 - MR - Improve Statistic Update Error Handling
    1.01.10 - MR - Shorten Debug Output
    1.01.09 - MR - Rais exception if DB should be deleted
    1.01.08 - MR - getNewTLID: Support level < 2
    1.01.07 - MR - Define first INDEX Table to speed up DB.
    1.01.06 - MR - Support debug database.
    1.01.05 - MR - Fix Bug in getNewTLID: Create new TLID if a item has no sub items.
    1.01.04 - MR - Set Result to -99999 if correct Value can't be get.
                 - Improve error handling of getNewTLID
    1.01.03 - MR - Save the user edited Data from the DB.
    1.01.02 - MR - TestStepResults supports traceback field.
                 - Update Label Time
    1.01.01 - MR - Correct Error on Masking "'"
    1.01.00 - MR - Add TLID into strukture.
    1.00.10 - MR - Extend LabelIDNames by "Date"
                 - Extend TestComponentsResults for ResultDesk Info
    1.00.09 - MR - Extend TLIDName by "UpdateTime" and "Status"
    1.00.08 - MR - Add "OfficialLabel" Flag to Label Table
    1.00.07 - MR - Add display Label to Label Table
                 - Correct the display label strings
                 - Create dummy entry (-1)
    1.00.06 - MR - Add a Reference between TestSteps / TestStepsResults.
    1.00.05 - MR - TestComponentsResults supports OS.
    1.00.04 - MR - Minor Bug Fixes by Update Functions
    1.00.03 - MR - Add Table for TestGroupsResult
                 - Update Statistic Info
    1.00.02 - MR - Add Result of Test Steps to Test Case
    1.00.01 - MR - Optimize DB Structure (Use varchar instad of text)
                 - Add Table for Labels
                 - Add Table for TestComponentResult
    1.00.00 - MR - First fully working version
"""


#-------------------------------------------------------------------------------
# Import of some basic functions
#

# MichaelRo
# from SQSDB_Logging import * # Logging of this script
from SQSDB_Logging import debug,debugLog

import _Configuration

import pymssql              # External modul used to access data base
                            # More info: http://pymssql.sourceforge.net/
import string               # String handling
import time                 # Time functions

# MichaelRo
# import sys                  # System access

import os                   # Operating System functions

# MichaelRo
import cfg




#-------------------------------------------------------------------------------
# Helpfunction: Convert a String so it can be saved into the DB
#
def dbStr(val):
    valStr =""
    try:
        if type(val) == type(""):
            valStr = unicode(val.replace("\0","").decode("iso-8859-1","replace").encode("ascii","xmlcharrefreplace"))
        elif type(val) == type(u""):
            valStr = val
        else:
            valStr = unicode(val)
    except:
        debug("Error: Can't convert String to unicode: Type " + str(type(val)) ,1,"SQSDB")
        print "               Can't convert String to unicode \n"+str(val)
        pass
    return valStr.replace("'","&apos;")

# Convert Date
def convDate(dt):

    if len(dt) == 24:
        y = dt[-4:]
        m = dt[4:7]

        if m == "Jan":
            m = "01"
        elif m == "Feb":
            m = "02"
        elif m == "Mar":
            m = "03"
        elif m == "Apr":
            m = "04"
        elif m == "May":
            m = "05"
        elif m == "Jun":
            m = "06"
        elif m == "Jul":
            m = "07"
        elif m == "Aug":
            m = "08"
        elif m == "Sep":
            m = "09"
        elif m == "Oct":
            m = "10"
        elif m == "Nov":
            m = "11"
        elif m == "Dec":
            m = "12"
        d = dt[8:10]

        dt = d+"."+m+"."+y
    return dt

#-------------------------------------------------------------------------------
# Helpfunction: Convert a Time-String into time
#
def convString2Time(dateNow,timeNow = "00:00:00"):
    splitDateNow = string.split(dateNow,".")
    splitTimeNow = string.split(timeNow,":")
    return time.mktime([string.atoi(splitDateNow[2]),string.atoi(splitDateNow[1]),string.atoi(splitDateNow[0]),string.atoi(splitTimeNow[0]),string.atoi(splitTimeNow[1]),string.atoi(splitTimeNow[2]),0,0,-1])

#-------------------------------------------------------------------------------
# Helpfunction: Convert a numeric value into hex-representation
#
def hex16(i):
    s = ("00000000"+hex(i)[2:])[-8:]
    return s[0:2]+"-"+s[2:4]+"-"+s[4:6]+"-"+s[6:8]

def isNullOrEmpty(res):
    return (res == None) or (res == [[None]]) or (res == []) or (res[0][0] == None)

# ##############################################################################
#
# Database Main Class
#
#
class SQS2SQL:

    #---------------------------------------------------------------------------
    # On Inint set some basic variables
    #
    def __init__(self,SourceSafe=None):
        self.con = None
        self.cur = None
        self.prePath = _Configuration.prePath

    #---------------------------------------------------------------------------
    # Open the Data base
    #
    def OpenDB(self,debugDB = False):
        if self.con == None:
            debug("host=%s, user=%s, Database=%s"%(_Configuration.DB_host,_Configuration.DB_user,_Configuration.DB_database))

            conn = pymssql.connect(host     = _Configuration.DB_host,
                                   user     = _Configuration.DB_user,
                                   password = _Configuration.DB_password,
                                   database = _Configuration.DB_database)
            self.con = conn
            self.cur = conn.cursor()


    #---------------------------------------------------------------------------
    # Close the Data base
    #
    def CloseDB(self):
        self.con.commit()
        self.con.close()


    #---------------------------------------------------------------------------
    # Commit a statement
    #
    def Commit(self):
        self.con.commit()


    #---------------------------------------------------------------------------
    # Execute a SQL Statment and commit it.
    #
    def SQLStatement(self, statement, autocommit = True):
        ret = None
        try:
            _Configuration.gb_SQLStatements += 1
            startt = time.time()
            ret = self.cur.execute(statement)
            if autocommit == True:
                self.Commit()
            endt = time.time()
            substatement = statement[0:200]
            sec  = endt - startt
            if _Configuration.write_debugInformation == True:
                if sec > 0.02:
                    debugLog(str(sec).replace(".",",") + "; " + substatement, _Configuration.foldername, _Configuration.folderpath)
        except:
            if len(statement)>400000:
                debug("Error (Shortend): "+statement,1,"SQSDB")
            else:
                debug("Error: "+statement,1,"SQSDB")

        return ret


    #---------------------------------------------------------------------------
    # Execute a SQL Statment and commit it.
    #
    def SQLStatementResult(self, statement, autocommit = False):
        ret = None

        try:
            _Configuration.gb_SQLStatements += 1
            startt = time.time()

            ret = self.cur.execute(statement)

            if autocommit == True:
                self.Commit()

            try:
                ret = self.cur.fetchall()
            except:
                debug("No Result: "+statement,1,"SQSDB")
                ret = None

            endt = time.time()
            substatement = statement[0:200]
            sec  = endt - startt
            if _Configuration.write_debugInformation == True:
                if sec > 0.02:
                    debugLog(str(sec).replace(".",",") + "; " + substatement, _Configuration.foldername, _Configuration.folderpath)
        except:
            debug("Error: "+statement,1,"SQSDB")

        return ret





    ##
    ##   Store a TestCases item to DB if it does not exist.
    ##
    ##   "does not exist": (tcnid,date,version) does not match exactly.
    ##
    ##   @remark Called only from StoreTestCaseAndSteps(), StoreCRTITAResults2DB.py.
    ##
    ##   @param   tcnid             Testcases Field to set and used for searching existing test case.
    ##   @param   date              Testcases Field to set and used for searching existing test case.
    ##   @param   version           Testcases Field to set and used for searching existing test case.
    ##   @param   ssver             Testcases Field to set.
    ##   @param   name              Testcases Field to set.
    ##   @param   author            Testcases Field to set.
    ##   @param   testDescription   Testcases Field to set.
    ##
    ##   @return  Test case ID from existing test case or tcid for newly inserted (last max + 1).
    ##

    def CheckAddTestCase(self,tcnid,date,version,ssver,name,author,testDescription):
        tcid = self.GetTestCase(tcnid,date,version)

        if tcid == -1:
            #
            # Create a new tcid
            #

            self.SQLStatement("SELECT max(tcid) FROM [SQS].[TestCases];",False)

            result = self.cur.fetchall()
            if isNullOrEmpty(result):
                tcid = 1
            else:
                tcid = result[0][0] + 1

            #
            # Store the Test Case into the DB
            #

            val = str(tcnid)+","+str(tcid)+",'"+dbStr(date)  +"','"+dbStr(version)        +"',"+str(ssver)+",'"
            val +=dbStr(name)[:255]+"','"+dbStr(author)+"','"+dbStr(testDescription)+"'"
            sql = "INSERT INTO [SQS].[TestCases] (tcnid, tcid, date, version, ssver, name, author, testDescription) VALUES ("+val+");"

            self.SQLStatement(sql)

        return tcid


    # --------------------------------------------------------------------------
    # Add a TestCaseName
    #
    def AddTestCaseName(self,tgid,name):
        #
        # Create a new tcid
        #

        #self.SQLStatement("SELECT max(tcnid) from TestCasesName where tgid="+str(tgid)+" and name like '"+name+"';")
        self.SQLStatement("SELECT max(tcnid) FROM [SQS].[TestCasesName] where tgid="+str(tgid)+" and name = '"+dbStr(name)[:255]+"';",False)

        result = self.cur.fetchall()
        if isNullOrEmpty(result):
            tcnid = None
        else:
            tcnid = result[0][0] + 1

        if tcnid == None:
            #debug("TestCaseName NOT found: tgid="+str(tgid)+" and name = >"+name+"<",0,"SQSDB")

            self.SQLStatement("SELECT max(tcnid) FROM [SQS].[TestCasesName];",False)

            result = self.cur.fetchall()
            if isNullOrEmpty(result):
                tcnid = 1
            else:
                tcnid = result[0][0] + 1

            # store test case name into the DB
            val = str(tcnid)+","+str(tgid)+",'"+dbStr(name)[:255]+"'"
            sql = "INSERT INTO [SQS].[TestCasesName] (tcnid, tgid, name) VALUES ("+val+");"

            self.SQLStatement(sql)
        else:
            #debug("TestCaseName found: tgid="+str(tgid)+" and name = '"+name+"'",0,"SQSDB")
            pass

        return tcnid





    ##
    ##   Add new TestCasesResults DB entry with empty test step results and empty comments.
    ##
    ##   @param  tcnid       DB field: TestCasesName table entry ID (and used to get test group result ID).
    ##   @param  ssver       DB field: Source safe version (here: fixed 1, WRV: not used).
    ##   @param  labelid     LabelIDNames table entry ID (used to get test group result ID).
    ##   @param  oswt        DB field os: OS/Matlab version String (and used to get test group result ID).
    ##   @param  name        DB field: Test case name / description (one or more lines).
    ##   @param  author      DB field: Test script author or "<unknown>".
    ##   @param  changedate  DB field: Test script change date (here: date/time if known or "2011-07-01 00:00:00").
    ##   @param  version     DB field: Test script version (here: "1.00.00").
    ##   @param  starttime   DB field: Test start time "2010/11/11 11:11:11.111".
    ##   @param  stoptime    DB field: Test start time "2010/11/11 11:11:11.111".
    ##   @param  tcResult    DB fields tcResult and cor_tcResult: WRV result (see StoreTestCaseResult() (here: CRTITA result crtita_result['testResult'][<path>][0]['tcList'][n]['status'], only status > 0 !).
    ##
    ##   @return tcrid (test case result ID) of new DB entry.
    ##

    def AddTestCaseResult(self, tcnid, ssver, labelid, oswt, name, author, changedate, version, starttime, stoptime, tcResult):
        #
        # Get the Test Group Result ID
        #

        tgrid = self.createGetTestGroupResultID(tcnid,labelid,oswt)
        #sslabel = str(labelid)+" "+sslabel


        #
        # Create a new tcrid
        #

        self.SQLStatement("SELECT max(tcrid) FROM [SQS].[TestCasesResults];",False)

        result = self.cur.fetchall()
        if isNullOrEmpty(result):
            tcrid = 1
        else:
            tcrid = result[0][0] + 1


        #
        # Store the Test Case into the DB
        #

        val =  str(tcnid)+","+str(ssver)+","+dbStr(tgrid)+","+str(tcrid)+",'"+dbStr(oswt)+"','"+dbStr(name)[:255]  +"','"
        val += dbStr(author)+"','"+str(changedate)+"','"+dbStr(version)+"','"+dbStr(starttime)+"','"+dbStr(stoptime)+"',"
        val += str(tcResult)+","+str(tcResult)+", 0,0,0,0,0,0,0,0,'',''"

        sql = "INSERT INTO [SQS].[TestCasesResults] ("+\
                  "tcnid, ssver, tgrid, tcrid, os, name,"+\
                  "author, changedate, version, startTime, stopTime,"+\
                  "tcResult,cor_tcResult, ts_ok,cor_ts_ok,ts_fail,cor_ts_fail,ts_crash,cor_ts_crash,ts_no,cor_ts_no, comment,rd_comment"+\
              ") VALUES ("+val+");"

        self.SQLStatement(sql)

        return tcrid





    # --------------------------------------------------------------------------
    # Add a TestCasesResultFiles-Reference
    #
    def AddTestCasesResultFilesReference(self,tcrid,labelid,tcres,fileIds):
        path = "no path"
        if tcrid != None:
            # Add TestStepResultFileContents into the DB

            # MichaelRo
            # files = ""

            # MichaelRo
            # path  = tcres["logDataList"]
            path = cfg.getTestLogFiles(tcres)

            for i in range(len(path)):
                if (i < len(fileIds)) and (fileIds[i] > 0):
                    if (self.ExistsFileRef(fileIds[i], tcrid, labelid)==False):
                        val = str(tcrid) +","+str(labelid)+",'',"+str(fileIds[i])
                        sql = "INSERT INTO [SQS].[TestCasesResultFiles] (tcrid,labelid,path,fileId) VALUES ("+val+");"
                        self.SQLStatement(sql)
        else:
            debug("Skipping Adding Test Cases Result Files",1,"SQSDB")
            debug(str(tcrid)+" "+str(path),1,"SQSDB")




    # --------------------------------------------------------------------------
    # Add a TestCasesResultFiles (skript-based, not Step-based)
    #
    def AddTestCasesResultFiles(self,tcrid,labelid,tcres):
        path = "no path"
        if tcrid != None:

            # Add TestStepResultFileContents into the DB
            res   = []
            files = ""

            ###
            #
            # MichaelRo

            #if tcres.has_key("logDataList"):
            #    path  = tcres["logDataList"]
            #    for i in range(len(path)):
            #        #print "path: ", path[i]["ID"]
            #        files    = path[i]["ID"]
            #        filetype = path[i]["Type"]
            #        fcontent = path[i]["Value"]
            #        fileId   = self.CreateGetDBFileEntry(tcrid, files, filetype, fcontent)
            #        res      = res + [fileId]
            #        if fileId>0:
            #            val = str(tcrid) +","+str(labelid)+",'',"+str(fileId)
            #            sql = "INSERT INTO [SQS].[TestCasesResultFiles] (tcrid,labelid,path,fileId) VALUES ("+val+");"
            #            self.SQLStatement(sql)

            for l in cfg.getTestLogFiles(tcres):
                files    = l['ID']
                filetype = l['Type']
                fcontent = l['Value']
                fileId   = self.CreateGetDBFileEntry(tcrid, files, filetype, fcontent)
                res      = res + [fileId]
                if fileId > 0:
                    val = str(tcrid) +","+str(labelid)+",'',"+str(fileId)
                    sql = "INSERT INTO [SQS].[TestCasesResultFiles] (tcrid,labelid,path,fileId) VALUES ("+val+");"
                    self.SQLStatement(sql)

            #
            ###

            return res
        else:
            debug("Skipping Adding Test Cases Result Files",1,"SQSDB")
            debug(str(tcrid)+" "+str(path),1,"SQSDB")




    ##
    ##   Store a TestCasesResultDescription in DB if it does not exist.
    ##
    ##   Params named exactly as DB table row names.
    ##

    def AddTestCasesResultDescription(self,tcrid,filePath,name,author,changedate,version,time,descriptionValue,runTime,preparation,totalTime,software,hardware):

        if tcrid != None:

            sql = "SELECT tcrid FROM SQS.TestCasesResultDescription WHERE tcrid = "+str(tcrid)
            result = self.SQLStatementResult(sql)
            if isNullOrEmpty(result):

                # Add TestStepResult to the DB
                val =             str(tcrid) \
                      + ",'"  + dbStr(filePath) \
                      + "','" + dbStr(name) \
                      + "','" + dbStr(author) \
                      + "','" +   str(changedate) \
                      + "','" +   str(version) \
                      + "','" +   str(time) \
                      + "','" +   str(runTime) \
                      + "','" +   str(preparation) \
                      + "','" +   str(totalTime) \
                      + "','" + dbStr(software) \
                      + "','" + dbStr(hardware) \
                      + "','" + dbStr(descriptionValue) \
                      +"'"
                sql = "INSERT INTO [SQS].[TestCasesResultDescription] "+\
                      "(tcrid,filePath,name,author,changedate,version,time,runTime,preparation,totalTime,software,hardware,descriptionValue) VALUES ("+val+");"
                self.SQLStatement(sql)

        else:
            debug("Skiping Adding Test Cases Result Files",1,"SQSDB")
            # MichaelRo
            # debug(str(tcrid)+" "+str(path),1,"SQSDB")
            debug(str(tcrid)+" "+str(filePath),1,"SQSDB")



    # --------------------------------------------------------------------------
    # Add a TestStep
    #
    def AddTestStep(self,pos,tcid,type,image,logText,id,title,stopOnFail,value,wait): #@ReservedAssignment
        if tcid != None:

            val = dbStr(pos)+","+dbStr(tcid) +",'"+dbStr(type)      +"','"+dbStr(image)+"','"+dbStr(logText)+"','"
            val += dbStr(id)+"','"+dbStr(title)+"','"+dbStr(stopOnFail)+"','"+dbStr(wait)+"','"+dbStr(value)+"'"

            sql = "INSERT INTO [SQS].[TestSteps] (pos, tcid, type, image, logText, id, title, stopOnFail, wait, value) VALUES ("+val+");"

            self.SQLStatement(sql)

        else:
            debug("Skiping Adding Test Step",1,"SQSDB")
            debug(type+" "+id+" "+title,1,"SQSDB")





    ##
    ##   Store a TestStepsResults item in DB.
    ##
    ##   Fixed TestStepsResults rd_comment "".
    ##
    ##   @param pos          DB TestStepsResults pos - test step number from 1 ..
    ##   @param tcrid        DB TestStepsResults tcrid, debug error msg without action if None.
    ##   @param tcid         DB TestStepsResults tcid.
    ##   @param ts_pos       DB TestStepsResults ts_pos.
    ##   @param logText      DB TestStepsResults logtext.
    ##   @param result       DB TestStepsResults result AND cor_result,
    ##                       WRV: -2, -1 'No Result', 0 'OK', 1 'Fail', 2 'Crash', 3 'Exception', 4 'Blocked',
    ##                       or "" for no test step mapped here to WRV -2
    ##   @param id           DB TestStepsResults id.
    ##   @param time         DB TestStepsResults time.
    ##   @param comment      DB TestStepsResults comment.
    ##   @param tcb          DB TestStepsResults traceback.
    ##   @param g_comment    DB TestStepsResults g_comment, default "".
    ##   @param tc_comment   DB TestStepsResults tc_comment, default "".
    ##   @param type         DB TestStepsResults type, default "".
    ##   @param stepValue    DB TestStepsResults stepValue, default "".
    ##

    def AddTestStepResult(self,pos,tcrid,tcid,ts_pos,logText,result,id,time,comment,tcb,g_comment="",tc_comment="",type="",stepValue=""):   #@ReservedAssignment

        #INSERT INTO
        #  SQS.TestStepsResults
        #(
        #  pos,
        #  tcrid,
        #  tcid,
        #  ts_pos,
        #  logText,
        #  [result],
        #  cor_result,
        #  id,
        #  [time],
        #  comment,
        #  rd_comment,
        #  tc_comment,
        #  g_comment,
        #  traceback,
        #  [state]
        #  stepValue,
        #  [type]
        #)


        if tcrid != None:

            # Statements have the result -2 (CRTITA result "" (no test) -> WRV result -2 = 'NoValue' / 'No Result')
            if result == "":
                result = -2

            # Add TestStepResult to the DB
            val =             str(pos) \
                  + ","   +   str(tcrid) \
                  + ","   +   str(ts_pos) \
                  + ","   +   str(tcid) \
                  + ",'"  + dbStr(logText) \
                  + "',"  +   str(result) \
                  + ","   +   str(result) \
                  + ",'"  + dbStr(id) \
                  + "','" + dbStr(time) \
                  + "','" + dbStr(comment) \
                  + "','" + dbStr(tcb) \
                  + "','" + dbStr(g_comment) \
                  + "','" + dbStr(tc_comment) \
                  + "','" + dbStr(type) \
                  + "','" + dbStr(stepValue) \
                  + "',"  + "''"

            sql = "INSERT INTO [SQS].[TestStepsResults] (pos, tcrid, ts_pos, tcid, logText, result, cor_result, id, time, comment, traceback, g_comment, tc_comment, type, stepValue, rd_comment) VALUES ("+val+");"
            self.SQLStatement(sql)

        else:
            debug("Skipping Adding Test Step Result",1,"SQSDB")
            debug("Pos: "+str(pos)+" "+str(tcrid)+" "+logText,1,"SQSDB")





    ##
    ##   Store a TLIDName item in DB.
    ##
    ##   UpdateTime and Status are left empty ('').
    ##
    ##   @param  PrTcId
    ##   @param  id1
    ##   @param  id2
    ##   @param  leaf
    ##   @param  name
    ##   @param  path
    ##

    def AddTLIDName(self,PrTcId,id1,id2,leaf,name,path):


        #INSERT INTO
        #  SQS.TLIDName
        #(
        #  prtcid,
        #  tlid1,
        #  tlid2,
        #  leaf,
        #  [path],
        #  [name],
        #  UpdateTime,
        #  [Status],
        #  invisible,
        #  setStatus
        #)
        #VALUES (
        #  :prtcid,
        #  :tlid1,
        #  :tlid2,
        #  :leaf,
        #  :path,
        #  :name,
        #  :UpdateTime,
        #  :Status,
        #  :invisible,
        #  :setStatus
        #);

        val = str(PrTcId)+","+str(id1)+","+str(id2)+","+str(leaf)+",'"+dbStr(name)+"','','','"+path+"'"
        sql = "INSERT INTO [SQS].[TLIDName] (prtcid, tlid1, tlid2, leaf, name, UpdateTime, Status, path) VALUES ("+val+");"

        self.SQLStatement(sql)





    ##
    ##   Check wether a TLIDName item is a leaf.
    ##
    ##   @param    path
    ##
    ##   @return   False if path not found or leaf in found entry is False.
    ##

    def CheckTLIDNameIsLeaf(self,path):

        ##INSERT INTO [SQS].[SQS_CalDesk].[SQS].[TLIDName]
        ##           ([prtcid]
        ##           ,[tlid1]
        ##           ,[tlid2]
        ##           ,[leaf]
        ##           ,[path]
        ##           ,[name]
        ##           ,[UpdateTime]
        ##           ,[Status]
        ##           ,[invisible]
        ##           ,[setStatus])
        ##     VALUES
        ##           (<prtcid, int,>
        ##           ,<tlid1, int,>
        ##           ,<tlid2, int,>
        ##           ,<leaf, bit,>
        ##           ,<path, nvarchar(255),>
        ##           ,<name, nvarchar(50),>
        ##           ,<UpdateTime, nvarchar(50),>
        ##           ,<Status, nvarchar(255),>
        ##           ,<invisible, bit,>
        ##           ,<setStatus, bit,>)
        ##GO
        ##

        ##SELECT[prtcid]
        ##      ,[tlid1]
        ##      ,[tlid2]
        ##      ,[leaf]
        ##      ,[path]
        ##      ,[name]
        ##      ,[UpdateTime]
        ##      ,[Status]
        ##      ,[invisible]
        ##      ,[setStatus]
        ##  FROM [SQS_ConfigDesk].[SQS].[TLIDName]

        leaf = False
        sql = "SELECT leaf from [SQS].[TLIDName] where path = '"+path+"';"
        try:
            result = self.SQLStatementResult(sql)
            if not isNullOrEmpty(result):
                leaf = result[0][0]
        except:
            pass
        return leaf





    ##
    ##   Create TLIDName item(s) from path and add it to TLIDName table in DB if full path not exist in DB.
    ##
    ##   Append / if no trailing / found. If path is found in the DB, do nothing.
    ##   Else find the first part of path which is not in the DB.
    ##   From this insert each path part up to the full path.
    ##   For all path parts set leaf = 0, for full path set leaf = 1.
    ##   Set UpdateTime = '', 'Status' = '', invisible = False, setStatus = False.
    ##
    ##   @remark  Called only from ImportData() in SQS_TR2DB.py.
    ##
    ##   @param   path  Path with leading /.
    ##

    def checkAddTLIDNameByPath(self,path):

        if path[-1:] != "/":                                                   # append / if entry does not end with /
            path += "/"

        prtcid,tlid1,tlid2 = self.getTLIDbyPath(path)                          # path already in DB? @UnusedVariable
        if prtcid == -1:                                                       # no:
            subElements = string.split(path[len(self.prePath):-1],"/")         # path elements without leading/trailing /
            level = 0
            minPath = self.prePath+subElements[level]+"/"

            while self.getTLIDbyPath(minPath)!=(-1,-1,-1) and level<len(subElements)-1:  # while part of path found in DB ...
                level += 1
                minPath+=subElements[level]+"/"

            # INSERT each path part not in DB into DB
            minPath = minPath[:string.rfind(minPath[:-1],"/")+1]               # base path, i.e. minPath = os.path.dirname(minPath[:-1])
            for se in subElements[level:]:                                     # for all path elements not in DB ...
                if minPath + se + "/" == path:                                 # if last element to process = full path reached, then it is a leaf entry
                    leaf = 1
                else:
                    leaf = 0

                self.getNewTLID(minPath,se,level,leaf)                         # INSERT in DB
                minPath += se + "/"                                            # add next path element





    ##
    ##   Insert or update test label in table LabelIDNames in DB.
    ##
    ##   @param   sslabel    Internal data base label, similiar displabel, max 50 chars are used.
    ##   @param   displabel  WRV displayed label, max 50 chars are used.
    ##   @param   date       New date ("23/09/11 15:24:38"), default = ''.
    ##
    ##   @return  labelid    ID of the label in DB.
    ##

    def createGetLabelID(self,sslabel,displabel,date=""):

        self.SQLStatement("SELECT max(labelid) FROM [SQS].[LabelIDNames] where sslabel = '"+dbStr(sslabel)[:50]+"';",False)

        result = self.cur.fetchall()
        if isNullOrEmpty(result):
            labelid = None
        else:
            labelid = result[0][0]

        if labelid == None:
            self.SQLStatement("SELECT max(labelid) FROM [SQS].[LabelIDNames];",False)

            result = self.cur.fetchall()
            if isNullOrEmpty(result):
                labelid = 1
            else:
                labelid = result[0][0]+1

            #
            # Store the Label ID into the DB
            #
            val = str(labelid)+",'"+dbStr(sslabel)[:50]+"'"+",'"+dbStr(displabel)[:50]+"',0,'"+str(date)+"'"
            sql = "INSERT INTO [SQS].[LabelIDNames] (labelid, sslabel,display_label,OfficialLabel,date) VALUES ("+val+");"

            self.SQLStatement(sql)
            debug("New Label: Label='"+dbStr(sslabel)[:50]+"'New Date = "+str(date),0,"SQSDB")
        else:
            if date != "":
                self.SQLStatement("SELECT date FROM [SQS].[LabelIDNames] where labelid = "+str(labelid)+";",False)

                result = self.cur.fetchall()
                try:
                    if isNullOrEmpty(result):
                        labelidDate = ""
                    else:
                        labelidDate = result[0][0]

                    if date > 0:
                        if str(date) < str(labelidDate) or str(labelidDate) == "":
                            sql = "UPDATE [SQS].[LabelIDNames] "+\
                                  "SET date = '"+str(date)+"' "+\
                                  "WHERE labelid = '"+str(labelid)+"';"

                            debug("Update: New Date:"+str(date)+", Old Date:"+str(labelidDate),0,"SQSDB")

                            self.SQLStatement(sql)
                        else:
                            debug("No Update: New Date:"+str(date)+", Old Date:"+str(labelidDate),0,"SQSDB")
                    else:
                        debug("No Update: New Date = "+str(date),0,"SQSDB")
                except:
                    debug("Exception Updating Label Date: labelid = "+str(labelid),1,"SQSDB")
        return labelid





    ##
    ##   Create a Group ID or get it if group already exists.
    ##
    ##   @param   source         Path (not yet used) or ID (prtcid,tlid1,tlid2) in TLIDName table.
    ##   @param   testGroupName  Name of the group (normally one dir from path to test script), trailing "/" is ignored
    ##
    ##   @return  Test group ID or None on errors.
    ##

    def createGetTestGroupID(self, source, testGroupName):

        # get prtcid, tlid1, tlid2
        if type(source) != type([]):
            #print "createGetTestGroupID",source
            prtcid,tlid1,tlid2 = self.getTLIDbyPath(source)
        else:
            (prtcid, tlid1, tlid2) = source


        if prtcid != -1:

            if testGroupName!="" and testGroupName[-1] == "/":    # strip trailing "/"
                testGroupName = testGroupName[:-1]

            # find TestGroups entry with given TLIDName ID and group name
            where = "prtcid="+str(prtcid)+"and tlid1 ="+str(tlid1)+"and tlid2="+str(tlid2)+" and name = '"+testGroupName+"'"
            sql = "SELECT tgid FROM [SQS].[TestGroups] where "+where+";"
            self.SQLStatement(sql,False)

            result = self.cur.fetchall()

            if not isNullOrEmpty(result):

                # Group found in DB, all done.
                tgid = result[0][0]

            else:

                # Group not found in DB, create new TestGroups entry with group ID = max existing group id + 1.

                self.SQLStatement("SELECT max(tgid) FROM [SQS].[TestGroups];",False)
                result = self.cur.fetchall()
                if isNullOrEmpty(result):
                    tgid = 1
                else:
                    tgid = result[0][0] + 1

                val = str(prtcid)+","+str(tlid1)+","+str(tlid2)+","+str(tgid)+",'"+dbStr(testGroupName)+"'"
                sql = "INSERT INTO [SQS].[TestGroups] (prtcid, tlid1, tlid2,tgid, name) VALUES ("+val+");"

                self.SQLStatement(sql)

        else:   # if source parm given as path and path not found in DB
            debug("Exception Finding Test Group Path:",1,"SQSDB")
            debug(source,1,"SQSDB")

            tgid = None

        return tgid





    ##
    ##   Create new TLIDName entry.
    ##
    ##   @remark  Called only from checkAddTLIDNameByPath()
    ##
    ##   @TODO Avoiding of int overflow in high byte of prtcidid, tlid1, tlid2 (SQL statements and checks).
    ##
    ##   @param  path         /dir/../dir/.
    ##   @param  newElement   new element to join with path.
    ##   @param  level        (not used)
    ##   @param  leaf         1: path + newElement = full path, no more elements to follow, else 0.
    ##
    ##
    ##
    ##   ---------------------------------------------------------------------
    ##
    ##
    ##
    ##   path:
    ##
    ##     Relative (part of) path for WRV hierarchy View. No real path.
    ##     Minimal number of elements in leafs (leaf = 1) have to be 3.
    ##     Each (part of) path is stored in DB only once and has leading and trailing /.
    ##     To be inserted in DB: Full path and each part of path from /<firstelement>/.
    ##     Example:
    ##
    ##        "/ConfigurationDesk_IMPL/"                (leaf = 0)
    ##        "/ConfigurationDesk_IMPL/FcnTst/"         (leaf = 0)
    ##        "/ConfigurationDesk_IMPL/FcnTst/CmnCfg/"  (leaf = 1)
    ##
    ##     Here: path = /<PRODUCTNAME>/, <PRODUCTNAME> from _Conf.txt, + Key for TestResult[] from
    ##     critita_result without <at-dir>\<testscript name>, all "\" changed to "/", + "/".
    ##     Wenn weniger als 2 Elemente, <testgroup> dupliziert.
    ##
    ##
    ##
    ##   prtcid, tlid1, tlid2:
    ##
    ##     prtcid           PRoject TopiC ID    Level 1,2        Bytes 3..1,0
    ##     tlid1            Topic Level ID 1    Level 3,4,5,6    Bytes 3,2,1,0
    ##     tlid2            Topic Level ID 2    Level 7,8,9,10   Bytes 3,2,1,0
    ##
    ##     For each (part of)"path" to a test script an ID  prtcid | tlid1 | tlid2 is generated,
    ##     which allow simple select of underlying sub paths:
    ##
    ##     prtcid    tlid1       tlid2
    ##     +-------+ +---------+ +---------+
    ##     3 2 1  0  3  2  1  0  3  2  1  0   byte
    ##     000008 02 04 02 02 01 03 00 00 00  hex (example)
    ##          1  2  3  4  5  6  7  8  9 10  level
    ##
    ##     level:
    ##
    ##                   1              2         3           4        ...
    ##       /ConfigurationDesk_IMPL/CmpTst/MdlEnvAdapter/Simulink/    ...
    ##
    ##     For each level the associated "counter" ist incremented. Example:
    ##
    ##       00000217 00000000 00000000  /FRCP/031_static_mux_pdu/
    ##       00000217 01000000 00000000  /FRCP/031_static_mux_pdu/Test001/
    ##       00000217 02000000 00000000  /FRCP/031_static_mux_pdu/Test003/
    ##       00000217 03000000 00000000  /FRCP/031_static_mux_pdu/Test004/
    ##       00000300 00000000 00000000  /RTC/
    ##       00000301 00000000 00000000  /RTC/10_BaseServices/
    ##       00000301 01000000 00000000  /RTC/10_BaseServices/Libraries/
    ##       00000301 01010000 00000000  /RTC/10_BaseServices/Libraries/DsAperiodicTimer/
    ##       00000301 01020000 00000000  /RTC/10_BaseServices/Libraries/DsBoardStatus/
    ##       00000301 01030000 00000000  /RTC/10_BaseServices/Libraries/DsIntervalTimer/
    ##

    def getNewTLID(self,path,newElement,level,leaf):

        prtcid,tlid1,tlid2 = self.getTLIDbyPath(path)

        debug( "Path       :"+str(path+newElement)+"/",0,"SQSDB")
        debug( "newElement :"+str(newElement),0,"SQSDB")
        debug( "Level      :"+str(level)+"  Level Neu  :"+str(len(string.split(path,"/"))- 1),0,"SQSDB")
        debug( "Leaf       :"+str(leaf),0,"SQSDB")
        debug( "Basis      :"+hex16(prtcid)+" "+hex16(tlid1)+" "+hex16(tlid2),0,"SQSDB")

        level = len(string.split(path,"/")) - 1            # #elements in path with newElement added, / = 1, /dir/ = 2, /dir1/dir2/ = 3, ...

        if level == 1:

                result = self.SQLStatementResult("SELECT max(prtcid) FROM [SQS].[TLIDName];")
                #print result

                try:
                    if isNullOrEmpty(result):
                        prtcid = 256
                    else:
                        if result[0][0] != -1:
                            prtcid = ((result[0][0]/256)+1)*256       # new prtcid = oldprtcid + 1 (without level 2)
                        else:
                            prtcid = 256
                except:
                    debug("Exception getting max prtcid",0,"SQSDB")
                    prtcid = 256

                debug("New prtcid="+str(prtcid),0,"SQSDB")

                #self.AddTLIDPath(prtcid,0,0,path+newElement+"/")
                self.AddTLIDName(prtcid,0,0,leaf,newElement,path+newElement+"/")

                debug("Adding new prtcid Level 1 ("+path+newElement+"/) ",0,"SQSDB")



        elif level == 2:

                prtcidOld = self.SQLStatementResult("SELECT max(prtcid) FROM [SQS].[TLIDName] "+\
                                                    "where prtcid>"+str(prtcid)+"and prtcid<"+str(prtcid+256)+";")[0][0]

                # If there are Subitems add one to the highest tlid1 else generate a new tlid1
                if prtcidOld!=None:
                    prtcidNew = prtcidOld + 1
                else:
                    # Create an new tlid1 for a subitem
                    prtcidNew = prtcid + 1

                #self.AddTLIDPath(prtcidNew,0,0,path+newElement+"/")
                self.AddTLIDName(prtcidNew,0,0,leaf,newElement,path+newElement+"/")

                debug("Adding new prtcid Level 2 ("+path+newElement+"/) ",0,"SQSDB")



        elif level < 7:

            try:
                i = 6 - level
                tlid1Max = self.SQLStatementResult("SELECT max(tlid1) FROM [SQS].[TLIDName] "+\
                                                   "where tlid1>"+str(tlid1)+"and tlid1 < "+str(tlid1+256**(i+1))+\
                                                   "and prtcid="+str(prtcid)+";")[0][0]


                # If there are Subitems add one to the highest tlid1 else generate a new tlid1
                if tlid1Max!=None:
                    tlid1Max = int(tlid1Max/256**i)*256**i # Clear of unused Bytes
                    tlid1New = tlid1Max + (256**i)
                else:
                    # Create an new tlid1 for a subitem
                    tlid1New = tlid1 + (256**i)
                    tlid1Max  = 0

                try:
                    debug( "New TLID   :"+hex16(prtcid)+" "+hex16(tlid1New)+" "+hex16(tlid2),0,"SQSDB")
                except:
                    pass

                self.AddTLIDName(prtcid,tlid1New,tlid2,leaf,newElement,path+newElement+"/")


                debug("Adding new tlid 1 ("+path+newElement+"/) ",0,"SQSDB")
            except:
                debug("Error Adding new tlid 1 ("+path+newElement+"/) ",1,"SQSDB")



        elif level < 11:

            try:
                i = 10 - level
                tlid2Max = self.SQLStatementResult("SELECT max(tlid2) FROM [SQS].[TLIDName] "+\
                                                   "where tlid2>"+str(tlid2)+"and tlid2 < "+str(tlid2+256**(i+1))+\
                                                   "and prtcid="+str(prtcid)+"and tlid1 = "+str(tlid1)+";")[0][0]


                # If there are Subitems add one to the highest tlid1 else generate a new tlid1
                if tlid2Max!=None:
                    tlid2Max = int(tlid2Max/256**i)*256**i # Clear of unused Bytes
                    tlid2New = tlid2Max + (256**i)
                else:
                    # Create an new tlid1 for a subitem
                    tlid2New = tlid2 + (256**i)
                    tlid2Max  = 0

                try:
                    debug( "New TLID   :"+hex16(prtcid)+" "+hex16(tlid1)+" "+hex16(tlid2New),0,"SQSDB")
                except:
                    pass

                self.AddTLIDName(prtcid,tlid1,tlid2New,leaf,newElement,path+newElement+"/")
                debug("Adding new tlid 2 ("+path+newElement+"/) ",0,"SQSDB")
            except:
                debug("Error Adding new tlid 2 ("+path+newElement+"/) ",1,"SQSDB")



        else:

            debug("Unsupported Level Error adding new tlid  ("+path+newElement+"/)  ",1,"SQSDB")





    ##
    ##   Get file ID from TestCasesResultDBFiles table in DB.
    ##
    ##   @param   tcrid  Test case result ID.
    ##   @param   fname  Path and file name for a file in TestCasesResultDBFiles table.
    ##
    ##   @return  (fileId,True) if fname found in DB, else (<max fileid + 1 from DB>,False).
    ##

    def GetMaxFromDBFiles(self, tcrid, fname):

        sql = "SELECT fileId FROM [SQS].[TestCasesResultDBFiles] WHERE (tcrid = "+str(tcrid) + ") AND (fileNameOrig = '"+fname+"')"

        res = self.SQLStatementResult(sql)
        if not isNullOrEmpty(res):
            return res[0][0],True
        else:
            sql = "SELECT MAX(fileId) FROM [SQS].[TestCasesResultDBFiles]"
            res = self.SQLStatementResult(sql)
            if not isNullOrEmpty(res):
                return res[0][0]+1,False
            else:
                return 1,False




    def GetMaxFromFiles(self, tcrid, fname):
        sql = "SELECT fileId FROM [SQS].[files] WHERE (tcrid = "+str(tcrid) + ") AND (fpath = '"+fname+"')"
        res = self.SQLStatementResult(sql)
        if not isNullOrEmpty(res):
            return res[0][0],True
        else:
            sql = "SELECT MAX(fileId) FROM [SQS].[files]"
            res = self.SQLStatementResult(sql)
            if not isNullOrEmpty(res):
                return res[0][0]+1,False
            else:
                return 1,False

    #---------------------------------------------------------------------------
    # get TLID by tcomprid
    #
    def getTLIDbyTCOMPRID(self,tcomprid):
        sql = "SELECT prtcid, tlid1, tlid2 FROM [SQS].[TestComponentsResults] where tcomprid = '"+str(tcomprid)+"';"

        self.SQLStatement(sql,False)

        prtcid = -1
        tlid1 = -1
        tlid2 = -1

        try:
            result = self.cur.fetchall()

            if not isNullOrEmpty(result):
                prtcid = result[0][0]
                tlid1 = result[0][1]
                tlid2 = result[0][2]
        except:
            pass

        #print "getTLIDbyPath",sourcePath,"=>",prtcid,tlid1,tlid2
        return prtcid,tlid1,tlid2





    ##
    ##   Get TLID prtcid,tlid1,tlid2 by path.
    ##
    ##   @param    sourcePath  Path which has to match the path column in TLIDName table.
    ##
    ##   @return   prtcid,tlid1,tlid2 of the TLIDName entry with found path, else -1,-1,-1.
    ##

    def getTLIDbyPath(self,sourcePath):

        sql = "SELECT prtcid, tlid1, tlid2 FROM [SQS].[TLIDName] where path = '"+sourcePath+"';"
        self.SQLStatement(sql,False)

        prtcid = -1
        tlid1 = -1
        tlid2 = -1

        try:
            result = self.cur.fetchall()

            if not isNullOrEmpty(result):
                prtcid = result[0][0]
                tlid1 = result[0][1]
                tlid2 = result[0][2]
        except:
            pass

        #print "getTLIDbyPath",sourcePath,"=>",prtcid,tlid1,tlid2
        return prtcid,tlid1,tlid2





    # --------------------------------------------------------------------------
    # Get the highest SourceSafe Version of a TestCase
    #

    # Return none if TestCase not found, else highest ssver

    def GetTestCaseSSversion(self,tcnid):
        self.SQLStatement("SELECT max(ssver) FROM [SQS].[TestCases] where tcnid="+str(tcnid)+";",False)

        result = self.cur.fetchall()
        if not isNullOrEmpty(result):
            return result[0][0]
        else:
            return -1



    # --------------------------------------------------------------------------
    # Get the highest SourceSafe Version of a TestCaseResult
    #

    # Return none if TestCaseResult not found, else highest ssver

    def GetTestCaseResultSSversion(self,tcnid,oswt):
        self.SQLStatement("SELECT max(ssver) FROM [SQS].[TestCasesResults] where tcnid="+str(tcnid)+" and os ='"+str(oswt)+"';",False)

        result = self.cur.fetchall()
        if not isNullOrEmpty(result):
            return result[0][0]
        else:
            return -1




    # --------------------------------------------------------------------------
    # Get all Labels of a TestCaseResult
    #

    # Return none if TestCaseResult not found, else highest ssver

    ##   @remark Not used.

    def GetTestCaseResultLabels(self,tcnid,oswt):
        self.SQLStatement("SELECT sslabel FROM [SQS].[LabelIDNames],[SQS].[TestComponentsResults],[SQS].[TestGroupsResults],[SQS].[TestCasesResults] "
               "where [SQS].[TestCasesResults].tcnid="+str(tcnid)+" and [SQS].[TestCasesResults].os ='"+str(oswt)+"' "
               "and [SQS].[TestCasesResults].tgrid = [SQS].[TestGroupsResults].tgrid "
               "and [SQS].[TestComponentsResults].tcomprid = [SQS].[TestGroupsResults].tcomprid "
               "and [SQS].[LabelIDNames].labelid = [SQS].[TestComponentsResults[.labelid;",False)

        result = self.cur.fetchall()
        return result

    # --------------------------------------------------------------------------
    # Find a TestGroup
    #

    def GetTestGroup(self,prtcid,tlid1,tlid2,tgName):
        result = self.SQLStatementResult("SELECT tgid FROM [SQS].[TestGroups] where prtcid="+str(prtcid)+
                                                                    " and tlid1='"+str(tlid1)+"'"+
                                                                    " and tlid2='"+str(tlid2)+"'"+
                                                                    " and name='"+str(tgName)+"';")

        if not isNullOrEmpty(result):
            if len(result) > 1:
                debug("FindTestGroup tgName="+str(tgName)+": Double Items -"+str(result),1,"SQSDB",True)

            tgid = result[-1][0]
        else:
            tgid = -1

        return tgid



    # --------------------------------------------------------------------------
    # Find a TestGroupResult
    #
    def GetTestGroupsResultID(self,tcomprid,tgid):
        result = self.SQLStatementResult("SELECT tgrid FROM [SQS].[TestGroupsResults] where tcomprid="+str(tcomprid)+
                                                                    " and tgid='"+str(tgid)+"';")

        if not isNullOrEmpty(result):
            tgrid = result[-1][0]
        else:
            tgrid = -1

        return tgrid


    # --------------------------------------------------------------------------
    # Find a TestCaseResultID by TGRID
    #
    def GetTestCasesResultIDByTGRID(self,tgrid,tcnid):
        result = self.SQLStatementResult("SELECT tcrid FROM [SQS].[TestCasesResults] where tcnid="+str(tcnid)+
                                                                    " and tgrid='"+str(tgrid)+"';")

        if not isNullOrEmpty(result):
            tcrid = result[-1][0]
        else:
            tcrid = -1

        return tcrid


    # --------------------------------------------------------------------------
    # Find a TestCase Name
    #
    def GetTestCasesNameIdByName(self,tgid,tcName):
        result = self.SQLStatementResult("SELECT tcnid FROM [SQS].[TestCasesName] where tgid="+str(tgid)+
                                                                          " and name='"+dbStr(tcName)[:255]+"';")

        if not isNullOrEmpty(result):
            if len(result) > 1:
                debug("GetTestCasesNameIdByName tcName="+dbStr(tcName)+": Double Items -"+str(result),1,"SQSDB",True)

            tcnid = result[-1][0]
        else:
            tcnid = -1

        return tcnid


    # --------------------------------------------------------------------------
    # Find all TestCase Names of a group
    #
    def GetTestCasesNamesForGroupId(self,tgid):
        result = self.SQLStatementResult("SELECT tcnid, name FROM [SQS].[TestCasesName] where tgid="+str(tgid)+";")

        if not isNullOrEmpty(result):
            tcnidList = result
        else:
            tcnidList = None

        return tcnidList

    # --------------------------------------------------------------------------
    # Find a TestCase by TCNID
    #

    def GetTestCaseByTCNID(self,tcnid):
        result =self.SQLStatementResult("SELECT TCID FROM [SQS].[TestCases] where tcnid="+str(tcnid)+";")

        if not isNullOrEmpty(result):
            tcid = result[-1][0]
        else:
            tcid = -1

        return tcid

    # --------------------------------------------------------------------------
    # Find a TestCase
    #

    def GetTestCase(self,tcnid,date,version):
        # SELECT* uses Unicode Problems
        #self.SQLStatement("SELECT* from TestCases where tcnid="+str(tcnid)+" and date='"+str(date)+"' and version='"+str(version)+"';",False)
        #result = self.cur.fetchall()

        result =self.SQLStatementResult("SELECT TCID FROM [SQS].[TestCases] where tcnid="+str(tcnid)+
                                                                    " and date='"+str(date)+"'"+
                                                                    " and version='"+str(version)+"';")

        if not isNullOrEmpty(result):
            if len(result) > 1:
                debug("FindTestCases tcnid="+str(tcnid)+": Double Items -"+str(result),1,"SQSDB",True)

            #print result

            tcid = result[-1][0]
        else:
            tcid = -1

        return tcid




    # --------------------------------------------------------------------------
    # Get Highest Date of Test Component Result
    #

    def getTestComponentResultMaxDate(self,prtcid,tlid1,tlid2):

        self.SQLStatement("SELECT max(date) FROM [SQS].[TestComponentsResults] where "+\
                          "prtcid="+str(prtcid)+" and tlid1="+str(tlid1)+" and tlid2="+str(tlid2)+";",False)

        result = self.cur.fetchall()

        if type(result) == type([]):
            try:
                ret = float(result[0][0])
            except:
                ret = None
        else:
            ret = None

        return ret



    # --------------------------------------------------------------------------
    # Get Test Component Result
    #

    def GetTestComponentResultID(self,tgid,labelid,oswt,path="",date=""):
        """ You can use a tgid or you can pass (prtcid, tlid1, tlid2) to be faster """

        (prtcid, tlid1, tlid2) = tgid

        #
        # Create a new tcid
        #

        # MichaelRo
        # GetTestComponentID = None

        self.SQLStatement("SELECT tcomprid FROM [SQS].[TestComponentsResults] where "+\
                          "prtcid="+str(prtcid)+" and tlid1="+str(tlid1)+" and tlid2="+str(tlid2)+\
                          " and labelid="+str(labelid)+" and os='"+str(oswt)+"';",False)
        result = self.cur.fetchall()

        if isNullOrEmpty(result):
            ret = None
        else:
            #print result
            ret = result[0][0]

        return ret


    # --------------------------------------------------------------------------
    # Create an Entry in Blob-Table
    #
    ##
    ##   @param   tcrid
    ##   @param   fname
    ##   @param   ftype
    ##   @param   fontent
    ##
    ##   @return  File ID or -1 on errors.
    ##

    def CreateGetDBFileEntry(self, tcrid, fname, ftype, fcontent):
        # ------------- Neue Version -----------------------#
##        if tcrid != None:
##            filename = fname
##            content  = dbStr(fcontent)
##            size     = len(content)
##            f        = open(filename,"w")
##            f.write(fcontent)
##            f.close()
##            newId, update = self.GetMaxFromFiles(tcrid, fname)
##            if update == False:
##                # FileImport.exe <tcrid> <ssPath> <filename>
##                importprogram = "FileImport.exe"
##                parameters    = [str(tcrid), fname, filename]
##                res = os.system("start /wait " + importprogram + " " + " ".join(parameters))
##                if res != 0:
##                    newId = -1
##                    debug("Error writing BLOB: "+cmd,1,"SQSDB")
##                os.remove(fname)
##            return newId

        # ------------- Alte Version -----------------------#
        if tcrid != None:
            content = dbStr(fcontent)
            size = len(content)
            newId, update = self.GetMaxFromDBFiles(tcrid,fname)   # update True if file already in DB, else False

            # MichaelRo, not used
            # fieldname = "fileContent"

            if (ftype == "LinkToTextFile"):
                ftype = "Text"
            if (size > 8000000) or (size == 0):
                return -1
            if update == False:
                val = str(newId) + "," +str(tcrid)+",'"+dbStr(ftype) + "'," + str(size)+",'"+dbStr(fname)+"','"+content+"',0"
                sql = "INSERT INTO [SQS].[TestCasesResultDBFiles] (fileId, tcrid, fileType, fileSize, fileNameOrig, fileContent, fileContentBig) VALUES (" + val + ");"
            else:
                sql = "UPDATE [SQS].[TestCasesResultDBFiles] SET fileContent= '"+dbStr(content)+"' WHERE fileId="+str(newId)+";"
            try:
                self.SQLStatement(sql)
            except:
                newId = -1

                # MichaelRo, no cmd, must be sql
                # debug("Error writing BLOB: "+cmd,1,"SQSDB")
                debug("Error writing BLOB: "+sql,1,"SQSDB")

            return newId





    # --------------------------------------------------------------------------
    # Get Test Component Result
    #
    def createGetTestComponentResultID(self,tgid,labelid,oswt,path="",date=""):
        """ You can use a tgid or you can pass (prtcid, tlid1, tlid2) to be faster """

        if type(tgid) != type([]):
            if tgid != "":
                result = self.SQLStatement("SELECT prtcid, tlid1, tlid2 FROM [SQS].[TestGroups] where tgid = "+str(tgid)+";",False)
            elif tgid == "":
                self.SQLStatement("SELECT prtcid,tlid1,tlid2 FROM [SQS].[TLIDName] where path = '"+path+"';",False)

            result = self.cur.fetchall()
            (prtcid, tlid1, tlid2) = result[0]
        else:
            (prtcid, tlid1, tlid2) = tgid


        #
        # Create a new tcid
        #

        GetTestComponentID = None

        self.SQLStatement("SELECT tcomprid FROM [SQS].[TestComponentsResults] where "+\
                          "prtcid="+str(prtcid)+" and tlid1="+str(tlid1)+" and tlid2="+str(tlid2)+\
                          " and labelid="+str(labelid)+" and os='"+str(oswt)+"';",False)
        result = self.cur.fetchall()



        if result == []:
            # Try to find the OS if it is empty (For old test cases only!)
            if oswt == "":
                self.SQLStatement("SELECT tcomprid FROM [SQS].[TestComponentsResults] where "+\
                          "prtcid="+str(prtcid)+" and tlid1="+str(tlid1)+" and tlid2="+str(tlid2)+\
                          " and labelid="+str(labelid)+";",False)
                result = self.cur.fetchall()

        if result == []:
            self.SQLStatement("SELECT max(tcomprid) FROM [SQS].[TestComponentsResults];",False)

            result = self.cur.fetchall()
            GetTestComponentID = result[0][0]

            if GetTestComponentID == None:
                GetTestComponentID = 1
            else:
                GetTestComponentID += 1

            #
            # Store the Label ID into the DB
            #

            val = str(GetTestComponentID)+","+str(prtcid)+","+str(tlid1)+","+str(tlid2)+","+dbStr(labelid)+",'"+dbStr(oswt)+\
                  "',0,0,0,0,0,0,0,0 ,0,0,0,0,0,0,0,0 ,0,0,0,0,0,0,0,0 ,'','','"+str(date)+\
                  "','','','','','','','','','','','',''"
            sql = "INSERT INTO [SQS].[TestComponentsResults] "+\
                  "(tcomprid, prtcid, tlid1, tlid2, labelid, os,"+\
                   "tg_ok,cor_tg_ok,tg_fail,cor_tg_fail,tg_crash,cor_tg_crash,tg_no,cor_tg_no,"+\
                   "tc_ok,cor_tc_ok,tc_fail,cor_tc_fail,tc_crash,cor_tc_crash,tc_no,cor_tc_no,"+\
                   "ts_ok,cor_ts_ok,ts_fail,cor_ts_fail,ts_crash,cor_ts_crash,ts_no,cor_ts_no,"+\
                   "comment,rd_comment,date,ShortTestPCDesc,OSWhileTestExec,WhoExecTest,"+\
                   "TestCandidateVersion,TestCandidateBuildType,TestCandidateBuildNumber,"+\
                   "TestCandidateSpecialBuild,TestCandidateDate,PlatformWhileTestExec,"+\
                   "InterfaceToPlatform,RemarksToTestExec,StatusOfTestExec)"+\
                  "VALUES ("+val+");"

            self.SQLStatement(sql)
        else:
            GetTestComponentID = result[0][0]

        return GetTestComponentID



    # --------------------------------------------------------------------------
    # Add a TestCaseResult by tcnid, label and oswt
    #

    ##
    ##
    ##

    def createGetTestGroupResultID(self,tcnid,labelid,oswt):
        #
        # Create a new tcid
        #

        sql = "SELECT tgid FROM [SQS].[TestCasesName] where tcnid = "+str(tcnid)+";"

        # MichaelRo
        # result = self.SQLStatement(sql,False)
        self.SQLStatement(sql,False)

        result = self.cur.fetchall()
        if not isNullOrEmpty(result):
            tgid = result[0][0]
        else:
            tgid = -1

        tcomprid = self.createGetTestComponentResultID(tgid,labelid,oswt)

        return self.setGetTestGroupResultID(tcomprid,tgid)




    # --------------------------------------------------------------------------
    # check if a Filereference already exists
    #
    def ExistsFileRef(self, fileId, tcrid, labelid ):
        where = "labelid="+str(labelid)+" and tcrid = "+str(tcrid)+" and fileId="+str(fileId)
        sql = "SELECT count(*) FROM [SQS].[TestCasesResultFiles] where "+where+";"
        result = self.SQLStatementResult(sql)
        if not isNullOrEmpty(result):
            return (result[-1][0] > 0)
        else:
            return False


    # --------------------------------------------------------------------------
    # check if a TestStep exists
    #
    def ExistTestStep(self,pos,tcid):
        res = False

        if tcid != None:
            sql = "SELECT pos FROM [SQS].[TestSteps] where pos="+str(pos)+" and tcid="+str(tcid)+";"

            posres = self.SQLStatementResult(sql,False)
            if not isNullOrEmpty(posres):
                res = True
        else:
            res = False

        return res

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Helpfunction: Find tcid By tcrid
    #
    def FindTcidByTcrid(self,tcrid):
        sql = "SELECT tcid from [SQS].TestCasesResults, [SQS].TestCases where "+\
              "[SQS].TestCasesResults.tcnid = [SQS].TestCases.tcnid and "+\
              "[SQS].TestCasesResults.version = [SQS].TestCases.version and "+\
              "[SQS].TestCasesResults.changedate = [SQS].TestCases.date and "+\
              "[SQS].TestCasesResults.tcrid = "+str(tcrid)+" "+\
              "order by tcid"

        self.SQLStatement(sql,False)
        return self.cur.fetchall()

    # --------------------------------------------------------------------------
    # Find Test Steps By TCRID
    #
    def FindTestStepsByTCRID(self,tcrid):

        # Find the TestCase to the Result
        TestSteps = None
        try:

            result = self.FindTcidByTcrid(tcrid)

            if result != None and result != []:
                if len(result) > 1:
                    debug("FindTestCases: Double Items -"+str(result),1,"SQSDB",True)
                tcid = result[-1][0]
                TestSteps = self.FindTestStepsByTcid(tcid)
            else:
                tcid = -1

                # MichaelRo
                # ts_pos = -1

                sql = "SELECT version, changedate from [SQS].[TestCasesResults] where "+\
                      "TestCasesResults.tcrid = "+str(tcrid)+";"

                self.SQLStatement(sql,False)
                result = self.cur.fetchall()

                if not isNullOrEmpty(result):

                    # MichaelRo
                    #version = result[0][0]
                    #date    = result[0][1]

                    sql = 'SELECT [SQS].TLIDName.Path,[SQS].TestGroups.Name "tgName",[SQS].TestCasesName.Name "tcName",[SQS].TestCasesResults.tcnid from [SQS].TestGroups,[SQS].TestCasesName,[SQS].TLIDName,[SQS].TestCasesResults '+\
                          'where [SQS].TestCasesResults.tcrid = '+str(tcrid)+\
                          '  and [SQS].TestCasesResults.tcnid  = [SQS].TestCasesName.tcnid'+\
                          '  and [SQS].TestCasesName.tgid  = [SQS].TestGroups.tgid'+\
                          '  and [SQS].TestGroups.prtcid = [SQS].TLIDName.prtcid'+\
                          '  and [SQS].TestGroups.tlid1  = [SQS].TLIDName.tlid1'+\
                          '  and [SQS].TestGroups.tlid2  = [SQS].TLIDName.tlid2;'

                    self.SQLStatement(sql,False)
                    result = self.cur.fetchall()

                    # MichaelRo
                    #if not isNullOrEmpty(result):
                    #    sourceGroup = result[0][1]
                    #    sourceCase  = result[0][2]
                    #    tcnid       = result[0][3]

        except:
            debug("Exception FindTestCases",1,"SQSDB")

            tcid = -1

            # MichaelRo
            # ts_pos = -1

        return TestSteps


    def FindTestStepResult(self, pos, tcrid):

        if tcrid == None:
            return False
        else:
            sql = "SELECT count(*) from [SQS].TestStepsResults where "+\
                  "[SQS].TestStepsResults.tcrid = "+str(tcrid)+" and "+\
                  "[SQS].TestStepsResults.pos = "+str(pos)+";"

            result = self.SQLStatementResult(sql,False)

        if isNullOrEmpty(result):
            return False
        else:
            return result[-1][0]>0

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Helpfunction: Find TestSteps By tcid
    #
    def FindTestStepsByTcid(self,tcid):

        sql = "SELECT POS,TCID,ID,TITLE from [SQS].TestSteps where tcid = "+str(tcid)
        return self.SQLStatementResult(sql)





    ##
    ##   In <table>, count the occurrences of each value of <resultType> and cor_<resultType> column, where <idVal> = <val>.
    ##
    ##   For example, called with  (tcomprid,'TestGroupsResults','tcomprid_val','tgResult') ->
    ##
    ##     res     = SELECT count(tgResult), tgResult FROM [SQS].TestGroupsResults where tcomprid_val = <tcomprid> group by tgResult;
    ##
    ##     cor_res = SELECT count(cor_tgResult), cor_tgResult FROM [SQS].TestGroupsResults where tcomprid_val = <tcomprid> group by cor_tgResult;
    ##
    ##   @param   idVal       String: ID which has to match val.
    ##   @param   table       String: The DB table for retrieving the occurrences of a column value.
    ##   @param   val         String: Column idVal has to match this value.
    ##   @param   resultType  String: [cor_] Column name of values to count.
    ##
    ##   @return  Tuple (res,cor_res,error). If error is False, res[] are the counts for <resultType>, cor_res[] are the results for cor_<resultType>.
    ##            Each result entry is [count,value], the count of entries with that value.
    ##

    def help_GetSums(self, idVal, table, val, resultType):

        err = False

        self.SQLStatement("SELECT count("+resultType+"), "+resultType+" FROM [SQS]."+str(table)+\
                          " where "+val+" = "+str(idVal)+\
                          " group by "+resultType+";",False)

        result = self.cur.fetchall()
        if not isNullOrEmpty(result):
            res = result
        else:
            res = 0
            err = True

        self.SQLStatement("SELECT count(cor_"+resultType+"), cor_"+resultType+" FROM [SQS]."+str(table)+\
                          " where "+val+" = "+str(idVal)+\
                          " group by cor_"+resultType+";",False)

        result = self.cur.fetchall()
        if not isNullOrEmpty(result):
            cor_res = result
        else:
            cor_res = 0
            err = True

        return res,cor_res,err





    ##
    ##   @remark Called only from UpdateTestCaseResultTCRID().
    ##

    def help_GetTestStepsResultsSum(self, idVal ):
        res,cor_res,err = self.help_GetSums(idVal, "[TestStepsResults]", "tcrid", "result")
        return res,cor_res,err





    ##
    ##   Get count of entries for a given column in given DB table.
    ##
    ##   @remark Called only from help_getResults().
    ##
    ##   @param table    Name of DB table in which to count.
    ##   @param col      Name of DB column, which values are counted.
    ##   @param wRow     Name of DB row for selecting table entries.
    ##   @param wRowVal  Value which has to match wRow content.
    ##
    ##   @return  None on errors, else list of (count,value) pairs.
    ##

    def help_getResult(self,table,col,wRow,wRowVal):
        self.SQLStatement("SELECT count("+col+"), "+col+" FROM [SQS]."+table+" where "+wRow+" = "+str(wRowVal)+" group by "+col,False)
        result = self.cur.fetchall()
        if not isNullOrEmpty(result):
            return result
        else:
            return None





    ##
    ##   Call help_getResult() and return counts in value order ok,fail,crash,no,exception,blocked.
    ##
    ##   Count values of a given DB table column and row content.
    ##   Return the counts of values (0,1,2,-1,3,4) = (#ok,#fail,#crash,#no,#exception,#blocked).
    ##   If a value does not exist, return 0 for it.
    ##
    ##   @param table (@see help_getResult).
    ##   @param col (@see help_getResult).
    ##   @param wRow (@see help_getResult).
    ##   @param wRowVal (@see help_getResult).
    ##
    ##   @return (#ok,#fail,#crash,#no,#exception,#blocked)
    ##

    def help_getResults(self,table,col,wRow,wRowVal):

        ok        = 0
        fail      = 0
        crash     = 0
        exception = 0
        blocked   = 0
        no        = 0

        res = self.help_getResult(table,col,wRow,wRowVal)

        if res != None:
            for r in res:
                if   r[1] == -1:  no        = r[0]
                elif r[1] ==  0:  ok        = r[0]
                elif r[1] ==  1:  fail      = r[0]
                elif r[1] ==  2:  crash     = r[0]
                elif r[1] ==  3:  exception = r[0]
                elif r[1] ==  4:  blocked   = r[0]

        ##        ok        = self.help_getResult(table,col,"=0",wRow,wRowVal)
        ##        fail      = self.help_getResult(table,col,"=1",wRow,wRowVal)
        ##        crash     = self.help_getResult(table,col,"=2",wRow,wRowVal)
        ##        exception = self.help_getResult(table,col,"=3",wRow,wRowVal)
        ##        blocked   = self.help_getResult(table,col,"=4",wRow,wRowVal)
        ##        no        = self.help_getResult(table,col,"=-1",wRow,wRowVal)

        return ok,fail,crash,no,exception,blocked





    def help_getResultSum(self,table,col,wRow,tgrid):
        # Return a value of 0 if a None returend form the DB
        err = False
        self.SQLStatement("SELECT sum("+col+") from "+table+" where "+wRow+" = "+str(tgrid),False)
        result = self.cur.fetchall()
        if not isNullOrEmpty(result):
            a = result[0][0]
        else:
            a = 0
            err = True

        self.SQLStatement("SELECT sum(cor_"+col+") from "+table+" where "+wRow+" = "+str(tgrid),False)
        result = self.cur.fetchall()
        b = result[0][0]

        if b == None:
            b = 0
            err = True

        return a,b,err





    #---------------------------------------------------------------------------
    # Add a TLID / Name item
    #
    def setTLIDNameStatus(self,path,status):
        prtcid,tlid1,tlid2 = self.getTLIDbyPath(path)

        if prtcid != -1:

            sql = "UPDATE [SQS].[TLIDName] "+\
                  "SET Status='"+str(status)[:255]+"' "+\
                  "WHERE prtcid="+str(prtcid)+" and tlid1="+str(tlid1)+" and "+"tlid2="+str(tlid2)+";"

            self.SQLStatement(sql)



    #---------------------------------------------------------------------------
    # Add a TLID / Name item
    #
    def setTLIDNameUpdateTime(self,path):
        prtcid,tlid1,tlid2 = self.getTLIDbyPath(path)

        if prtcid != -1:
            t = time.localtime(time.time())

            h = str(t[3])+":"+str(t[4])+":"+str(t[5])
            d = str(t[2])+"."+str(t[1])+"."+str(t[0])

            sql = "UPDATE [SQS].[TLIDName] "+\
                  "SET UpdateTime='"+str(h+" "+d)[:30]+"' "+\
                  "WHERE prtcid="+str(prtcid)+" and tlid1="+str(tlid1)+" and "+"tlid2="+str(tlid2)+";"

            self.SQLStatement(sql)


    # --------------------------------------------------------------------------
    # Add a TestGroupResult by tcomprid and tgid
    #
    def setGetTestGroupResultID(self,tcomprid,tgid,comment = ""):
        tgrid = None
        self.SQLStatement("SELECT tgrid from [SQS].TestGroupsResults where tcomprid = "+str(tcomprid)+" and tgid = "+str(tgid)+";",False)
        result = self.cur.fetchall()

        if isNullOrEmpty(result):
            self.SQLStatement("SELECT max(tgrid) from [SQS].TestGroupsResults;",False)

            result = self.cur.fetchall()
            if not isNullOrEmpty(result):
                tgrid = result[0][0] + 1
            else:
                tgrid = 1

            #
            # Store the Label ID into the DB
            #

            val = str(tcomprid)+","+str(tgid)+","+str(tgrid)+",0,0, 0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0, '"+dbStr(comment)+"',''"
            sql = "INSERT INTO [SQS].[TestGroupsResults] "+\
                  "(tcomprid, tgid, tgrid, tgResult, cor_tgResult,"+\
                  "tc_ok,cor_tc_ok,tc_fail,cor_tc_fail,tc_crash,cor_tc_crash,tc_no,cor_tc_no,"+\
                  "ts_ok,cor_ts_ok,ts_fail,cor_ts_fail,ts_crash,cor_ts_crash,ts_no,cor_ts_no,"+\
                  "comment,rd_comment)"+\
                  "VALUES ("+val+");"

            self.SQLStatement(sql)

        else:
            tgrid = result[0][0]

        return tgrid




    # --------------------------------------------------------------------------
    # Update Test Case Result
    #
    def UpdateTestCaseResult(self,tcrid, ssver, oswt, author, timestamp, version, starttime, stoptime, status):
        sql = "UPDATE [SQS].[TestCasesResults] "+\
              "SET ssver = "+str(ssver)+", os = '"+dbStr(oswt)+"', author = '"+dbStr(author)+"', changeDate = '"+dbStr(timestamp)+"', "+\
              "version = '"+str(version)+"', startTime = '"+dbStr(starttime)+"', stopTime = '"+dbStr(stoptime)+"', tcResult = "+str(status)+", "+\
              "cor_tcResult = "+str(status)+"  "+\
              "WHERE tcrid = "+str(tcrid)+";"

        self.SQLStatement(sql)


    # --------------------------------------------------------------------------
    # Update Test Case Result Comments
    #
    def UpdateTestCasesResultsComments(self,tgrid,tcnid,comment = -1, rd_comment = -1):
        if comment != -1:
            sql = "UPDATE [SQS].[TestCasesResults] "+\
                  "SET comment = '"+dbStr(comment)+"' "\
                  "WHERE tcnid = "+str(tcnid)+\
                   " AND tgrid = "+str(tgrid)+";"

            self.SQLStatement(sql)

        if rd_comment != -1:
            sql = "UPDATE [SQS].[TestCasesResults] "+\
                  "SET rd_comment = '"+dbStr(rd_comment)+"' "\
                  "WHERE tcnid = "+str(tcnid)+\
                   " AND tgrid = "+str(tgrid)+";"
            self.SQLStatement(sql)





    ##
    ##   Set sums of all test step results of a test case in an existing TestCasesResults DB table entry.
    ##
    ##   Set the correspondend ts counter in the TestCasesResults entry
    ##   with ID tcrid. Set the cor_ts counter to the ts counter.
    #
    ##   @param tcrid     ID of this test case result.
    ##   @param ts_ok     Number of passed test steps for this test case result.
    ##   @param ts_fail   Number of failed test steps for this test case result.
    ##   @param ts_crash  Number of crashed test steps for this test case result.
    ##   @param ts_no     Number of not executed test steps for this test case result.
    ##

    def UpdateTestCaseResultStatistic(self,tcrid,ts_ok,ts_fail,ts_crash,ts_no):
        sql = "UPDATE [SQS].[TestCasesResults] "+\
              "SET ts_ok = "+str(ts_ok)+", ts_fail = "+dbStr(ts_fail)+", ts_crash = "+str(ts_crash)+", ts_no = "+str(ts_no)+", "+\
              "cor_ts_ok = "+str(ts_ok)+", cor_ts_fail = "+dbStr(ts_fail)+", cor_ts_crash = "+str(ts_crash)+", cor_ts_no = "+str(ts_no)+" "+\
              "WHERE tcrid = "+str(tcrid)+";"

        self.SQLStatement(sql)

        #self.UpdateTestGroupResultByTCR(tcrid)





    ##
    ##   Collect all test step results for a given test case result ID from DB and store it in TestCasesResults DB entry.
    ##
    ##   Get crash/blocked/fail/exception/ok/no sums for all test steps, for each result and cor_result.
    ##   From the cor_* sums determine cor_tcResult.
    ##
    ##   @param  tcrid  Test case result ID for TestCasesResults DB table entry.
    ##

    def UpdateTestCaseResultTCRID(self,tcrid):

        ##        ts_no,cor_ts_no,err       = self.help_GetTestStepsResultsSum(tcrid,-1)    # No Result
        ##        ts_ok,cor_ts_ok,err       = self.help_GetTestStepsResultsSum(tcrid,0)    # OK / Pass
        ##        ts_fail,cor_ts_fail,err   = self.help_GetTestStepsResultsSum(tcrid,1)    # Fail
        ##        ts_crash,cor_ts_crash,err = self.help_GetTestStepsResultsSum(tcrid,2)    # Crash
        ##
        ##        ts_exception,cor_ts_exception,err = self.help_GetTestStepsResultsSum(tcrid,3)    # Exception
        ##        ts_blocked,cor_ts_blocked,err     = self.help_GetTestStepsResultsSum(tcrid,4)    # Blocked

        ts_no,        cor_ts_no        = 0, 0
        ts_ok,        cor_ts_ok        = 0, 0
        ts_fail,      cor_ts_fail      = 0, 0
        ts_crash,     cor_ts_crash     = 0, 0

        # MichaelRo - not used (no according Db table entries)
        # ts_exception, cor_ts_exception = 0, 0
        # ts_blocked,   cor_ts_blocked   = 0, 0
        cor_ts_exception = 0
        cor_ts_blocked   = 0

        # count all (cor_)result for all test steps = TestStepsResults with given tcrid,
        # results are lists of (count,value) pairs
        res, corres, err = self.help_GetTestStepsResultsSum(tcrid)

        if err == False:
            for r in res:

                if   r[1] == -1:  ts_no            = r[0]
                elif r[1] == 0:   ts_ok            = r[0]
                elif r[1] == 1:   ts_fail          = r[0]
                elif r[1] == 2:   ts_crash         = r[0]

                # MichaelRo - not used (no according DB table entries)
                # elif r[1] == 3:   ts_exception     = r[0]
                # elif r[1] == 4:   ts_blocked       = r[0]

            for r in corres:
                if   r[1] == -1:  cor_ts_no        = r[0]
                elif r[1] == 0:   cor_ts_ok        = r[0]
                elif r[1] == 1:   cor_ts_fail      = r[0]
                elif r[1] == 2:   cor_ts_crash     = r[0]
                elif r[1] == 3:   cor_ts_exception = r[0]
                elif r[1] == 4:   cor_ts_blocked   = r[0]

            #print res, corres, err

        #
        #   Calculate the cor_tcResult of the TestCase
        #
        #   Priority (one or more overrides the other): crash > blocked > fail > exception > ok > no.
        #
        cor_tcResult = -1
        if cor_ts_ok        > 0:  cor_tcResult = 0
        if cor_ts_exception > 0:  cor_tcResult = 3
        if cor_ts_fail      > 0:  cor_tcResult = 1
        if cor_ts_blocked   > 0:  cor_tcResult = 4
        if cor_ts_crash     > 0:  cor_tcResult = 2

        #print "UpdateTestCaseResultTCRID",tcrid,"=",cor_ts_ok,cor_ts_exception,cor_ts_fail,cor_ts_blocked,cor_ts_crash,"=>",cor_tcResult

        # Only the cor results must be updated. Other Data isn't shown anywere.
        sql = "UPDATE [SQS].[TestCasesResults] "+\
              "SET ts_ok = "        + str(ts_ok)            + ", ts_fail = "         + dbStr(ts_fail)        + ", ts_crash = "     + str(ts_crash)       + ", ts_no = "     + str(ts_no)+", "+\
              "cor_ts_ok = "        + str(cor_ts_ok)        + ", cor_ts_fail = "     + dbStr(cor_ts_fail)    + ", cor_ts_crash = " + str(cor_ts_crash)   + ", cor_ts_no = " + str(cor_ts_no)+", "+\
              "cor_ts_exception = " + str(cor_ts_exception) + ", cor_ts_blocked = "  + dbStr(cor_ts_blocked) + ", cor_tcResult = " + dbStr(cor_tcResult) + " "+\
              "WHERE tcrid = "      + str(tcrid)+";"

        self.SQLStatement(sql)





    # ----------------------------------------------------------------------
    # Update Test Component Result
    #
    def UpdateTestComponentsResultsByPath(self,path,labelid):
        self.SQLStatement("SELECT prtcid,tlid1,tlid2 FROM [SQS].[TLIDName] where path = '"+path+"';",False)
        result = self.cur.fetchall()

        if not isNullOrEmpty(result):
            for row in result:               # ? more than 1 result possible ?
                prtcid = row[0]
                tlid1 = row[1]
                tlid2 = row[2]
                self.UpdateTestComponentsResults(prtcid,tlid1,tlid2,labelid)
        else:
            debug('"'+path+"' not found.",1,"SQSDB")





    ##
    ##   Update all results of a given component ("test path") of a given test.
    ##
    ##   Updates first all test group results of the component.
    ##
    ##   @param  prtcid   ID of the component / test path to update.
    ##   @param  tlid1    "
    ##   @param  tlid2    "
    ##   @param  labelid  ID of the test to update (label).
    ##

    def UpdateTestComponentsResults(self,prtcid,tlid1,tlid2,labelid):
        try:
            self.SQLStatement("SELECT tcomprid from [SQS].TestComponentsResults where prtcid = "+str(prtcid)+" AND tlid1 ="+str(tlid1)+" AND tlid2 ="+str(tlid2)+" AND labelid="+str(labelid) ,False)
            result = self.cur.fetchall()

            for row in result:
                tcomprid=str(row[0])

                #
                #   First, update all test group results for this component.
                #

                self.SQLStatement("SELECT tgrid from [SQS].TestGroupsResults where tcomprid = "+tcomprid,False)
                tgridResult = self.cur.fetchall()

                for tgrid in tgridResult:
                    #print "tgrid",tgrid[0]
                    self.UpdateTestGroupResult(tgrid[0])



                #
                #   Get sums of all test steps results and test case results for all group test results for this component.
                #

                self.SQLStatement("SELECT"+\
                                  "   sum(ts_ok),sum(ts_fail),sum(ts_crash),sum(ts_no),"+\
                                  "   sum(cor_ts_ok),sum(cor_ts_fail),sum(cor_ts_crash),sum(cor_ts_no),sum(cor_ts_exception),sum(cor_ts_blocked),"+\
                                  "   sum(tc_ok),sum(tc_fail),sum(tc_crash),sum(tc_no),"+\
                                  "   sum(cor_tc_ok),sum(cor_tc_fail),sum(cor_tc_crash),sum(cor_tc_no),sum(cor_tc_exception),sum(cor_tc_blocked) "+\
                                  "from [SQS].TestGroupsResults where tcomprid = "+tcomprid,False)
                result2 = self.cur.fetchall()


                ts_ok,ts_fail,ts_crash,ts_no,cor_ts_ok,cor_ts_fail,cor_ts_crash,cor_ts_no,cor_ts_exception,cor_ts_blocked,\
                tc_ok,tc_fail,tc_crash,tc_no,cor_tc_ok,cor_tc_fail,cor_tc_crash,cor_tc_no,cor_tc_exception,cor_tc_blocked = result2[0]

                ##                tg_no,cor_tg_no,err               = self.help_GetSums(tcomprid,-1,"TestGroupsResults","tcomprid","tgResult")
                ##                tg_ok,cor_tg_ok,err               = self.help_GetSums(tcomprid, 0,"TestGroupsResults","tcomprid","tgResult")
                ##                tg_fail,cor_tg_fail,err           = self.help_GetSums(tcomprid, 1,"TestGroupsResults","tcomprid","tgResult")
                ##                tg_crash,cor_tg_crash,err         = self.help_GetSums(tcomprid, 2,"TestGroupsResults","tcomprid","tgResult")
                ##                tg_exception,cor_tg_exception,err = self.help_GetSums(tcomprid, 3,"TestGroupsResults","tcomprid","tgResult")
                ##                tg_blocked,cor_tg_blocked,err     = self.help_GetSums(tcomprid, 4,"TestGroupsResults","tcomprid","tgResult")



                #
                #   Collect the test group results tgResult / cor_tgResult for all groups for this component.
                #

                tg_no,        cor_tg_no        = 0, 0
                tg_ok,        cor_tg_ok        = 0, 0
                tg_fail,      cor_tg_fail      = 0, 0
                tg_crash,     cor_tg_crash     = 0, 0
                # MichaelRo - not used, not in DB
                #tg_exception, cor_tg_exception = 0, 0
                #tg_blocked,   cor_tg_blocked   = 0, 0
                cor_tg_exception = 0
                cor_tg_blocked   = 0

                res, corres, err = self.help_GetSums(tcomprid, "TestGroupsResults","tcomprid","tgResult")

                if err == False:

                    for r in res:
                        if   r[1] == -1:   tg_no            = r[0]   # r[0] is count, r[1] is counted value
                        elif r[1] == 0:    tg_ok            = r[0]
                        elif r[1] == 1:    tg_fail          = r[0]
                        elif r[1] == 2:    tg_crash         = r[0]

                        # MichaelRo - not used, not in DB
                        #elif r[1] == 3:    tg_exception     = r[0]
                        #elif r[1] == 4:    tg_blocked       = r[0]

                    for r in corres:
                        if   r[1] == -1:   cor_tg_no        = r[0]
                        elif r[1] == 0:    cor_tg_ok        = r[0]
                        elif r[1] == 1:    cor_tg_fail      = r[0]
                        elif r[1] == 2:    cor_tg_crash     = r[0]
                        elif r[1] == 3:    cor_tg_exception = r[0]
                        elif r[1] == 4:    cor_tg_blocked   = r[0]

                #print res, corres, err



                #
                #   Calculate the result for the component.
                #

                # MichaelRo - not used, not in DB
                #tcompResult = -1
                #if cor_tg_ok        > 0:  tcompResult = 0
                #if cor_tg_exception > 0:  tcompResult = 3
                #if cor_tg_fail      > 0:  tcompResult = 1
                #if cor_tg_blocked   > 0:  tcompResult = 4
                #if cor_tg_crash     > 0:  tcompResult = 2

                #print   tcomprid,"tcomprid =",cor_tg_ok,cor_tg_exception,cor_tg_fail,cor_tg_blocked,cor_tg_crash,"=>",tcompResult

                #
                # Set some Results
                #

                er = 0

                # MichaelRo - not used
                # erTXT = ""

                # ? Is the following possible ?
                # Since all first writing functions initialize with 0 ... DB access errors?

                if tc_ok            == None:   er = 1;  tc_ok            = -1
                if tc_fail          == None:   er = 1;  tc_fail          = -1
                if tc_crash         == None:   er = 1;  tc_crash         = -1
                if tc_no            == None:   er = 1;  tc_no            = -1
                if cor_tc_ok        == None:   er = 1;  cor_tc_ok        = -1
                if cor_tc_fail      == None:   er = 1;  cor_tc_fail      = -1
                if cor_tc_crash     == None:   er = 1;  cor_tc_crash     = -1
                if cor_tc_no        == None:   er = 1;  cor_tc_no        = -1
                if cor_tc_exception == None:   er = 1;  cor_tc_exception = -1
                if cor_tc_blocked   == None:   er = 1;  cor_tc_blocked   = -1
                if ts_ok            == None:   er = 1;  ts_ok            = -1
                if ts_fail          == None:   er = 1;  ts_fail          = -1
                if ts_crash         == None:   er = 1;  ts_crash         = -1
                if ts_no            == None:   er = 1;  ts_no            = -1
                if cor_ts_ok        == None:   er = 1;  cor_ts_ok        = -1
                if cor_ts_fail      == None:   er = 1;  cor_ts_fail      = -1
                if cor_ts_crash     == None:   er = 1;  cor_ts_crash     = -1
                if cor_ts_no        == None:   er = 1;  cor_ts_no        = -1
                if cor_ts_exception == None:   er = 1;  cor_ts_exception = -1
                if cor_ts_blocked   == None:   er = 1;  cor_ts_blocked   = -1

                if er == 1:
                    #debug("UpdateTestComponentsResults: None as Result for tcomprid = "+str(row[0]),1,"SQSDB",NoTB=True)
                    pass

                sql =   "UPDATE [SQS].[TestComponentsResults] SET "+\
                            "tg_ok = "     + str(tg_ok)     + ", tg_fail = "      + str(tg_fail)     +", tg_crash = "     + str(tg_crash)     + ", tg_no = "     + str(tg_no)     + ", " +\
                            "cor_tg_ok = " + str(cor_tg_ok) + ", cor_tg_fail = "  + str(cor_tg_fail) +", cor_tg_crash = " + str(cor_tg_crash) + ", cor_tg_no = " + str(cor_tg_no) + ", cor_tg_exception = " + str(cor_tg_exception) + ", cor_tg_blocked = " + str(cor_tg_blocked)+", " +\
                            "tc_ok = "     + str(tc_ok)     + ", tc_fail = "      + str(tc_fail)     +", tc_crash = "     + str(tc_crash)     + ", tc_no = "     + str(tc_no)     + ", " +\
                            "cor_tc_ok = " + str(cor_tc_ok) + ", cor_tc_fail = "  + str(cor_tc_fail) +", cor_tc_crash = " + str(cor_tc_crash) + ", cor_tc_no = " + str(cor_tc_no) + ", cor_tc_exception = " + str(cor_tc_exception) + ", cor_tc_blocked = " + str(cor_tc_blocked)+", " +\
                            "ts_ok = "     + str(ts_ok)     + ", ts_fail = "      + str(ts_fail)     +", ts_crash = "     + str(ts_crash)     + ", ts_no = "     + str(ts_no)     + ", " +\
                            "cor_ts_ok = " + str(cor_ts_ok) + ", cor_ts_fail = "  + str(cor_ts_fail) +", cor_ts_crash = " + str(cor_ts_crash) + ", cor_ts_no = " + str(cor_ts_no) + ", cor_ts_exception = " + str(cor_ts_exception) + ", cor_ts_blocked = " + str(cor_ts_blocked)+" " +\
                        "where tcomprid = "+ str(row[0])+";"

                self.SQLStatement(sql)
        except:
            debug("No UpdateTestComponentsResults for prtcid = "+str(prtcid)+" AND tlid1 ="+str(tlid1)+" AND tlid2 ="+str(tlid2),1,"SQSDB")





    ##
    ##
    ##
    ##   @param  TestComponentResultID
    ##   @param  TestResult             crtita_result['TestResult'][path][0]
    ##   @param  OS
    ##   @param  timestamp
    ##   @param  envdescr
    ##   @param  whoexec
    ##

    def updateTestComponentResult_ResDesc(self,TestComponentResultID,TestResult,OS,timestamp,envdescr,whoexec):
        m_DateTimeExec = ""
        m_ShortTestPCDesc = ""
        m_OSWhileTestExec = ""

        m_WhoExecTest = whoexec

        m_TestCandidateVersion = ""
        m_TestCandidateBuildType = ""
        m_TestCandidateBuildNumber = ""
        m_TestCandidateSpecialBuild = ""
        m_TestCandidateDate = ""
        m_PlatformWhileTestExec = ""
        m_InterfaceToPlatform = ""
        m_RemarksToTestExec = ""
        m_StatusOfTestExec = ""

        try:
        # --!LarsG: NEU  (Alles neu schreiben, die Attribute kommen woanders her!)

            # Haben wir nicht
            m_ShortTestPCDesc = envdescr

            m_OSWhileTestExec = OS

            # Haben wir nicht
            m_WhoExecTest = whoexec

            # Haben wir nicht
            m_DateTimeExec = timestamp
            #m_DateTimeExec = _Configuration.m_StartNextTest

            # Haben wir nicht
            m_TestCandidateVersion = _Configuration.gb_TestCandidate

            # Haben wir nicht
            m_TestCandidateBuildType = _Configuration.gb_BuildType

            # Haben wir nicht
            ### m_TestCandidateBuildNumber = ResDesc.m_TestCandidateBuildType

            # Haben wir nicht
            ### m_TestCandidateSpecialBuild = ResDesc.m_TestCandidateSpecialBuild

            # Haben wir nicht
            m_TestCandidateDate = _Configuration.gb_BuildDate

            m_PlatformWhileTestExec = "CRTITA-Version: "+_Configuration.gb_CRTITAVersion

            # Haben wir nicht
            m_InterfaceToPlatform = "Python-Version: "+_Configuration.gb_PythonVer

            m_RemarksToTestExec = TestResult['comment']

            m_StatusOfTestExec = TestResult['status']
            #print "m_StatusOfTestExec",ResDesc.m_StatusOfTestExec

        except:
            debug("Error Reading ResDesc",1,"SQSDB")

        sql =   "UPDATE [SQS].[TestComponentsResults] SET "+\
                    "date = '"+str(m_DateTimeExec)+"',"+\
                    "WhoExecTest = '"+str(m_WhoExecTest)+"',"+\
                    "StatusOfTestExec = '"+str(m_StatusOfTestExec)+"', "+\
                    "OSWhileTestExec = '"+str(m_OSWhileTestExec).strip()+"',"+\
                    "ShortTestPCDesc = '"+dbStr(m_ShortTestPCDesc).strip()[:255]+"', "+\
                    "PlatformWhileTestExec = '"+str(m_PlatformWhileTestExec)+"',"+\
                    "InterfaceToPlatform = '"+str(m_InterfaceToPlatform)+"', "+\
                    "comment = '"+dbStr(str(m_RemarksToTestExec).strip())+"', "+\
                    "TestCandidateVersion = '"+str(m_TestCandidateVersion)+"', "+\
                    "TestCandidateBuildType = '"+str(m_TestCandidateBuildType)+"', "+\
                    "TestCandidateBuildNumber = '"+str(m_TestCandidateBuildNumber)+"', "+\
                    "TestCandidateSpecialBuild = '"+str(m_TestCandidateSpecialBuild)+"', "+\
                    "TestCandidateDate = '"+str(m_TestCandidateDate)+"' "+\
                "where tcomprid = "+str(TestComponentResultID)+";"

        self.SQLStatement(sql)




    def UpdateTestGroupResultByTCR(self,tcrid):
        self.SQLStatement("SELECT tgrid from [SQS].TestCasesResults where tcrid = "+str(tcrid),False)
        result = self.cur.fetchall()
        if not isNullOrEmpty(result):
            tgrid = result[0][0]
            self.UpdateTestGroupResult(tgrid)

    def UpdateTestGroupResultByTGID(self,tgid):
        self.SQLStatement("SELECT tgrid from [SQS].TestGroupsResults where tgid = "+str(tgid),False)
        result = self.cur.fetchall()
        if not isNullOrEmpty(result):
            for row in result:
                tgrid = row[0]
                self.UpdateTestGroupResult(tgrid)



    ##
    ##   Collect all results for a given test group and store it in TestGroupsResults DB table.
    ##
    ##   Update in DB test steps results for each related test case (@see UpdateTestCaseResultTCRID()).
    ##
    ##   @param  tgrid  Test group result ID for TestGroupsResults DB entry.
    ##

    def UpdateTestGroupResult(self,tgrid):

        ## self.SQLStatement("SELECT TestGroups.name from TestGroups,TestGroupsResults where TestGroups.tgid = TestGroupsResults.tgid and TestGroupsResults.tgrid = "+str(tgrid),False)
        ## tg_name = self.cur.fetchall()[0][0]
        ##
        ## #print ">"+tg_name+"<",tgrid



        #
        #   Update in DB test steps results for each test case result in this group result (@see UpdateTestCaseResultTCRID()).
        #

        self.SQLStatement("SELECT tcrid from [SQS].TestCasesResults where tgrid = "+str(tgrid),False)
        tcridResult = self.cur.fetchall()
        if not isNullOrEmpty(tcridResult):
            for tcrid in tcridResult:
                #print "tcrid",tcrid[0]
                self.UpdateTestCaseResultTCRID(tcrid[0])



        #
        #   Collect results for all test cases results in this group result.
        #
        #   (tc_exception,tc_blocked not used)

        tc_ok ,tc_fail,tc_crash,tc_no,tc_exception,tc_blocked                         = self.help_getResults("TestCasesResults",    "tcResult","tgrid",tgrid) #@UnusedVariable
        cor_tc_ok ,cor_tc_fail,cor_tc_crash,cor_tc_no,cor_tc_exception,cor_tc_blocked = self.help_getResults("TestCasesResults","cor_tcResult","tgrid",tgrid)




        #
        #   Sum results for all test steps from all test cases results in this group result.
        #

        self.SQLStatement("select"+\
                          "   sum(ts_ok),sum(ts_fail),sum(ts_crash),sum(ts_no),"+\
                          "   sum(cor_ts_ok),sum(cor_ts_fail),sum(cor_ts_crash),sum(cor_ts_no),sum(cor_ts_exception),sum(cor_ts_blocked) "+\
                          "from SQS.TestCasesResults  where tgrid = "+str(tgrid),False)
        result2 = self.cur.fetchall()

        ts_ok,ts_fail,ts_crash,ts_no,cor_ts_ok,cor_ts_fail,cor_ts_crash,cor_ts_no,cor_ts_exception,cor_ts_blocked = str(result2[0]).replace("None","0")[1:-1].split(",")



        #
        #   Determine test group (cor_) result.
        #

        tgResult = 0                    # OK
        if tc_fail  > 0:  tgResult = 1  # Fail
        if tc_crash > 0:  tgResult = 2  # Crash

        cor_tgResult = -1                             # No Result
        if cor_tc_ok        > 0:  cor_tgResult =  0   # OK
        if cor_tc_exception > 0:  cor_tgResult =  3   # Exception
        if cor_tc_fail      > 0:  cor_tgResult =  1   # Fail
        if cor_tc_blocked   > 0:  cor_tgResult =  4   # Blocked
        if cor_tc_crash     > 0:  cor_tgResult =  2   # Crash

        #print tgrid,"tgrid",cor_ts_ok,cor_tc_exception,cor_tc_fail,cor_tc_blocked,cor_ts_crash,cor_ts_no,"=>",cor_tgResult



        #
        #   Store collected and generated results.
        #

        sql =   "UPDATE [SQS].[TestGroupsResults] SET "+\
                    "tgResult = "+str(tgResult)+", cor_tgResult = "+str(cor_tgResult)+", "+\
                    "tc_ok = "+str(tc_ok)+", tc_fail = "+str(tc_fail)+", tc_crash = "+str(tc_crash)+", tc_no = "+str(tc_no)+", "+\
                    "cor_tc_exception = "+str(cor_tc_exception)+", cor_tc_blocked = "+str(cor_tc_blocked)+",cor_tc_ok = "+str(cor_tc_ok)+", cor_tc_fail = "+str(cor_tc_fail)+", cor_tc_crash = "+str(cor_tc_crash)+", cor_tc_no = "+str(cor_tc_no)+", "+\
                    "ts_ok = "+str(ts_ok)+", ts_fail = "+str(ts_fail)+", ts_crash = "+str(ts_crash)+", ts_no = "+str(ts_no)+", "+\
                    "cor_ts_exception = "+str(cor_ts_exception)+", cor_ts_blocked = "+str(cor_ts_blocked)+",cor_ts_ok = "+str(cor_ts_ok)+", cor_ts_fail = "+str(cor_ts_fail)+", cor_ts_crash = "+str(cor_ts_crash)+", cor_ts_no = "+str(cor_ts_no)+" "+\
                "WHERE tgrid = "+str(tgrid)+";"

        self.SQLStatement(sql)





# dies sollte in C# umgesetzt werden!
##    # --------------------------------------------------------------------------
##    # Create an Entry in Blob-Table
##    #
##    def CreateGetBlobfileEntry(self,tcrid, fname, ftype, fcontent):
##        if tcrid != None:
##            size = len(fcontent)
##            newId, update = self.GetMaxFromDBFiles(tcrid, fname)
##            fieldname = "fileContent"
##            if size>8000:
##                fieldName = "fileContentBig"
##            cmd = "INSERT INTO "
##            if update == False:
##                val = str(newId) + "," +str(tcrid)+",'"+dbStr(ftype) + "'," + str(size)+",'"+dbStr(fname)+"',0,0"
##                sql = "INSERT into TestCasesResultDBFiles (fileId, tcrid, fileType, fileSize, fileNameOrig, fileContent, fileContentBig) VALUES (" + val + ");"
##                self.SQLStatement(sql)
##            try:
##                cmd = "SELECT"+fieldName+" FROM TestCasesResultDBFiles WHERE fileId = "+str(newId)+" FOR UPDATE"
##                res = self.SQLStatementResult(cmd)
##                if ((res != None) and (res != [])):
##                    if (res.next()):
##                        # Get the BLOB locator and open output stream for the BLOB
##                        bCol = res.getBLOB(1);
##                        blobOutputStream = bCol.getBinaryOutputStream();
##                        # Open the sample file as a stream for INSERTion
##                        # into the BLOB column
##                        file2Load = os.open(strDirectory + strFile,"r");
##                        sampleFileStream = FileInputStream(file2Load);
##                        # Read a chunk of data from the sample file input stream,
##                        # and write the chunk to the BLOB column output stream.
##                        # Repeat till file has been fully read.
##                        intBytesRead = 0
##                        # read from file until done
##                        intBytesRead = sampleFileStream.read(bBuffer)
##                        while ((intBytesRead) != -1):
##                            # write to BLOB
##                            blobOutputStream.write(bBuffer,0,intBytesRead)
##                            intBytesRead = sampleFileStream.read(bBuffer)
##
##                        # closing the streams and committing
##                        sampleFileStream.close();
##                        blobOutputStream.close();
##                        dbConn.commit();
##            except:
##                debug("Error writing BLOB: "+cmd,1,"SQSDB")




    # --------------------------------------------------------------------------
    # Show some elements of the TLID Tables
    #

    def ShowTLIDTables(self):

##        #self.SQLStatement("SELECT* from TLIDPath where tlid1 > 255463168 ;",False)
##        self.SQLStatement("SELECT* from TLIDPath;",False)
##        while 1:
##            result = self.cur.fetchall()
##
##            # #print header of table
##            for t in self.TLIDPath:
##                #print t,"|",
##            print
##
##            # #print rows
##            for row in result:
##                for i in range(0,len(row)):
##                    column = row[i]
##                    if type(column) == type(1):
##                        column = "0x"+("00000000"+hex(column)[2:])[-8:]
##
##                    #print (str(column)+"                                                                                                ")[:len(self.TLIDPath[i])],"|",
##                print
##
##            if 0 == self.cur.nextset():
##                break

        #print
        #print

        #self.SQLStatement("SELECT* from TLIDName where tlid1 > 255463168 ;")
        self.SQLStatement("SELECT * from [SQS].TLIDName;",False)
        while 1:
            result = self.cur.fetchall()

            # FIXME: There is no TLIDName.
            # #print header of table
            for t in self.TLIDName:
                print t,"|",
            print

            # #print rows
            for row in result:
                for i in range(0,len(row)):
                    column = row[i]

                    if i == 3:
                        if column == "":
                            column = "      "
                        else:
                            column = "   X  "
                    else:
                        if type(column) == type(1):
                            column = "0x"+("00000000"+hex(column)[2:])[-8:]

                    print (str(column)+"                                                                                                ")[:len(self.TLIDName[i])],"|",
                print

            if 0 == self.cur.nextset():
                break

        print
        print


    # -------------------------------------------------------
    # Alle Tabellen erst einmal löschen ...
    # Nur für diese Inbetriebnahme!!!
    #
    def EmptyTables(self):

        # Delete all testresults
        sql = "Delete from SQS.LabelIDNames"
        self.SQLStatement(sql)
        # delete all structure information
        sql = "Delete from SQS.TLIDname Where prtcid>0"
        self.SQLStatement(sql)

        sql = "Delete from SQS.TestStepsResultsPRs"
        self.SQLStatement(sql)
        sql = "Delete from SQS.TestStepsResults"
        self.SQLStatement(sql)
        sql = "Delete from SQS.TestSteps"
        self.SQLStatement(sql)
        sql = "Delete from SQS.TestCasesResultFiles"
        self.SQLStatement(sql)
        sql = "Delete from SQS.TestCasesResultDBFiles"
        self.SQLStatement(sql)
        sql = "Delete from SQS.TestCasesResultDescription"
        self.SQLStatement(sql)
        sql = "Delete from SQS.TestCasesResults"
        self.SQLStatement(sql)
        sql = "Delete from SQS.TestCases"
        self.SQLStatement(sql)
        sql = "Delete from SQS.TestCasesName"
        self.SQLStatement(sql)
        sql = "Delete from SQS.TestGroupsResults"
        self.SQLStatement(sql)
        sql = "Delete from SQS.TestGroups"
        self.SQLStatement(sql)
        sql = "Delete from SQS.TestComponentsResults"
        self.SQLStatement(sql)


    # --------------------------------------------------------------------------
    # Show some elements of the TestCases Tables
    #

    def ShowTables(self):
        self.PrintTable("TestGroups",self.TestGroupsTable)
        self.PrintTable("TestCasesName",self.TestCasesNameTable)
        self.PrintTable("TestCases",self.TestCasesTable,6,50)
        self.PrintTable("TestSteps",self.TestStepsTable,None,50)



    # --------------------------------------------------------------------------
    # Show some elements of the TestCasesResults Tables
    #

    def ShowResultTables(self):
        self.PrintTable("LabelIDNames",self.LabelIDName,None,50)
        self.PrintTable("TestComponentsResults",self.TestComponentResultTable,None,50)
        self.PrintTable("TestGroupsResults",self.TestGroupResultTable,None,50)
        self.PrintTable("TestCasesResults",self.TestCasesResultTable,None,50)
        self.PrintTable("TestStepsResults",self.TestStepsResultTable,None,100)



    # --------------------------------------------------------------------------
    # Show some elements of the TLID Tables
    #

    # #print the content of a Table

    def PrintTable(self,TableName,title,MaxColumn=None,MaxRow=None):
        if MaxColumn == None:
            MaxColumn = len(title)

        print
        print
        #print "Table",TableName
        print

        try:
            self.SQLStatement("SELECT * from [SQS]."+TableName+";",False)

            while 1:
                result = self.cur.fetchall()

                # #print header of table
                for t in title[:MaxColumn]:
                    print t,"|",
                print

                if MaxRow == None:
                    MaxRow = len(result)

                for row in result[:MaxRow]:
                    for i in range(0,len(row[:MaxColumn])):
                        column = row[i]
                        print (str(column)+"                                                                    ")[:len(title[i])],"|",
                    print

                if 0 == self.cur.nextset():
                    break
        except:
            print "Error reading Table"



    #---------------------------------------------------------------------------
    # Save the user edit information from the DB
    #

    ##   @remark Not used.

    def saveUserInfo(self):


        #print "Ge�erte Label"

        f = open("LabelIDNames.csv","w")
        f.write("sslabel\tdisplay_label\n")

        try:
            self.SQLStatement("SELECT sslabel,display_label from [SQS].LabelIDNames where sslabel not like display_label",False)
            result = self.cur.fetchall()

            for row in result:
                sslabel = row[0]
                display_label = row[1]
                if sslabel != display_label:
                    #print sslabel,"=>",display_label
                    f.write(sslabel+"\t"+display_label+"\n")
        except:
            print "Fehler beim schreiben von LabelIDNames.csv"

        f.close()



        #print "Corrected Results"

        f = open("CorrectedResults.csv","w")
        f.write("sslabel\tdisplay_label\n")

        try:
            self.SQLStatement(  "select"+\
                                "  TLIDName.path, TestGroups.name, TestCasesName.name, LabelIDNames.sslabel,"+\
                                "  TestComponentsResults.os, TestStepsResults.pos, TestStepsResults.cor_result "+\
                                "from"+\
                                "  TLIDName, LabelIDNames, TestComponentsResults, TestGroups, TestGroupsResults,"+\
                                "  TestCasesName, TestCasesResults, TestStepsResults "+\
                                "where"+\
                                "  TLIDName.tlid2 = TestComponentsResults.tlid2 and"+\
                                "  TLIDName.tlid1 = TestComponentsResults.tlid1 and"+\
                                "  TLIDName.prtcid = TestComponentsResults.prtcid and"+\
                                "  LabelIDNames.labelid = TestComponentsResults.labelid and"+\
                                "  TestComponentsResults.tcomprid = TestGroupsResults.tcomprid and"+\
                                "  TestGroups.tgid = TestGroupsResults.tgid and"+\
                                "  TestGroupsResults.tgrid = TestCasesResults.tgrid and"+\
                                "  TestCasesName.tcnid = TestCasesResults.tcnid and"+\
                                "  TestStepsResults.tcrid = TestCasesResults.tcrid and"+\
                                "  TestStepsResults.cor_result != TestStepsResults.result",False)
            result = self.cur.fetchall()

            #print "Corrected Results"
            for row in result:
                path = row[0]
                tg_name = row[1]
                tc_name = row[2]
                sslabel = row[3]
                os = row[4]
                pos = row[5]
                cor_result = row[6]

                #print path,tg_name,tc_name,sslabel,os,pos,cor_result
                f.write(path+"\t"+tg_name+"\t"+tc_name+"\t"+sslabel+"\t"+os+"\t"+str(pos)+"\t"+str(cor_result)+"\n")
        except:
            #print "Fehler beim schreiben von CorrectedResults.csv"
            import traceback
            traceback.print_exc()
        f.close()

        #print "R&D Comments"

        f = open("RDComments.csv","w")
        f.write("sslabel\tdisplay_label\n")

        try:

            self.SQLStatement(  "select"+\
                                "  TLIDName.path, TestGroups.name, TestCasesName.name, LabelIDNames.sslabel,"+\
                                "  TestComponentsResults.os, TestStepsResults.pos, TestStepsResults.rd_comment "+\
                                "from"+\
                                "  TLIDName, LabelIDNames, TestComponentsResults, TestGroups, TestGroupsResults,"+\
                                "  TestCasesName, TestCasesResults, TestStepsResults "+\
                                "where"+\
                                "  TLIDName.tlid2 = TestComponentsResults.tlid2 and"+\
                                "  TLIDName.tlid1 = TestComponentsResults.tlid1 and"+\
                                "  TLIDName.prtcid = TestComponentsResults.prtcid and"+\
                                "  LabelIDNames.labelid = TestComponentsResults.labelid and"+\
                                "  TestComponentsResults.tcomprid = TestGroupsResults.tcomprid and"+\
                                "  TestGroups.tgid = TestGroupsResults.tgid and"+\
                                "  TestGroupsResults.tgrid = TestCasesResults.tgrid and"+\
                                "  TestCasesName.tcnid = TestCasesResults.tcnid and"+\
                                "  TestStepsResults.tcrid = TestCasesResults.tcrid and"+\
                                '  TestStepsResults.rd_comment not like ""',False)
            result = self.cur.fetchall()
            #print result

            for row in result:
                path = row[0]
                tg_name = row[1]
                tc_name = row[2]
                sslabel = row[3]
                os = row[4]
                pos = row[5]
                rd_comment = row[6]

                #print path,tg_name,tc_name,sslabel,os,pos,rd_comment
                f.write(path+"\t"+tg_name+"\t"+tc_name+"\t"+sslabel+"\t"+os+"\t"+str(pos)+"\t"+str(rd_comment)+"\n")
        except:
            #print "Fehler beim schreiben von R&D Comments.csv"

            # MichaelRo
            # import traceback

            traceback.print_exc()
        f.close()

        #print "- End -"





    ##   @remark  Not used.

    def importUserInfo(self):

        """
        #print "Ge�erte Label importieren"

        f = open("LabelIDNames.csv","r")
        LabelIDNames = f.readlines()
        f.close()

        for label in LabelIDNames[1:]:
            sslabelNew,display_labelNew = string.split(label[:-1],"\t")
            #print sslabelNew,"=>",display_labelNew

            try:
                self.SQLStatement('SELECTsslabel,display_label from LabelIDNames where sslabel ="'+sslabelNew+'"',False)
                result = self.cur.fetchall()

                if len(result) > 0:
                    for row in result:
                        sslabel = row[0]
                        display_label = row[1]

                        # Check the labels in the new DB
                        if sslabel!=display_label:
                            if display_label != display_labelNew:
                                #print "\n\nChanged Label in new DB!!!"
                                #print display_label,"!=",display_labelNew,"\n\n"
                        else:
                            try:
                                #print sslabel,"=>",display_labelNew
                                sql =   "UPDATE LabelIDNames SET "+\
                                            'display_label="'+str(display_labelNew)+'"'+\
                                            'where sslabel="'+sslabelNew+'";'

                                self.SQLStatement(sql)
                            except:
                                #print "Updated failed!"
                else:
                    #print "Label not found in new DB!",sslabelNew
            except:
                #print "Fehler beim schreiben von LabelIDNames.csv"
        """


        """
        #print "Import corrected Results"

        f = open("CorrectedResults.csv","r")
        CorrectedResults = f.readlines()
        f.close()

        for CorrectedResult in CorrectedResults[1:]:
            path,tg_name,tc_name,sslabel,os,pos,cor_result = string.split(CorrectedResult[:-1],"\t")
            #print path,tg_name,tc_name,sslabel,os,pos,cor_result


            sql = 'SELECTTestStepsResults.tcrid,'+\
                        ' TestStepsResults.logText,'+\
                        ' TestStepsResults.rd_comment,'+\
                        ' TestStepsResults.cor_result,'+\
                        ' TestGroupsResults.tgrid '+\
                  ' from TLIDName,'+\
                        ' LabelIDNames,'+\
                        ' TestComponentsResults,'+\
                        ' TestGroups,'+\
                        ' TestCasesName,'+\
                        ' TestGroupsResults,'+\
                        ' TestCasesResults,'+\
                        ' TestStepsResults '+\
                  ' where TLIDName.Path="'+path+'" '+\
                  ' and TestComponentsResults.prtcid = TLIDName.prtcid '+\
                  ' and TestComponentsResults.tlid1 = TLIDName.tlid1 '+\
                  ' and TestComponentsResults.tlid2 = TLIDName.tlid2 '+\
                  ' and LabelIDNames.sslabel="'+sslabel+'" '+\
                  ' and TestComponentsResults.labelid = LabelIDNames.labelid'+\
                  ' and TestComponentsResults.os = "'+os+'" '+\
                  ' and TestGroups.prtcid = TLIDName.prtcid '+\
                  ' and TestGroups.tlid1 = TLIDName.tlid1 '+\
                  ' and TestGroups.tlid2 = TLIDName.tlid2 '+\
                  ' and TestGroups.name = "'+tg_name+'" '+\
                  ' and TestCasesName.tgid = TestGroups.tgid '+\
                  ' and TestCasesName.name = "'+tc_name+'" '+\
                  ' and TestGroupsResults.tcomprid = TestComponentsResults.tcomprid '+\
                  ' and TestGroupsResults.tgid = TestGroups.tgid '+\
                  ' and TestCasesResults.tgrid = TestGroupsResults.tgrid '+\
                  ' and TestCasesResults.tcnid = TestCasesName.tcnid '+\
                  ' and TestStepsResults.tcrid = TestCasesResults.tcrid '+\
                  ' and TestStepsResults.pos = '+str(pos)
            self.SQLStatement(sql,False)
            result = self.cur.fetchall()

            if len(result) > 0:
                if len(result) == 1:
                    for row in result:

                        tcrid       = row[0]
                        log         = row[1]
                        rd_comment  = row[2]
                        cor_resultO = row[3]
                        tgrid       = row[4]

                        #print cor_resultO,"<=>",cor_result
                        #print "tcrid,tgrid",tcrid,tgrid

                        sql =   "UPDATE TestStepsResults SET"+\
                                    ' cor_result = '+str(cor_result)+\
                                    ' where TestStepsResults.tcrid = '+str(tcrid)+\
                                    ' and TestStepsResults.pos = '+str(pos)+';'

                        self.SQLStatement(sql)
                        self.UpdateTestCaseResultTCRID(tcrid)
                        self.UpdateTestGroupResult(tgrid)
                        self.UpdateTestComponentsResultsByPath(path)
                else:
                    #print "\n\n!!!More than expected!!!"
                    for row in result:
                        #print row[0]
                        #print row[1]
                        #print row[2]
                        #print row[3],"<=>",cor_result
            """


        #print "Import Comments"

        f = open("RDComments.csv","r")
        CorrectedResults = f.readlines()
        f.close()

        for i in range(len(CorrectedResults)-1,1,-1):
            if CorrectedResults[i][0] != "$":
                CorrectedResults[i-1] += CorrectedResults[i]
                CorrectedResults.pop(i)

        for CorrectedResult in CorrectedResults[1:]:
            sps = string.split(CorrectedResult[:-1],"\t")
            #print sps

            path=sps[0]
            tg_name=sps[1]
            tc_name=sps[2]
            sslabel=sps[3]
            os=sps[4]
            pos=sps[5]

            # MichaelRo
            # rd_comment = sps[5:]

            #print path,tg_name,tc_name,sslabel,os,pos,rd_comment


            sql = 'SELECT [SQS].TestStepsResults.tcrid,'+\
                        ' [SQS].TestStepsResults.logText,'+\
                        ' [SQS].TestStepsResults.rd_comment,'+\
                        ' [SQS].TestStepsResults.cor_result,'+\
                        ' [SQS].TestGroupsResults.tgrid '+\
                  ' from [SQS].TLIDName,'+\
                        ' LabelIDNames,'+\
                        ' TestComponentsResults,'+\
                        ' TestGroups,'+\
                        ' TestCasesName,'+\
                        ' TestGroupsResults,'+\
                        ' TestCasesResults,'+\
                        ' TestStepsResults '+\
                  ' where TLIDName.Path="'+path+'" '+\
                  ' and TestComponentsResults.prtcid = TLIDName.prtcid '+\
                  ' and TestComponentsResults.tlid1 = TLIDName.tlid1 '+\
                  ' and TestComponentsResults.tlid2 = TLIDName.tlid2 '+\
                  ' and LabelIDNames.sslabel="'+sslabel+'" '+\
                  ' and TestComponentsResults.labelid = LabelIDNames.labelid'+\
                  ' and TestComponentsResults.os = "'+os+'" '+\
                  ' and TestGroups.prtcid = TLIDName.prtcid '+\
                  ' and TestGroups.tlid1 = TLIDName.tlid1 '+\
                  ' and TestGroups.tlid2 = TLIDName.tlid2 '+\
                  ' and TestGroups.name = "'+tg_name+'" '+\
                  ' and TestCasesName.tgid = TestGroups.tgid '+\
                  ' and TestCasesName.name = "'+tc_name+'" '+\
                  ' and TestGroupsResults.tcomprid = TestComponentsResults.tcomprid '+\
                  ' and TestGroupsResults.tgid = TestGroups.tgid '+\
                  ' and TestCasesResults.tgrid = TestGroupsResults.tgrid '+\
                  ' and TestCasesResults.tcnid = TestCasesName.tcnid '+\
                  ' and TestStepsResults.tcrid = TestCasesResults.tcrid '+\
                  ' and TestStepsResults.pos = '+str(pos)
            self.SQLStatement(sql,False)

            # MichaelRo
            result = self.cur.fetchall() #@UnusedVariable

##            if len(result) > 0:
##                if len(result) == 1:
##                    for row in result:
##
##                        tcrid       = row[0]
##                        log         = row[1]
##                        rd_comment  = row[2]
##                        cor_resultO = row[3]
##                        tgrid       = row[4]
##
##                        #print "tcrid,tgrid",tcrid,tgrid
##
##                        sql =   "UPDATE TestStepsResults SET"+\
##                                    ' rd_comment = "'+str(rd_comment)+'"'\
##                                    ' where TestStepsResults.tcrid = '+str(tcrid)+\
##                                    ' and TestStepsResults.pos = '+str(pos)+';'
##
##                        self.SQLStatement(sql)
##
##                else:
##                    #print "\n\n!!!More than expected!!!"
##                    for row in result:
##                        #print row[0]
##                        #print row[1]
##                        #print row[2]
##                        #print row[3],"<=>",cor_result
'''
if __name__ == '__main__':
    """
    print"\nOrginal DB:"
    db = SS2SQL()
    db.OpenDB()
    #db.AddTLIDName(1027,100663296,0,1,"Instrumentation");
    #db.UpdateTestComponentsResults(513,251724288,0)
    db.saveUserInfo()
    #db.ShowTLIDTables()
    #db.PrintTable("LabelIDNames",db.LabelIDName,None,1000)
    db.CloseDB()
    db = None
    """

    """
    print"\n\n\nDebug DB:"
    db = SS2SQL()
    db.OpenDB(debugDB = True)

    db.importUserInfo()


    #db.AddTLIDName(1027,100663296,0,1,"Instrumentation");
    #db.UpdateTestComponentsResults(513,251724288,0)
    #db.saveUserInfo()
    #db.ShowTLIDTables()
    #db.PrintTable("LabelIDNames",db.LabelIDName,None,1000)
    db.CloseDB()
    db = None
    """
    """
    # Save Userdata from DB
    db = SS2SQL()
    db.OpenDB(debugDB = True)

    #print "Start - Save User Info"
    db.saveUserInfo()
    #print "Stop - Save User Info"
    db.CloseDB()
    db = None

    #print "- End -"
    """
    """
    db = SS2SQL()
    db.OpenDB()

    print "ret",db.SQLStatementResult("SELECT* FROM TLIDName",False)

    db.CloseDB()
    db  = None

    print "- Fine -"
    """

    print "Get all"
    db = SQS2SQL()
    db.OpenDB()

    print "ret",db.SQLStatementResult("SELECTTCID FROM TestCases")
    print db.SQLStatementResult("SELECTtlid1 from TLIDName")[0][0]
    print db.SQLStatement("SELECTtlid1 from TLIDName;",False)
    """
    conn = db.con
    cur = conn.cursor()
    cur.execute('SELECT* FROM TLIDName') # WHERE salesrep=%s', 'John Doe')

    row = cur.fetchall()
    for r in row:
        print r

    conn.close()
    """

    db.CloseDB()
'''


