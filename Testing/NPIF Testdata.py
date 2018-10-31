#-------------------------------------------------------------------------------
# Name:         NPIF Testdata
# Purpose:      Create some crude testdata for the NPIF code. Unfortunately lots
#				of Hex in code below...(the standard has lots of Hex in it)
#				
#
# Author:       sfhelsdon-dstl
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
#-------------------------------------------------------------------------------
#
# NOTE that some of the test cases require access to the 7023 Golden files
# edit the location of the appropriate files in the lines below
#
# enter the location of the three golden files here
# first the file: 64-sensors.7023
f64sensors_GOLDEN = "U:\\My Documents\\64-sensors.7023"
# second the file: line-8.7023
fline8_GOLDEN = 'U:\\My Documents\\line-8.7023'
# third the file: step-frame-8.7023
fstepframe8_GOLDEN = 'U:\\My Documents\\step-frame-8.7023'
# fourth the file: pan-frame-16.7023
fpanframe16_GOLDEN = 'U:\\My Documents\\pan-frame-16.7023'
# destination folder for generated files
NPIF_data_folder_out = 'U:\\My Documents\\npiftest'

import sys
if '../' not in sys.path:
    sys.path.append('../')

from NPIF import *


def Do_7023_FullX(fname):
    # Create Tablelist Object
    a = Tablelist()
    # read in the file
    a.Open_7023_File(fname)
    # add contents to 1st output file (summary)
    a.Summarise_7023_Contents()
    # add contents to 2nd output file (csv detail)
    a.Print_All_Tables_Neat(detail=True)
    # add contents to 3rd output file (simple analysis)
    a.Do_All_7023_Checks()
    #


def maketestf():
    """
    Crude function to generate sample packet for every table type.

    Extracts from Golden Files where possible, and makes up the rest.
	Locations of the golden files are hardcoded below. Fix this later.
    """
    # temporary function
    #
    qqq=NPIF()
    edition=b"\x04"
    flags=b"\x00"
    segnum=b"\x02"
    sa=b"\x20" # groupid
    dfa=b"\x00\x41\x00\xbb" # groupid
    size=b"\x00\x00\x00\x06"
    dfn=b"\x00\x00\x00\xee"
    time=b"\x00\x00\x00\x00\x12\x34\x56\x78"
    sync=b"\x00"
    reserved=b"\x00\x00\x00\x00\x00"
    crc=b"\xab\xcd"
    data=b"\x00\x02\x03\x00\x05\x09"

    sensorgrouping=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    sa=b"\x3f"
    dfa=b"\x00\x00\x00\xbb"
    size=b"\x00\x00\x00\x0f"
    data=b"\x00"*15
    userdefined=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    sa=b"\x50"
    dfa=b"\x00\x00\x00\x30"
    size=b"\x00\x00\x00\x48"
    data=struct.pack('>ddddddddd', 1.0, 1.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0)
    compsensatt=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    sa=b"\x50"
    dfa=b"\x00\x00\x00\x53"
    size=b"\x00\x00\x00\x18"
    data=struct.pack('>ddd', 11.0, 12.0, 13.0)
    gimbpos=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    sa=b"\x50"
    dfa=b"\x00\x00\x00\x72"
    size=b"\x00\x00\x00\x48"
    data=struct.pack('>ddddddddd', 1.0, 1.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0)
    compgimbatt=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    sa=b"\x50"
    dfa=b"\x00\x00\x10\x10"
    size=b"\x00\x00\x00\x13"
    data=b"\x00\x0c\x00\x20\x03\x20\x03\x0c\x00\x20\x03\x20\x03\x0c\x00\x20\x03\x20\x03"
    senssampcoorddes=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    sa=b"\x50"
    dfa=b"\x00\x00\x10\x20"
    size=b"\x00\x00\x00\x07"
    data=b"\x00\x00\x00\x00\x00\x00\x00"
    senssamptimedes=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    sa=b"\x55"
    dfa=b"\x00\x01\x00\x01"
    size=b"\x00\x00\x00\x1d"
    data=b"\x00\x00\x00\xff\x00\x00\x00\xff\x00\x00\x00\x40\x00\x00\x00\x80\x00\x00\x00\x80\x00\x05\x01\x00\x10\x00\x08\x04\x02"
    radsendes=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    sa=b"\x55"
    dfa=b"\x00\x01\x03\x00"
    size=b"\x00\x00\x00\x21"
    data=struct.pack('>dddd', 1.5, 2.5, 3.5, 4.5)+b"\x01"
    radcolplngeo=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    sa=b"\x55"
    dfa=b"\x00\x01\x03\x01"
    size=b"\x00\x00\x00\x48"
    data=struct.pack('>dd', math.pi/4, math.pi/4)+b"\xff"*24+struct.pack('>dddd', 1.1, 2.1, 3.1, 4.1)
    reftrack=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    sa=b"\x55"
    dfa=b"\x00\x01\x03\x02"
    size=b"\x00\x00\x00\xe2"
    data=struct.pack('>ddddddddddd', 1.1,2.1,3.1,4.1,5.1,6.1,7.1,8.1,9.1,10.1,11.1)+b"\xff"*8*15 + struct.pack('>dd', 0.5, 0.5)+b"\x02\x01"
    rectimgeo=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    sa=b"\x56"
    dfa=b"\x00\x01\x03\x03"
    size=b"\x00\x00\x00\x19"
    data=struct.pack('>dd', 0.0,0.0)+b"\x00\x01\xff\xff\x00\x03\xff\xff\x00"
    virtualsendef=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    sa=b"\x55"
    dfa=b"\x00\x01\x03\x04"
    size=b"\x00\x00\x00\x7a"
    data=struct.pack('>ddddddddddddd', 1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0)+b"\x00\x00\x00\x0a\x00\x0a\x00\x0a\x40\x00\x01\x02\x03\x04\x05\x06\x07\x08"
    radarparam=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    sa=b"\x55"
    dfa=b"\x00\x01\x03\x05"
    size=b"\x00\x00\x00\x17"
    data=struct.pack('>dd', 1.0,1.0)+b"\x00\x00\x00\x0a\x01\x02\x01"
    isar=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    sa=b"\x55"
    dfa=b"\x00\x01\x10\x00"
    size=b"\x00\x00\x00\x53"
    data=b"\x0c\x00\x00\x00\x00\x00\x00\x02"+struct.pack('>ddddddddd', 1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0)+b"\x01\x03\x00"
    radel=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    sa=b"\xbc"
    dfa=b"\x00\x00\x00\x10"
    size=b"\x00\x00\x00\x28"
    data = b"\x00" * 40
    sensampx=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    dfa=b"\x00\x00\x00\x20"
    sensampy=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    dfa=b"\x00\x00\x00\x30"
    sensampz=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    dfa=b"\x00\x00\x00\x50"
    sensampt=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    dfa=b"\x00\x00\x00\x60"
    gmti=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    dfa=b"\x00\x00\x00\x70"
    mi=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    dfa=b"\x00\x00\x00\x80"
    size=b"\x00\x00\x00\x08"
    data=struct.pack('>d', 1.0)
    rangef=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    sa=b"\x55"
    dfa=b"\x00\x00\x01\x03"
    size=b"\x00\x00\x00\x09"
    data=b"\x01\x00\x08\x00\x40\x00\x20\x01\x0a"
    j2kdes=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    # finally jpeg2000 index table
    sa=b"\x60"
    dfa=b"\x00\x00\x01\x04"
    size=b"\x00\x00\x00\x28"
    data = b"\x00" * 40
    j2kindex=qqq.SYNC_FIELD+edition+flags+segnum+sa+dfa+size+dfn+time+sync+reserved+crc+data
    #
    #
    line8=Tablelist()
    sen64=Tablelist()
    panf16=Tablelist()
	## Hard coded values follow Golden Files
    f2 = fline8_GOLDEN
    f3 = f64sensors_GOLDEN
    f7 = fpanframe16_GOLDEN
    line8.Open_7023_File(f2)
    sen64.Open_7023_File(f3)
    panf16.Open_7023_File(f7)
    #64 sen
    p64=[9,1514,3032]
    #lin8
    p8=[0,1,2,3,4,12,13,14,15,16,17,20,21,22,23,24,25,26,27,28,29,30,31,32,34,15845,15846,15848]
    #panframe16
    p16=[10,13]
    #open the 3 files again
    fp8 = open(f2, 'rb')
    fp16 = open(f7, 'rb')
    fp64 = open(f3, 'rb')
    #
    newout = open(NPIF_data_folder_out + '\\test.7023', 'wb')
    for p in p16:
        start=panf16.packetstarts[p]
        plength=panf16.packets[p].hdr.claimlen
        fp16.seek(start)
        print("aaa", plength)
        mstr = fp16.read(plength)
        newout.write(mstr)
    for p in p64:
        start=sen64.packetstarts[p]
        plength=sen64.packets[p].hdr.claimlen
        fp64.seek(start)
        mstr = fp64.read(plength)
        newout.write(mstr)
    #
    newout.write(sensorgrouping)
    newout.write(userdefined)
    newout.write(compsensatt)
    newout.write(gimbpos)
    newout.write(compgimbatt)
    newout.write(senssampcoorddes)
    newout.write(senssamptimedes)
    newout.write(radsendes)
    newout.write(radcolplngeo)
    newout.write(reftrack)
    newout.write(rectimgeo)
    newout.write(virtualsendef)
    newout.write(radarparam)
    newout.write(isar)
    newout.write(radel)
    newout.write(sensampx)
    newout.write(sensampy)
    newout.write(sensampz)
    newout.write(sensampt)
    newout.write(gmti)
    newout.write(mi)
    newout.write(rangef)
    newout.write(j2kdes)
    newout.write(j2kindex)
    #
    for p in p8:
        start=line8.packetstarts[p]
        plength=line8.packets[p].hdr.claimlen
        fp8.seek(start)
        mstr = fp8.read(plength)
        newout.write(mstr)
    #
    fp8.close()
    fp64.close()
    fp16.close()
    newout.close()

def maketestf2():
    # make a dud file
    dud = open(NPIF_data_folder_out + '\\test2.7023', 'wb')
    mstr = b"\x00" * 1000
    dud.write(mstr)
    dud.close()

def maketestf3():
    # create a file that just repeats a few tables
    t1 = NPIF_data_folder_out + '\\test.7023'

    a = Tablelist()
    a.Open_7023_File(t1)
    wantedp=[29, 30, 31, 36, 40, 52, 53, 3, 29, 30, 31, 36, 40, 52, 53, 3, 29, 30, 31, 36, 40, 52, 53, 3, 51, 56]
    newout = open(NPIF_data_folder_out + '\\test3.7023', 'wb')
    oldtest = open(t1, 'rb')
    # put some dud bytes up front
    newout.write(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    for p in wantedp:
        start=a.packetstarts[p]
        length=a.packets[p].hdr.claimlen+3
        oldtest.seek(start)
        mstr = oldtest.read(length)
        newout.write(mstr)
    newout.close()
    oldtest.close()

def generate_test_samples():
    testfile = NPIF_data_folder_out + '/test.7023'
    a = Tablelist()
    a.Open_7023_File(testfile)
    outname = NPIF_data_folder_out + '/testPrint_All_Tables_Neat1.txt'
    outfile = open(outname, 'w')
    a.Print_All_Tables(detail=True, strictcsv=True, obuf=outfile)
    outfile.close()
    outname = NPIF_data_folder_out + '/testPrint_All_Tables_Neat2.txt'
    outfile = open(outname, 'w')
    a.Print_All_Tables(detail=False, strictcsv=True, obuf=outfile)
    outfile.close()
    outname = NPIF_data_folder_out + '/testPrint_Table_Summary.txt'
    outfile = open(outname, 'w')
    a.Print_Table_Summary(obuf=outfile)
    outfile.close()



def main():
	# make ./test.7023 - has one instance of every table. Values are not always sensible in them
	# but structurally they should be OK. 
    maketestf()
	#
	# make ./test2.7023 - This is just a dud file with no sensible 7023 content
    maketestf2()
	#
	# make ./test3.7023 - just has a few repeated 7023 tables, to check in one test that the 
	# number of tables are being counted correctly in some functions
    maketestf3()
	#
	# Generate some simple text outputs based on test.7023
    generate_test_samples()
	#


if __name__ == '__main__':
    main()
