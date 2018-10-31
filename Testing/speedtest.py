#-------------------------------------------------------------------------
# Name:         speedtest
# Purpose:      profiling of code
#
# Author:      sfhelsdon-dstl
#
############################################################################
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
"""
Test code for the NPIF module.
""" 

import NPIF
import cProfile
import time

def runlots():
    """
    Runs a standard analysis over the set of golden files. prints time per file and total time.
    Also profiles code
    """
    
    baselocation = "U:\\My Documents\\goldentest\\"
    
    goldenlist = ["frame-8.7023",
                  "line-8.7023",
                  "64-sensors.7023",
                  "pushbroom-10.7023",
                  "frame-24.7023",
                  "line-12.7023",
                  "pan-frame-16.7023",
                  "step-frame-8.7023",
                  "frame-10.7023"]
    
    allfiles = []
    for f in goldenlist:
        allfiles.append(baselocation + f)

    start = time.time()

    for f in allfiles :
        lstart = time.time()
        print(f)
        NPIF.Do_7023_Full(f)
        lend = time.time()
        print("...",lend - lstart,"seconds")
        
    end = time.time()
    print("Total Time",end - start,"seconds")
    

if __name__ == '__main__':
    cProfile.run("runlots()")
    #runlots()
    #
    