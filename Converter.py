#-------------------------------------------------------------------------------
# Name:        RTITE2CRTITAConverter
# Purpose:     Converts .mat-resultfiles of RTITE to CRTITA structures for
#              importing them with CRTITAWRVImporter.
#
# Author:      TimV
#
# Created:     23.02.2012
# Copyright:   (c) dSPACE GmbH 2012
#-------------------------------------------------------------------------------

from numpy import array
import sys
import time
import scipy.io.matlab
import calendar
import datetime
import os
import pickle

## ------ For output only ---------------------------------------------------------------
def __noCr(s):
    """Removes all linebreaks"""
    return s.replace('\n', '').replace('\r', '')
    #return s

depth = 0

def __printArrayStruct(a):
    """Prints the structure of a MAT-file"""
    global depth
    depth += 1
    indent = 4
    if type(a) == type(array(0)):
        a = a[0][0]
        for i in range(0, len(a[0])):
                for n in a.dtype.names:
                    e = a[n][0][i]
                    try:
                        z = e.dtype.names != None
                    except:
                        z = False

                    if z:
                        #print ' ' * depth * indent + n
                        __printFormatted("- " + n, depth, indent, 150)
                        __printArrayStruct(a[n])
                    else:
                        if len(e) > 0:
                            #print '%-32s%s' % (' ' * depth * indent + n, noCr(str(e[0]))[:150])     # leaf
                            __printFormatted("- " + n, depth, indent, 150)
                            __printFormatted(str(e[0]), depth + 1, indent, 150)
                        else:
                            #print ' ' * depth * indent + n
                            __printFormatted("- " + n, depth, indent, 150)
    depth -= 1

def __printFormatted(t, depth, indent, maxlength):
    """Formats the text with the given depth to match desired indentation"""
    if type(t) == type("") or type(t) == type(u""):
        if maxlength > 0 and len(t) > maxlength:
            t = t[:maxlength] + " [...]"
        if t.strip() == "":
            t = "[EMPTY]"
        c = t.split("\n")
        for x in c:
            print " " * depth * indent, x
    else:
        print " " * depth * indent, "[" + str(type(t)).split("'")[1] + "] ", t

def __printCRTITA(t, depth, maxlength):
    """Prints the contents of a CRTITA structure"""
    indent = 4
    if type(t) == type({}):
        for x in t.keys():
            if x.strip() == "":
                s = "[EMPTY]"
            else:
                s = x
            print " " * depth * indent, "-", s
            __printCRTITA(t[x], depth + 1, maxlength)
    elif type(t) == type([]):
        for i, x in enumerate(t):
            print " " * depth * indent, "[" + str(i) + "]"
            __printCRTITA(x, depth + 1, maxlength)
    else:
        __printFormatted(t, depth, indent, maxlength)

def __printMat(mat):
    """Prints the contents of a loaded Mat-file"""
    print
    print "#####################"
    print "#      Matfile      #"
    print "#####################"
    print
    print "--- ENVIRONMENT ---"
    print
    __printArrayStruct(mat['testdata']['environment'])
    print
    print
    print "--- TEPARAM ---"
    __printArrayStruct(mat['testdata']['teparam'])
    print
    print
    print "--- RESULT ---"
    __printArrayStruct(mat['testdata']['result'])
    print
    print "#####################"
    print "#   End of Matfile  #"
    print "#####################"
    print
## ------------------------------------------------------------------------------------
def printHeader():
    # Header
    print " ______________________________________________ "
    print "|                                              |"
    print "| RTITE2CRTITA Converter v0.1 (c)dSPACE GmbH   |"
    print "|______________________________________________|"

def printFooter():
    print " ______________________________________________ "
    print "|                                              |"
    print "|             All tasks successful.            |"
    print "|______________________________________________|"

def convertAndSaveMany(matfilesRoot, resultsSaveRoot, printMat=False, printResult=False, generateConfTxt=True, maxOutputLineLength=100):
    """ Converts all matfiles below the given matfilesRoot and saves them as "resultsSaveRoot\\FolderStructureAsBelowRoot\\crtita_result"
    
            If stated True, also prints the loaded Matfile and the result, any strings cropped to <maxOutputLineLength> characters.
            Can also generate the necessary Conf.txt file below resultSaveFolder (default is True)"""
    printHeader()
    # Get all matfiles below matfilesRoot
    print
    print "--- Getting matfiles to convert ---"
    print
    matfiles = []
    i = 0
    for dirpath, _, filenames in os.walk(matfilesRoot):
        for fn in filenames:
            if fn.endswith(".mat"):
                matpath = os.path.join(dirpath, fn)
                print "  -", matpath
                matfiles.append(matpath)
                i += 1
    print
    print "--- Finished, found " + str(i) + " file" + ("s" if i != 1 else "") + " ---"
    print
    current = 1
    for matpath in matfiles:
        print
        print "###"
        print "### Converting file " + str(current) + "/" + str(len(matfiles)) + ": \"" + matpath + "\" ###"
        print "###"
        print
        convertedFile = __convert(matpath, printMat, printResult, maxOutputLineLength)
        print
        savepath = os.path.join(resultsSaveRoot, matpath[len(matfilesRoot) + 12:len(matpath) - 4], "crtita_result")
        if not os.path.exists(os.path.join(resultsSaveRoot, matpath[len(matfilesRoot) + 12:len(matpath) - 4])):
            os.makedirs(os.path.join(resultsSaveRoot, matpath[len(matfilesRoot) + 12:len(matpath) - 4]))
        print
        print "--- Saving to " + savepath + " ---"
        pickle.dump(convertedFile, open(savepath, "w"))
        print
        print "--- Finished Saving ---"
        print
        print
        if generateConfTxt:
            __GenerateConfTxt(matpath, os.path.split(savepath)[0])
            print
        print
        print "###"
        print "### Finished conversion of file " + str(current) + "/" + str(len(matfiles)) + " ###"
        print "###"
        current += 1
    print
    printFooter()

def convertAndSave(matfilepath, resultSaveFolder, printMat=False, printResult=False, generateConfTxt=True, maxOutputLineLength=100):
    """Converts the given matfile and saves it as "resultSaveFolder\\crtita_result".
    
            If stated True, also prints the loaded Matfile and the result, any strings cropped to <maxOutputLineLength> characters.
            Can also generate the necessary Conf.txt file below resultSaveFolder (default is True)"""
    # convert mat
    crtita = __convert(matfilepath, printMat, printResult, maxOutputLineLength)
    # save result
    print
    print "> Saving CRTITA result (\"" + os.path.join(resultSaveFolder, "crtita_result") + "\")...",
    pickle.dump(crtita, open(os.path.join(resultSaveFolder, "crtita_result"), "w"))
    print "Finished."
    print
    # generate Conf.txt
    if generateConfTxt:
        __GenerateConfTxt(matfilepath, resultSaveFolder)
    printFooter()


def __convert(matfile, printMat=False, printResult=False, maxlength=100):
    """Converts the given matfile (as path) and returns a corresponding CRTITA structure
        
            If stated True, also prints the loaded Matfile and the result, any strings cropped to <maxlength> characters"""
    # Starttime Loading
    start = time.time()
    # Overall starttime
    convstart = time.time()
    print "--- Conversion of \'" + matfile + "\' ---"
    print
    # Loading
    print "Loading file...",
    mat = scipy.io.matlab.loadmat(matfile)
    end = time.time()
    print "Finished. (" + str(end - start) + "s)"
    # Matfile output
    if printMat:
        print
        print "Input:"
        start = time.time()
        __printMat(mat)
        end = time.time()
        print "End Input (" + str(end - start) + "s)"
        print
    #Conversion
    print "Converting TestResult (1/7)...",
    start = time.time()
    crtita = {"TestResult":[], "EnvInfo":[], "Summary":[], "TestAvailableOutput":[], "StatusInfo":[], "PreTriggerLogOutput":[], "TestrunConfig":[]}
    crtita["TestResult"] = __GenerateTestResult(mat["testdata"][0])
    end = time.time()
    print "Finished. (" + str(end - start) + "s)"
    print "Converting EnvInfo (2/7)...",
    start = time.time()
    crtita["EnvInfo"] = __GenerateEnvInfo(mat["testdata"])
    end = time.time()
    print "Finished. (" + str(end - start) + "s)"
    print "Converting Summary (3/7)...",
    start = time.time()
    crtita["Summary"] = __GenerateSummary(mat["testdata"][0])
    end = time.time()
    print "Finished. (" + str(end - start) + "s)"
    print "Converting TestAvailableOutput (4/7)...",
    start = time.time()
    crtita["TestAvailableOutput"] = __GenerateTestAvailableOutput(mat["testdata"])
    end = time.time()
    print "Finished. (" + str(end - start) + "s)"
    print "Converting StatusInfo (5/7)...",
    start = time.time()
    crtita["StatusInfo"] = __GenerateStatusInfo(mat["testdata"])
    end = time.time()
    print "Finished. (" + str(end - start) + "s)"
    print "Converting PreTriggerLogOutput (6/7)...",
    start = time.time()
    crtita["PreTriggerLogOutput"] = __GeneratePreTriggerLogOutput(mat["testdata"])
    end = time.time()
    print "Finished. (" + str(end - start) + "s)"
    print "Converting TestrunConfig (7/7)...",
    start = time.time()
    crtita["TestrunConfig"] = __GenerateTestrunConfig(mat["testdata"], __getLabelFromDir(matfile))
    end = time.time()
    print "Finished. (" + str(end - start) + "s)"
    print
    #End Conversion
    convend = time.time()
    print "--- Finished conversion. (" + str(convend - convstart) + "s) ---"
    # Result Output
    if printResult:
        print
        print "--- Result ---"
        print
        __printCRTITA(crtita, 1, maxlength)
        print
        print "--- End Result ---"
    return crtita

def __GenerateTestResult(td):
    """Generates the TestResult part of a CRTITA structure from the given testdata part of an RTITE mat-result-file"""
    # create empty structure
    tr = {}
    # for entryStatus, currently only Passed, since it is not known whether the order is correct
    statusBefore = "Passed"
    # Test only
    #print "### TEST ###", td["result"][0]["script"][0][0][0][0]["error"]
    # for each script
    for script in td["result"][0]["script"][0][0][0]:
        # empty structure
        tr[str(script["name"][0])] = [{"comment":"", "crashHookLog":"", "disableMsg":"", "exitHook":"", "entryHookLog":"", "crashTimeout":0, "testDuration":"", "exceptMsg":"", "crashHook":"", "templateVersion":"", "frameworkInitLog":"", "entryStatus":"", "abortMsg":"", "execTime":"", "status":0, "exitTimeout":0, "logDataList":[], "entryHook":"", "repetition":0, "tcList":[], "entryTimeout":0, "hookset":"", "frameWorkPostLog":"", "output":"", "exitStatus":"", "exitHookLog":"", "scriptDisabled":0}]
        # entrystatus set via statusBefore variable (=status of script that ran before)
        tr[str(script["name"][0])][0]["entryStatus"] = statusBefore
        # execTime placeholder
        tr[str(script["name"][0])][0]["execTime"] = "[00][00:00:00]"
        # testDuration Placeholder
        tr[str(script["name"][0])][0]["testDuration"] = "00.00 Sek"
        # direct mapping
        tr[str(script["name"][0])][0]["status"] = int(script["status"][0][0])
        # direct mapping
        tr[str(script["name"][0])][0]["comment"] = str("" if len(script["comment"]) < 1 else script["comment"][0])
        # nearly direct mapping (from int to string representation)
        tr[str(script["name"][0])][0]["exitStatus"] = "Passed" if script["status"][0][0] == 0 else ("Failed" if script["status"][0][0] == 1 else "Aborted")
        # generate cumulated output of all stages
        output = ""
        for info in script["stage_info"][0]:
            output += "" if len(info[5]) < 1 else (unicode(info[5][0]).encode("utf-8", "ignore") + "\n")
        tr[str(script["name"][0])][0]["output"] = output
        # create testcase entry for each error, enumerated and named like "F<number>_<scriptname>"
        # userData contains exec_error information
        num = 0
        for stage in script["stage_info"][0]: #@UnusedVariable
            dictt = {"status":0, "ScreenShots":[], "tcName":"", "tcNum":0, "userData":{}}
            # Wenn kein error-Eintrag vorhanden, stage passed
            tsf = int(script["error"][num]["teststage_failed"][0][0][0]) if len(script["error"]) > num else 100
            tsf = 100 if tsf < 0 else tsf
            dictt["status"] = 0 if (tsf > num and num <= script["test_depth_max"][0][0]) else (1 if tsf == num else (2 if num <= script["test_depth_max"][0][0] else 4))
            dictt["tcName"] = "Stage" + str(num) + "_" + str(script["name"][0])
            dictt["tcNum"] = num
            #dictt["userData"]["stageinfo"]=str(stage["output"])[10:30]
            tr[str(script["name"][0])][0]["tcList"].append(dictt)
            num += 1
    return tr

def __GenerateEnvInfo(td):
    """Generates the EnvInfo part of a CRTITA result file from the given testdata part of an RTITE mat-result-file"""
    # create empty structure
    env = {"1CRTITA package version":"", "2Frame version":"", "3Extensions":"", "4Libraries":"", "5Python version":"", "6Operating system":"", "7DSPACE_ROOT":""}
    # direct mapping
    env["5Python version"] = str(td["environment"][0][0][0]["swver"][0][0][0]["pytools"][0])
    # direct mapping
    env["6Operating system"] = str(td["environment"][0][0][0]["swver"][0][0][0]["operating_system"][0])
    # direct mapping
    env["7DSPACE_ROOT"] = str(td["environment"][0][0][0]["swroot"][0][0][0]["dspace"][0])
    return env

def __GenerateSummary(td):
    """Generates the summary part of a CRTITA result file from the given testdata part of an RTITE mat-result-file"""
    # create empty structure
    summ = {"Number of scripts not executed":0, "Testrun aborted":0, "General status of processed scripts":0, "Number of scripts processed":0, "Start time":"starttime", "Number of scripts failed":0, "End time":"endtime", "Number of scripts passed":0, "General status of repeated scripts":0, "Number of scripts in job":0}
    # not executed scripts equal scripts in job-executed scripts
    summ["Number of scripts not executed"] = int(td["result"][0]["scripts_in_job_numof"][0][0][0][0] - td["result"][0]["scripts_executed_numof"][0][0][0][0])
    # run aborted if aborted at any teststage
    summ["Testrun aborted"] = 1 if (td["result"][0]["job_aborted_at_idx"][0][0][0][0] > 0) else 0
    # status = 0 if passed, 1 if any failed but not aborted, 2 if aborted
    summ["General status of processed scripts"] = 1 if (td["result"][0]["scripts_failed_numof"][0][0][0][0] > 0) else 0
    summ["General status of processed scripts"] = 2 if (td["result"][0]["job_aborted_at_idx"][0][0][0][0] > 0) else summ["General status of processed scripts"]
    # direct mapping
    summ["Number of scripts processed"] = int(td["result"][0]["scripts_executed_numof"][0][0][0][0])
    # mapping using strftime to format the time from time_start
    datetmp = td["result"][0]["time_start"][0][0][0].split("-")
    timetmp = td["result"][0]["time_start"][0][0][0][td["result"][0]["time_start"][0][0][0].find(":") - 2:]
    ts = timetmp.split(":")
    tmpd = dict((v, k) for k, v in enumerate(calendar.month_abbr))
    summ["Start time"] = time.strftime("%a, %d %b %Y %H:%M:%S", (int(datetmp[2][:4]), int(tmpd[datetmp[1]]), int(datetmp[0]), int(ts[0]), int(ts[1]), int(ts[2]), datetime.date(int(datetmp[2][:4]), int(tmpd[datetmp[1]]), int(datetmp[0])).weekday(), 0, 0))
    ##print "Mapped 'Summary.Start time': from '", td["result"][0]["time_start"][0][0][0], "' (time_start) to '", summ["Start time"],"'"
    # direct mapping
    summ["Number of scripts failed"] = int(td["result"][0]["scripts_failed_numof"][0][0][0][0])
    # mapping using strftime to format the time from time_finish
    datetmp = td["result"][0]["time_finish"][0][0][0].split("-")
    timetmp = td["result"][0]["time_finish"][0][0][0][td["result"][0]["time_finish"][0][0][0].find(":") - 2:]
    ts = timetmp.split(":")
    summ["End time"] = time.strftime("%a, %d %b %Y %H:%M:%S", (int(datetmp[2][:4]), int(tmpd[datetmp[1]]), int(datetmp[0]), int(ts[0]), int(ts[1]), int(ts[2]), datetime.date(int(datetmp[2][:4]), int(tmpd[datetmp[1]]), int(datetmp[0])).weekday(), 0, 0))
    # passed scripts numof equals executed scripts-failed scripts
    summ["Number of scripts passed"] = int(td["result"][0]["scripts_executed_numof"][0][0][0][0] - td["result"][0]["scripts_failed_numof"][0][0][0][0])
    # placeholder, since no such information is available
    summ["General status of repeated scripts"] = -2
    # direct mapping
    summ["Number of scripts in job"] = int(td["result"][0]["scripts_in_job_numof"][0][0][0][0])
    return summ

def __GenerateTestAvailableOutput(td):
    """Generates the TestAvailableOutput part of a CRTITA result file from the given testdata part of an RTITE mat-result-file"""
    return []

def __GenerateStatusInfo(td):
    """Generates the StatusInfo part of a CRTITA result file from the given testdata part of an RTITE mat-result-file"""
    return []

def __GeneratePreTriggerLogOutput(td):
    """Generates the PreTriggerLogOutput part of a CRTITA result file from the given testdata part of an RTITE mat-result-file"""
    return ""

def __GenerateTestrunConfig(td, label):
    """Generates the TestRunConfig part of a CRTITA result file from the given testdata part of an RTITE mat-result-file"""
    # create empty structure
    trc = {"ReportChecked":0, "TestSuite":"", "TSPreTriggerEnabled":"", "SearchPath":[], "TestDescription":"", "CloseScriptProcessesEnabled":0, "ResumeChecked":0, "ReportDir":"", "ResumeDir":"", "Exclusive Tests":[], "Repeat Tests":"", "TestScriptCtrlParameter":{}, "TestMode":"", "ShowWindowChecked":0, "TestScriptParameter":{}, "ExcludedTests":[], "TestWorkRoot":"", "TSEnvironmentInfo":""}
    # direct mapping
    trc["RepeatTests"] = "" if len(td[0]["teparam"][0]["repeat_failed_tests"][0][0]) < 1 else td[0]["teparam"][0]["repeat_failed_tests"][0][0][0]
    # empty structure
    trc["TestScriptCtrlParameter"] = {"TargetCompiling":"", "RealTimeHW":"", "MATLAB":"", "Specific_TestEnvironment_Scenario":""}
    # direct mapping from really and unused excluded tests
    for test in (td["teparam"][0][0][0][0]["really_excluded_tests"] | td["teparam"][0][0][0][0]["unused_excluded_tests"]):
        trc["ExcludedTests"].append(test[0])
    # direct mapping from comment
    trc["TestDescription"] = "" if len(td["teparam"][0][0][0][0]["comment"]) < 1 else str(td["teparam"][0][0][0][0]["comment"][0])
    # CRTI-BTP specific import parameter (refer to MichaelRo's changes to WRV-Importer)
    trc["TestScriptParameter"]["TEST_DEPARTMENT"] = "CRTI_BTP"
    trc["TestScriptParameter"]["TEST_LABEL"] = label
    return trc

def __GenerateConfTxt(matfilepath, destlocation):
    """Creates a Conf.txt file in the given location from the given matfile"""
    print "--- Generating Conf.txt ---"
    print
    print "Loading Matfile \"" + matfilepath + "\"...",
    # Load matfile
    mat = scipy.io.matlab.loadmat(matfilepath)
    print "Finished."
    print
    # Get creation time of matfile
    statResult = os.stat(matfilepath)
    resultCreationTime = min(statResult.st_atime, statResult.st_mtime, statResult.st_ctime)
    # Write Conf.txt
    f = open(os.path.join(destlocation, "Conf.txt"), "w")
    print "Writing Conf.txt (\"" + os.path.join(destlocation, "Conf.txt") + "\")...",
    # Productname from path
    print >> f, 'PRODUCTNAME=' + os.path.dirname(matfilepath).split("\\")[-4]
    # Matlab version from matfile
    print >> f, 'Matlab=' + mat["testdata"]["environment"][0][0][0]["swver"][0][0][0]["matlab_short"][0]
    # Buildroot from path and timestamp
    print >> f, 'BuildRoot=' + __getBuildRootFromDir(matfilepath, resultCreationTime)
    f.close()
    print "Finished."
    print
    print "--- Finished Conf.txt generation ---"

def __getBuildRootFromDir(matfilepath, timeStamp):
    """Returns the buildroot to be used by wrv, generated from the location of the result file"""
    try:
        dirstr = os.path.dirname(matfilepath)
        dirs = dirstr.split('\\')
        version = dirs[-5].split('_')
        r = os.path.join('\\'.join(dirs[:-5]), version[2], version[1], time.strftime('%Y-%m-%d', time.localtime(timeStamp)))
    except IndexError:
        r = ""
        print
        print "Error gathering BuildRoot for \"" + matfilepath + "\". Conf.txt will be incomplete."
    return r

# get label from dir, BTP specific
def __getLabelFromDir(matfilepath):
    rtixxx = os.path.basename(matfilepath).split("_")[-1]
    rtixxx = rtixxx[:len(rtixxx) - 4]
    dirs = matfilepath.split('\\')[-6:-1]
    label = dirs[0][5:] + ' ' + dirs[1] + ' ' + dirs[3] + " " + rtixxx
    if len(label) > 38:
        print
        print "WARNING: Length of TEST_LABEL exceeds 38 characters! WRVImporter will cut the end!"
        print "TEST_LABEL:", label
        print
    return label

# Main functionality (called when run as a single script)
if __name__ == '__main__':
    printMat = False
    printResult = False
    GenerateConf = True
    MaxLineLength = 100
    if len(sys.argv) > 2:
        matfileArguments = str(sys.argv[1])
        matfiles = matfileArguments.rsplit(";")
        destination = str(sys.argv[2])
        if len(sys.argv) > 3:
            options = str(sys.argv[3])
            printMat = (options.count("-printmat") > 0)
            printResult = (options.count("-printresult") > 0)
            GenerateConf = not (options.count("-noconf") > 0)
            if options.count("-maxlength=") > 0:
                MaxLineLength = int(str(options.partition("-maxlength=")[2]).partition(" ")[0])
        found = True
    else:
        print "You have to start this Converter with arguments!"
        print "Call it like python Converter.py \"<rootfolder1>;<rootfolder2>;...\" \"<destinationfolder>\" \"<options>\"."
        print "Options are -printmat, -printresult, -noconf and -maxlength=<number>."
        found = False
    if found:
        print "Starting with these settings:"
        print "Print Matfiles:", printMat
        print "Print Resultfiles:", printResult
        print "Generate Conf.txt:", GenerateConf
        print "Maximum Output Line Length:", MaxLineLength
        print
        for m in matfiles:
            convertAndSaveMany(m, destination, printMat, printResult, GenerateConf, MaxLineLength)
