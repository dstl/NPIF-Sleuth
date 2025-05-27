#-------------------------------------------------------------------------
# Name:         NPIF Splitter
# Purpose:      split a 7023 file into multiple files (one per table)
#
# Based on NPIF Sleuth, by sfhelsdon-dstl
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


def NPIF_Split(fname):
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
    #
    # read in the file
    a.Open_7023_File(fname)
    tableIndex = 0
    for p in a.packets:
        tablefile = open(noext + "_table_" + str(tableIndex).zfill(4) + ".7023", 'wb')
        tablefile.write(NPIF.SYNC_FIELD)
        tablefile.write(p.hdr.serialise())
        tablefile.write(p.tdat.dataraw)
        tablefile.close()
        tableIndex += 1
    #
    return retstring


def main():
    fname = Get7023_Filename()
    # check this looks like a 7023 file
    retval = NPIF_Split(fname)
    if retval is not None:
        Do7023_ErrorBox(retval)
    # all done

if __name__ == '__main__':
    main()
