#!/usr/bin/env python
#
# sas_utils: a set of Python utilities to use
# the SAS application via subprocess
#
# SASReturnObject: backbone of the SAS call
# call_SAS: invokes SAS via subprocess, handles log
# sas2csv: convert SAS7BDAT to csv file
# sasSQLVarMostFreq: calculate most frequent values
#   of SAS7BDAT variable
# exportSASMetadata: export metadata from SAS7BDAT

import os
import re
import subprocess
import tempfile
import csv
from datetime import datetime
from pprint import pprint


# from https://github.com/wharton/inlinesas
class SASReturnObject(object):
    def __init__(self, returncode, stdout, stderr):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        message = 'Call returned code ' + str(self.returncode) + '.\n'
        message += 'stdout: ' + self.stdout + '\n'
        message += 'stderr: ' + self.stderr + '\n'
        return message


# adapted from https://github.com/wharton/inlinesas
def call_SAS(code_as_str, log_location=None):
    """
    Call SAS from within a Python script.
    Usage:
    =======================================
    from inlinesas import call_SAS
    sascode = 'your SAS code as a string'
    result = call_SAS(sascode)

    # You can also specify a location (using absolute path) for the logfile.
    #
    # If no logfile location is specified, no logfile will be created.
    result = call_SAS(sascode, log_location='/path/to/file.log')
    =======================================
    You can access the returncode, stdout, and stderr of your SAS run:
    result.returncode
    result.stdout
    result.stderr

    """
    f = tempfile.NamedTemporaryFile(mode='w+t', delete=False)
    f.write(code_as_str)
    f.close()
    invocation = ['sas', '-noterminal', '-nonews', '-cpucount', '2', '-sysin', f.name]
    # '-memsize', 'MAX',
    if log_location:
        invocation = invocation + ['-log', log_location]
    else:
        invocation.append('-nolog')
    r = subprocess.Popen(invocation)
    # try:
    #     stdout, stderr = r.communicate(timeout=15)
    #     print(r.returncode, stdout, stderr)
    # except TimeoutExpired:
    #     r.kill()
    stdout, stderr = r.communicate()
    # print(r.returncode, stdout, stderr)
    # stdout, stderr = r.communicate()
    os.unlink(f.name)  # Remove the temporary SAS file
    return SASReturnObject(r.returncode, stdout, stderr)


# export subset of variables from a sas7bdat file
# to a pandas dataframe via a temporary csv on disk
def sas2csv(infile, outfile, logdir, sqltxt=''):
    if not os.path.exists(infile):
        raise IOError("Input file {} does not exist".format(infile))
    filedir = os.path.dirname(os.path.realpath(infile))
    filebase = os.path.basename(os.path.realpath(infile))
    filebase = re.sub('\.sas7bdat(.)*$', '', filebase)
    # print(filedir, filebase, outfile, logdir)
    # named temp file for sas log
    templog = tempfile.NamedTemporaryFile(
        mode='w+t', suffix='.log', dir=logdir, delete=False
    )
    # the file only needs to be used by SAS first
    templog.close()
    sasstring = 'libname datalib "' + filedir + '";\n\n'
    sasstring += 'proc sql;\n'
    sasstring += '    create view export as select * from datalib.'
    sasstring += filebase + '\n'
    sasstring += '    ' + sqltxt + ';\n'
    sasstring += 'quit;\n\n'
    sasstring += 'proc export data= export\n'
    sasstring += '    outfile="' + outfile + '"\n'
    sasstring += '    dbms=csv\n'
    sasstring += '    replace;\n'
    sasstring += 'quit;\n'
    print(sasstring)
    call_SAS(sasstring, log_location=templog.name)
    # with open(templog.name, 'r') as f:
    # print(f.read())
    os.unlink(templog.name)
    return None
    # todo - maybe pass back the log file instead of None


# export most frequent values of variable to a list using
# a temporary csv on disk
def sasSQLVarMostFreq(
    infile, varName, tempdir, logdir, valueLimit=10, noisy=False, nolog=False
):
    # for f in glob.glob(os.path.join(tempdir, '*')):
    #     os.remove(f)
    filedir = os.path.dirname(os.path.realpath(infile))
    filebase = os.path.basename(os.path.realpath(infile))
    filebase = re.sub('\.sas7bdat(.)*$', '', filebase)
    if noisy is True:
        print(filedir, filebase, logdir)
    # varliststr = ' '.join(varlist)
    # tempsas = os.path.join(tempdir, 'tempsas.sas')
    # named temp file for saved csv data
    tempcsv = tempfile.NamedTemporaryFile(
        mode='w+t', suffix='.csv', dir=tempdir, delete=False
    )
    # # the file only needs to be used by SAS first
    tempcsv.close()
    if nolog is False:
        # named temp file for sas log
        templog = tempfile.NamedTemporaryFile(
            mode='w+t', suffix='.log', dir=tempdir, delete=False
        )
        # print(templog)
        # the file only needs to be used by SAS first
        templog.close()
        logLocation = templog.name
    else:
        logLocation = None
    if noisy is True:
        print('SAS call')
    sasstring = 'libname datalib "' + filedir + '";\n\n'
    sasstring += 'proc sql outobs=' + str(valueLimit) + ';\n'
    sasstring += '    CREATE VIEW exportTable AS\n'
    sasstring += '    SELECT ' + varName + ', COUNT(' + varName + ') AS Frequency\n'
    sasstring += '    FROM datalib.' + filebase + '\n'
    sasstring += '    GROUP BY ' + varName + '\n'
    sasstring += '    ORDER BY Frequency DESC;\n'
    # SAS SQL flavor does not support the LIMIT operator
    sasstring += 'quit;\n\n'
    sasstring += 'proc export data= exportTable (obs=' + str(valueLimit) + ')\n'
    sasstring += '    outfile="' + tempcsv.name + '"\n'
    sasstring += '    dbms=csv\n'
    sasstring += '    replace;\n'
    sasstring += 'quit;\n'
    if noisy is True:
        print(sasstring)
    call_SAS(sasstring, log_location=logLocation)
    if noisy is True:
        print(locals())
    # print(result.returncode)
    # print(result.stdout)
    # print(result.stderr)
    # sascli = ('/usr/local/bin/sas -noterminal -nonews
    # -cpucount 4 -log ' + templog + ' -sysin ' + tempsas)
    # print(sascli)
    # sascomplete = subprocess.run(sascli, shell=True)
    # stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # stdout, stderr = sascomplete.communicate()
    # print('SAS return code: ', sascomplete.returncode, stdout, stderr)
    if nolog is False and noisy is True:
        with open(templog.name, 'r') as f:
            print(f.read())
    with open(tempcsv.name, 'r') as f:
        # read csv into list but skip header row
        csvlist = list(csv.reader(f))[1:]
    # delete both named temp files by name
    os.unlink(tempcsv.name)
    if nolog is False:
        os.unlink(templog.name)
    return csvlist
    # !!! Maybe pass back the log file instead of None


# export sas metadata using proc contents
def exportSASMetadata(infile, tempdir, noisy=False, nolog=False):
    filedir = os.path.dirname(os.path.realpath(infile))
    filebase = os.path.basename(os.path.realpath(infile))
    filebase = re.sub('\.sas7bdat(.)*$', '', filebase)
    if noisy:
        print(filedir, filebase, tempdir)
    tempcsv = tempfile.NamedTemporaryFile(
        mode='w+t', suffix='.csv', dir=tempdir, delete=False
    )
    # the file only needs to be used by SAS first
    tempcsv.close()
    templog = tempfile.NamedTemporaryFile(
        mode='w+t', suffix='.log', dir=tempdir, delete=False
    )
    # the file only needs to be used by SAS first
    templog.close()
    if noisy:
        print('SAS call')
    sasstring = 'libname datalib "' + filedir + '";\n\n'
    # run proc contents to produce metadata
    # the list of available metadata attributes is here:
    # https://support.sas.com/documentation/cdl/en/proc/61895/HTML/default/viewer.htm#a002473443.htm#a000085825
    sasstring += 'proc contents\n'
    sasstring += '    data=datalib.' + filebase + '\n'
    sasstring += '    memtype=data out=table_listing \n'
    sasstring += '    ;\n'
    sasstring += 'run;\n'
    sasstring += 'proc export data=table_listing\n'
    sasstring += '    outfile="' + tempcsv.name + '"\n'
    sasstring += '    dbms=csv\n'
    sasstring += '    replace;\n'
    sasstring += 'run;\n'
    if noisy:
        print(sasstring)
    call_SAS(sasstring, log_location=templog.name)
    # print(locals())
    if noisy:
        with open(templog.name, 'r') as f:
            print(f.read())
        with open(tempcsv.name, 'r') as f:
            print(f.read())
    datasetMetaDict = {}
    variableMetaList = []
    with open(tempcsv.name, 'r') as f:
        for i, row in enumerate(csv.DictReader(f)):
            if noisy:
                print(row)
            if 'fileNameSASHeader' not in datasetMetaDict:
                datasetMetaDict['fileNameSASHeader'] = row['MEMNAME']
                datasetMetaDict['fileLabelSASHeader'] = row['MEMLABEL']
                datasetMetaDict['fileRowCount'] = int(row['NOBS'])
                datasetMetaDict['fileDateCreated'] = row['CRDATE']
                datasetMetaDict['fileDateModified'] = row['MODATE']
                datasetMetaDict['fileSASRelease'] = row['ENGINE']
                for datefield in ['fileDateCreated', 'fileDateModified']:
                    datasetMetaDict[datefield] = datetime.strptime(
                        datasetMetaDict[datefield], '%d%b%y:%H:%M:%S'
                    )
            varDict = {}
            varDict['varName'] = row['NAME']
            varDict['varLabel'] = row['LABEL']
            # varDict['varDescription'] = row[]
            varDict['varFormat'] = row['TYPE']
            varDict['varSASFormat'] = row['FORMAT']
            varDict['varLength'] = int(row['LENGTH'])
            variableMetaList.append(varDict)
    datasetMetaDict['fileColumnCount'] = i + 1
    if noisy:
        pprint(datasetMetaDict)
        pprint(variableMetaList)
    os.unlink(templog.name)
    os.unlink(tempcsv.name)
    return (datasetMetaDict, variableMetaList)


def test():
    sasFileList = ['/path/to/file.sas7bdat']
    tempDir = os.path.dirname(os.path.realpath(__file__))
    for sasFile in sasFileList:
        sasout = sas2csv(sasFile, '/path/to/file.csv', tempDir)
        print(sasout)
        (a, b) = exportSASMetadata(sasFile, tempDir, noisy=False)
        pprint(a)
        pprint(b)
        varFreqVals = sasSQLVarMostFreq(sasFile, 'varName', tempDir, tempDir)
        print(varFreqVals)


if __name__ == '__main__':
    test()
