# -*- coding: utf-8 -*-
# ##############################################################################
#
#                       S Q S D B _ L o g g i n g
#
# A simple logging functions, errors are logged into a seperate file.
#
# Author: Marek Roehm
#
Date    = "04.03.2009"
Version =  "1.00.07"
"""
History:
    1.00.07 - MR - Anpassungen f�e DB
    1.00.06 - MR - Write Error into new folder
    1.00.05 - MR - Write Error into both logfiles
    1.00.04 - MR - Timestampe contains date
    1.00.03 - MR - Optional Traceback
    1.00.02 - MR - Optimize printing
    1.00.01 - MR - Add Traceback to logging
    1.00.00 - MR - First fully working version
"""
import _Configuration
import traceback
import win32api
import string
import time
import os

logPath = os.path.join(_Configuration.logPath, _Configuration.foldername)

SQSSFrameClassLogFilePath      = os.path.join(logPath, "CRTITA-DBImport.LOG.txt")

SQSSFrameClassLogFilePathError = os.path.join(logPath, "CRTITA-DBImport.ERROR.txt")

#print SQSSFrameClassLogFilePath
#print SQSSFrameClassLogFilePathError

def traceback2str():
    try:
        tmpFile = win32api.GetTempPath()+"traceback.tmp"

        f=open(tmpFile, 'w')
        traceback.print_exc(file=f)
        f.close()

        f=open(tmpFile, 'r')
        tb = f.readlines()
        f.close()

        tcb = ""
        if tb != "":
            for i in tb:
                tcb = tcb + i + "\n"
        else:
            tcb = "[None]"
    except:
        #print "Error opening tmp file.\n"
        #traceback.print_exc()
        
        # MichaelRo - not used
        # self.printLine(".\n")
        
        tcb = "[Error getting traceback]\n"

    return tcb

def timeStamp():
    t_tmp = time.localtime(time.time())
    h = ("00"+str(t_tmp[3]))[-2:]+":"+("00"+str(t_tmp[4]))[-2:]+":"+("00"+str(t_tmp[5]))[-2:]
    d = ("00"+str(t_tmp[2]))[-2:]+"."+("00"+str(t_tmp[1]))[-2:]+"."+("00"+str(t_tmp[0]))[-2:]

    return d+" "+h+"-"


def printLog(Fcn,text,label):
##    s = (Fcn+"                        ")[9:25]+" "+label+"> "
##
##    maxLen = 120
##
##    while text != "":
##        if len(text) > maxLen:
##            sp = string.rfind(text," ",0,maxLen)
##
##            if sp == -1:
##                sp = string.rfind(text,"\\",0,maxLen)
##            if sp == -1:
##                sp = string.rfind(text,"/",0,maxLen)
##            if sp == -1:
##                sp = maxLen
##
##            sp += 1
##            st = text[:sp]
##            text = text[sp:]
##        else:
##            st = text
##            text = ""
##
##        print s+st
##        s = "               "
    pass



#---------------------------------------------------------------------------
# Check if Logfile is larger than 10 mb
#

def checkFileSize(name,name2=None):
    try:
        if os.access(name,os.F_OK) and os.stat(name)[6] > 10485760:
            print name+" File larger than 10mb"
            i = 1
            while os.access(name+"_"+str(i)+".txt",os.F_OK) == True:
                i+=1
            os.rename(name,name+"_"+str(i)+".txt")

            if name2!=None:
                os.rename(name2,name2+"_"+str(i)+".txt")
    except:
        #print "Error renaming file!"
        #traceback.print_exc()
        pass




def debug(text, Level=0, Fcn="----------",NoTB = False):
    
    f = None
    logPath = os.path.join(_Configuration.logPath, _Configuration.foldername)

    SQSSFrameClassLogFilePath      = os.path.join(logPath, "CRTITA-DBImport.LOG.txt")

    SQSSFrameClassLogFilePathError = os.path.join(logPath, "CRTITA-DBImport.ERROR.txt")

    #---------------------------------------------------------------------------
    # Check if Logfile is larger than 10 mb
    #

    #print SQSSFrameClassLogFilePath
    #print SQSSFrameClassLogFilePathError

    checkFileSize(SQSSFrameClassLogFilePath, SQSSFrameClassLogFilePathError)
    checkFileSize(SQSSFrameClassLogFilePathError, SQSSFrameClassLogFilePath)



    #---------------------------------------------------------------------------
    # Write Data to Error Log
    #
    if Level != 0:
        printLog(timeStamp()+Fcn,text,"F.")

        if NoTB == False:
            tcb = traceback2str()
            tz = string.split(tcb,"\n")
            for z in tz:
                printLog("",z,"  ")

        if not os.path.exists (SQSSFrameClassLogFilePathError):
            f=open(SQSSFrameClassLogFilePathError, 'w+')
        else:
            f=open(SQSSFrameClassLogFilePathError, 'a')    

        try:
            f.write(timeStamp()+(Fcn+"             ")[:10] + " F.> " + text.encode("ascii","ignore") + "\n")
            f.write("-----------------------------------------------------------------------------\n")

            if NoTB == False:
                f.write(unicode(tcb) + "\n" + "-----------------------------------------------------------------------------\n")
        except:
            print traceback.print_exc()
            print "Error writing to file!"

        if not (f==None): f.close()

        if not os.path.exists (SQSSFrameClassLogFilePath):
            f=open(SQSSFrameClassLogFilePath, 'w+')
        else:
            f=open(SQSSFrameClassLogFilePath, 'a')
            
        try:
            f.write(timeStamp()+(Fcn+"             ")[:10] + " F.> " + text + "\n")
            f.write("-----------------------------------------------------------------------------\n")

            if NoTB == False:
                f.write(unicode(tcb) + "\n" + "-----------------------------------------------------------------------------\n")
        except:
            pass
            #print "Error writing to file!"

        if not (f==None): f.close()
    else:

        printLog(timeStamp()+Fcn,text,"OK")
        if not os.path.exists (SQSSFrameClassLogFilePath):
            f=open(SQSSFrameClassLogFilePath, 'w+')
        else:
            f=open(SQSSFrameClassLogFilePath, 'a+')

        try:
            f.write(timeStamp()+ (Fcn+"             ")[:10] + " OK> " + unicode(text) + "\n")
        except:
            #print "Error writing to file!"
            pass

        if not (f==None): f.close()

def debugLog(text, time, path):
    t = timeStamp().strip("-")

    logfile = os.path.join(path, time, "CRTITA-DBImport.DBTimelog." + time + ".csv")
    logfolder = os.path.join(path, time)
    if not os.path.exists (logfolder):
        os.mkdir(logfolder)
    if not os.path.exists (logfile):
        f = open(logfile, "w+")
    else:
        f = open(logfile, "a+")
    f.write(t + "; " + text + "\n")        
    f.flush()
    f.close()

def logging(message, path):
    logfile = os.path.join(path, "info.log")
    f = None
    if not os.path.exists (logfile):
        f = open(logfile, "w+")
    else:
        f = open(logfile, "a+")
    t = time.strftime("%d.%m.%Y %H:%M:%S\t") 
    f.write(t + message + "\n")
    f.flush()
    f.close()
'''
if __name__ == '__main__':
    for i in range(0,50):
        debug("Test",0,"Super!")
        debug("Test",-1,"Naja")
'''
