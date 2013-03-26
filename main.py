import os
import time
import shutil
import _Configuration

import SQS_TR2DB
import SQSDB


def insertResult(folderpath, daemonPath, folder, name, logPath):
    runTest = True
    _Configuration.foldername = name
    _Configuration.folderpath = logPath
    logPath = os.path.join(daemonPath, "logs")
    logPathName = os.path.join(logPath, name)
    if not os.path.exists(logPathName):
        os.makedirs(logPathName)
    productName = None
    debugFlag = False

    DBImpLog = logPath
    if not os.path.exists(DBImpLog):
        os.mkdir(DBImpLog)

    # reset/init global variables
    _Configuration.gb_OSWhileTestExec = ""
    _Configuration.gb_MATLABVer = ""
    _Configuration.gb_BuildDate = ""
    _Configuration.gb_BuildType = ""
    _Configuration.gb_TestCandidate = ""
    _Configuration.gb_StartTime = 0.0
    _Configuration.gb_EndTime = 0.0
    _Configuration.gb_CRTITAVersion = ""
    _Configuration.gb_FrameVersion = ""
    _Configuration.gb_Extensions = []
    _Configuration.gb_Libraries = []
    _Configuration.gb_PythonVer = ""
    _Configuration.gb_TestScriptCtrlParameter = {}
    _Configuration.gb_TestScriptParameter = {}
    _Configuration.m_StartNextTest = 0.0
    _Configuration.m_lastExecTime = 0.0
    _Configuration.gb_SQLStatements = 0

    prodDBEntry = None
    configpath = os.path.join(folderpath, "Conf.txt")
    if not os.path.exists(os.path.join(folderpath, "crtita_result")):
        runTest = False
    if os.path.exists(configpath):
        f = open(configpath)
        params = {}
        for line in f:
            if line.find("=") >= 0:
                param = line.strip("\n").split("=")
                params[param[0]] = param[1]
        f.close()

        productName = params.get('PRODUCTNAME', "unknown")
        _Configuration.gb_SaveUnknownAuthors = params.get('SaveAuthors')
        _Configuration.gb_MATLABVer = "ML " + params.get('Matlab', "na")

        # extracting some information about the test candidate from Build
        # result, for example:
        # \\dspace.de\root\PE\Build\ConfigurationDesk\IMPL\2011B\NB\2011-09-06
        hstr = params.get('BuildRoot')
        if hstr:
            r, _Configuration.gb_TestCandidate, _Configuration.gb_BuildType, \
                _Configuration.gb_BuildDate = hstr.rsplit("\\", 4)

        print "Import is running for: %s (%s %s)" % (
            _Configuration.gb_TestCandidate, _Configuration.gb_BuildType,
            _Configuration.gb_BuildDate)
        # SQSDB_Logging.logging("", logPath)

        prodDBEntry = productName
    else:
        runTest = False
        print "Conf.txt missing... "
        print "Import of result " + folderpath + " canceled"
        brokenPath = os.path.join(daemonPath, "corrupt")
        if not os.path.exists(brokenPath):
            os.mkdir(brokenPath)
        print folderpath, brokenPath, name
        shutil.copytree(folderpath, os.path.join(brokenPath, name))

    try:
        db = SQSDB.SQS2SQL(None)
        db.OpenDB(debugFlag)
        print "Connection to database established: %s" % (
            _Configuration.DB_host, )

    except:
        print "Failed to connect to databese"
        runTest = False

    if runTest:
        try:
            starttime = time.time()
            print "Import for " + prodDBEntry + " is running ..."
            ts_root = os.path.join(daemonPath, "working")

            # MichaelRo, unused variables
            # stat = os.stat(ts_root+"crtita_result")
            # label = None

            # MichaelRo (see scriptnamedict comment above)
            #                        <dir "working" with copied crtita_result>             "/<product name>"                      (see above)
            # SQS_TR2DB.ImportData(db, ts_root,                                              _Configuration.prePath + prodDBEntry, scriptnamedict)
            SQS_TR2DB.ImportData(db, ts_root, folderpath, _Configuration.prePath + prodDBEntry)

            endtime = time.time()
            print "Import finished! ("+str(endtime-starttime)+" sec)\n"

        except:
            SQS_TR2DB.debug("Exception", 1, "XML2DB")
            SQS_TR2DB.debug("Exception working on Import data")

    if db:
        db.CloseDB()
    db = None


def clearLogFolders(daemonpath, saveUnknownAuthors):
    try:
        logPath = os.path.join(daemonpath, "logs")
        logFoldernames = os.listdir(logPath)
        logFoldernames.sort()
        print "logpaths found ... " + str(len(logFoldernames))
        for logPathName in logFoldernames:
            if not os.path.isdir(logPath+"\\"+logPathName):
                continue
            print "Checking "+logPath+"\\"+logPathName+" ... "
            dodelete = not os.path.exists(logPath+"\\"+logPathName + "\\"+"CRTITA-DBImport.ERROR.txt")
            if not dodelete:
                print "Cannot delete "+logPath+"\\"+logPathName+" because CRTITA-DBImport.ERROR.txt exists in folder!"
            else:
                dodelete = not os.path.exists(logPath+"\\"+logPathName + "\\"+"CRTITA-DBImport.DBTimelog."+logPathName+".csv")
                if not dodelete:
                    print "Can not delete %r because CRTITA-DBImport." \
                        "DBTimelog.%s.csv exists in folder!" % (
                        os.path.join(logPath, logPathName), logPathName)
            authors = os.path.join(logPath, logPathName,
                                   "CRTITA-DBImport.Update.csv")

            if dodelete and saveUnknownAuthors and os.path.exists(authors):
                print "Checking for <unknown> authors in " + authors
                f = open(authors)
                for line in f:
                    line = line.strip("\n")+';'
                    col = line.split(";")
                    author = col[1]  # ab sofort neues Tabellenformat ...
                    #print "Author = " + author

                    # MichaelRo
                    # if author == "<unknown>":
                    if author == "&lt;unknown&gt;":
                        dodelete = False
                        print "Cannot delete %r because some <unknown> " \
                            "authors exists in file!" % (
                            os.path.join(logPath, logPathName))
                        break
                f.close()
            if dodelete:
                shutil.rmtree(logPath+"\\"+logPathName)
                print "Clearing logging directories ... Path "+logPath+"\\"+logPathName+" was deleted!"
    except:
        SQSDB_Logging.logging("Failed to clear logging directories!", logPath)


def main(oneShot):

    # daemonPath = "D:\\CRTITAWRVImport"
    # path = os.path.join("\\\\Nas1-dspace\\Info\\CRTITAWRVImport", "new")
    # old = os.path.join("\\\\Nas1-dspace\\Info\\CRTITAWRVImport", "old")

    # MichaelRo
    # Relative new/old under daemonPath only here for running eclipse project.
    # TODO: move settings to _Configuration.py

    # MichaelRo
    global daemonPath, workingDir, logPath, path, old

    daemonPath = os.path.abspath('..')

    print daemonPath
    path = os.path.abspath(os.path.join(daemonPath, 'new'))
    old = os.path.abspath(os.path.join(daemonPath, 'old'))

    if not os.path.exists(old):
        os.mkdir(old)
    workingDir = os.path.join(daemonPath, "working")
    logPath = os.path.join(daemonPath, "logs")

    os.chdir(os.path.join(daemonPath, 'main'))

    print "TestResultDaemon startet ....."

    cnt = 1440 // _Configuration.waitingTime
    while(True):
        foldernames = os.listdir(path)
        foldernames.sort()

        if len(foldernames) == 0:
            print "no work to do, sleeping ..."
            cnt = cnt + 1
            # taeglich nur genau einmal pruefen und loeschen ...
            if cnt * _Configuration.waitingTime >= 86400:
                cnt = 0
                print "Trying to clear logdirectories ..."
                clearLogFolders(daemonPath, _Configuration.gb_SaveUnknownAuthors)
            # MichaelRo
            if oneShot:
                break

            time.sleep(_Configuration.waitingTime)
        elif len(foldernames) > 0 and not os.path.exists(os.path.join(path, "locked")):
            if not os.path.exists(os.path.join(old, foldernames[0])):
                shutil.copytree(os.path.join(path, foldernames[0]), os.path.join(old, foldernames[0]))
            if os.path.exists(os.path.join(path, foldernames[0], 'crtita_result')):
                print "CRTITA_Result found in folder " + str(os.path.join(path, foldernames[0]))

                #print 'os.path.join(path,foldernames[0],"crtita_result")  %s' % (os.path.join(path,foldernames[0],'crtita_result'),)
                #print 'workingDir %s' % (workingDir,)
                shutil.copy(os.path.join(path, foldernames[0], 'crtita_result'),
                            workingDir)
                # exit()

                insertResult(os.path.join(path, foldernames[0]), daemonPath,
                             path, foldernames[0], logPath)
                try:
                    shutil.rmtree(os.path.join(path, foldernames[0]))
                except:
                    print "Error: Cannot delete " + foldernames[0]
                os.remove(os.path.join(workingDir, 'crtita_result'))
            else:
                print "Error: CRTITA_Result not found in " + foldernames[0] + " moving to corrupt directory"
                SQSDB_Logging.logging("\nError: CRTITA_Result not found in " + foldernames[0], logPath)
                if not os.path.exists(os.path.join(daemonPath, "corrupt")):
                    os.mkdir(os.path.join(daemonPath, "corrupt"))
                try:
                    if not os.path.exists(os.path.join(daemonPath, "corrupt", foldernames[0])):
                        shutil.copytree(os.path.join(path, foldernames[0]), os.path.join(daemonPath, "corrupt", foldernames[0]))
                except:
                    SQSDB_Logging.logging("\nError: Try copying path: " + foldernames[0], logPath)
                try:
                    shutil.rmtree(os.path.join(path, foldernames[0]))
                except:
                    SQSDB_Logging.logging("\nError: Try deleting path: " + foldernames[0], logPath)
            foldernames = ""

if __name__ == '__main__':
    main(False)
