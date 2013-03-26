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

def insert_result():
    db = SQSDB.SQS2SQL(None)
    db.OpenDB(True)


def main():
    import find_results
    result_path = r"R:\PE\Testdata\CRTI-Test\ImplSW_RLS_2013-A"
    for result_file in find_results.results(result_path, 'crtita'):
        print "Found result at %r." % (result_file, )
        insert_result()
        # insertResult()


if __name__ == '__main__':
    main()
