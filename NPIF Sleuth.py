#-------------------------------------------------------------------------
# Name:         NPIF Sleuth
# Purpose:      print information about a 7023 file. Includes:
#               - Summary of tables (txt file)
#               - detail on tables, and table contents (csv file)
#               - basic analysis results (txt file)
#
# Author:      sfhelsdon-dstl
# Originally Created:     02/07/2013
# 
############################################################################
#
# Intellectual Property Rights
#
# The MIT License (MIT)
#
# Copyright (c) 2018 Dstl
# 
# Permission is hereby granted, free of charge, to any person obtaining a 
# copy of this software and associated documentation files (the "Software"), 
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, 
# and/or sell copies of the Software, and to permit persons to whom the 
# Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL 
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER 
# DEALINGS IN THE SOFTWARE.
#
#-------------------------------------------------------------------------

from NPIF import *
from S7023_GUI import *


def NPIF_Extract(fname):
    retstring = None
    # Create Tablelist Object
    a = Tablelist()
    #
    # check file looks 7023 like and can be opened
    if a.Check_Is_7023_File(fname) is False:
        retstring = "Do not recognise:\n" + str(fname) + "\nas a valid 7023 file"
        return retstring
    #
    # get filename with no extension on the end
    noext = os.path.splitext(fname)[0]
    # make names for output files
    summaryout = noext + '_summary.txt'
    tablesout = noext + '_tables.csv'
    testsout = noext + '_tests.txt'
    #
    # open output files for writing
    try:
        sout = open(summaryout, 'w')
    except IOError:
        retstring = "Unable to Open output file:\n" + str(summaryout) + "\nCheck it is not open in another program and you can write to that location."
        return retstring
    try:
        tabout = open(tablesout, 'w')
    except IOError:
        retstring = "Unable to Open output file:\n" + str(tablesout) + "\nCheck it is not open in another program and you can write to that location."
        return retstring
    try:
        tstout = open(testsout, 'w')
    except IOError:
        retstring = "Unable to Open output file:\n" + str(testsout) + "\nCheck it is not open in another program and you can write to that location."
        return retstring
    #
    # read in the file
    a.Open_7023_File(fname)
    # add contents to 1st output file (summary)
    a.Print_Basic_File_Data(obuf=sout)
    sout.close()
    # add contents to 2nd output file (csv detail)
    a.Print_All_Tables(obuf=tabout, detail=True, strictcsv=True)
    tabout.close()
    # add contents to 3rd output file (simple analysis)
    a.file_error_checks()
    a.printallerrorssorted(obuf=tstout)
    tstout.close()
    #
    return retstring


def main():
    if len(sys.argv) > 1:
        # Use specified file name if provided
        fname = sys.argv[1]
    else:
        # Use GUI
        fname = Get7023_Filename()
    # check this looks like a 7023 file
    retval = NPIF_Extract(fname)
    if retval is not None:
        Do7023_ErrorBox(retval)
    # all done

if __name__ == '__main__':
    main()
