#-------------------------------------------------------------------------
# Name:         NPIF Test
# Purpose:      Unit tests for NPIF module
#
# Author:       sfhelsdon-dstl
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

# NOTE that some of the test cases require access to the 7023 Golden files
# edit the location of the appropriate files in the lines below

# enter the location of the three golden files here
# first the file: 64-sensors.7023
f64sensors_GOLDEN = "U:\\My Documents\\64-sensors.7023"
# second the file: line-8.7023
fline8_GOLDEN = 'U:\\My Documents\\line-8.7023'
# third the file: step-frame-8.7023
fstepframe8_GOLDEN = 'U:\\My Documents\\step-frame-8.7023'

import unittest
import struct
import binascii
import math
import os
import sys
import io
import difflib

if '../' not in sys.path:
    sys.path.append('../')

import NPIF


class TestNPIF_Error(unittest.TestCase):

    def setUp(self):
        self.edat = NPIF.NPIF_Error()

    def tearDown(self):
        pass

    def test_data(self):
        # check default values in data structure
        self.assertEqual(self.edat.errorcount, 0)
        self.assertEqual(self.edat.errorinfo, [])
        self.assertEqual(self.edat.maxerrorlevel, 0)

    def testadderror(self):
        # start with case ok values and check all looks ok
        testlvl = 2
        testtype = 20
        testtxt = "Test for errors"
        self.edat.adderror(testtype,testlvl,testtxt)
        self.assertEqual(self.edat.einfo(0)[2], testtxt)
        self.assertEqual(self.edat.einfo(0)[1], testlvl)
        self.assertEqual(self.edat.einfo(0)[0], testtype)
        self.assertEqual(self.edat.ecount(), 1)
        self.assertEqual(self.edat.emaxlvl(), testlvl)
        #
        testlvl2 = 99  # should get reset to ELVL_HIGH
        testtype2 = 2000  # should get reset to E_UNKNOWN
        testtxt2 = "Test for errors2"
        self.edat.adderror(testtype2,testlvl2,testtxt2)
        self.assertEqual(self.edat.einfo(1)[2], testtxt2)
        self.assertEqual(self.edat.einfo(1)[1], self.edat.ELVL_HIGH)
        self.assertEqual(self.edat.einfo(1)[0], self.edat.E_UNKNOWN)
        self.assertEqual(self.edat.ecount(), 2)
        self.assertEqual(self.edat.emaxlvl(), self.edat.ELVL_HIGH)

    def test_edict(self):
        # check that the set of entries in ETYPES matches the set of keys in
        # ETYPES_TXT
        a = set(self.edat.ETYPES)
        b = set(self.edat.ETYPES_TXT.keys())
        self.assertSetEqual(a,b)

    def testecount(self):
        # add a few errors and check the right number counted
        testlvl = 2
        testtype = 20
        testtxt = "Test for errors"
        self.edat.adderror(testtype,testlvl,testtxt)
        self.edat.adderror(testtype,testlvl,testtxt)
        self.edat.adderror(testtype,testlvl,testtxt)
        self.assertEqual(self.edat.ecount(), 3)

    def testeinfo(self):
        # add an error and check contents look ok
        testlvl = 1
        testtype = 10
        testtxt = "Test for errors"
        self.edat.adderror(testtype,testlvl,testtxt)
        self.assertEqual(self.edat.einfo(0)[2], testtxt)
        self.assertEqual(self.edat.einfo(0)[1], testlvl)
        self.assertEqual(self.edat.einfo(0)[0], testtype)
        self.assertEqual(self.edat.ecount(), 1)
        # add a few more and check things broadly look ok
        testlvl = 2
        testtype = 6
        testtxt = "Test for errors more"
        self.edat.adderror(testtype,testlvl,testtxt)
        self.edat.adderror(testtype,testlvl,testtxt)
        self.edat.adderror(testtype,testlvl,testtxt)
        self.edat.adderror(testtype,testlvl,testtxt)
        self.assertEqual(self.edat.ecount(), 5)
        self.assertEqual(self.edat.einfo(3)[2], testtxt)
        self.assertEqual(self.edat.einfo(3)[1], testlvl)
        self.assertEqual(self.edat.einfo(3)[0], testtype)
        # test some bad values
        self.assertEqual(self.edat.einfo(99),(None,None,None))
        self.assertEqual(self.edat.einfo(-1),(None,None,None))

    def testemaxlvl(self):
        # add an error and check contents look ok
        testlvl = 1
        testtype = 10
        testtxt = "Test for errors"
        self.edat.adderror(testtype,testlvl,testtxt)
        self.assertEqual(self.edat.emaxlvl(), testlvl)
        # add another of higher level and check it rises
        testlvl = 3
        self.edat.adderror(testtype,testlvl,testtxt)
        self.assertEqual(self.edat.emaxlvl(), testlvl)
        # add another of lower level and check number does not drop
        newtestlvl = 2
        self.edat.adderror(testtype,newtestlvl,testtxt)
        self.assertEqual(self.edat.emaxlvl(), testlvl)

    def testwhereerr(self):
        # add an error and check it is found correctly
        testlvl = 1
        testtype = 10
        testtxt = "Test for errors"
        self.edat.adderror(testtype,testlvl,testtxt)
        self.assertEqual(self.edat.whereerr(10), [0])
        # add bad value and check for empty list
        self.assertEqual(self.edat.whereerr(99999), [])
        # add some more errors of various value and check correct indices get
        # returned
        self.edat.adderror(testtype,testlvl,testtxt)
        testtype = 15
        self.edat.adderror(testtype,testlvl,testtxt)
        self.edat.adderror(testtype,testlvl,testtxt)
        testtype = 16
        self.edat.adderror(testtype,testlvl,testtxt)
        self.edat.adderror(testtype,testlvl,testtxt)
        testtype = 10
        self.edat.adderror(testtype,testlvl,testtxt)
        self.assertEqual(self.edat.whereerr(15), [2, 3])
        self.assertEqual(self.edat.whereerr(16), [4, 5])
        self.assertEqual(self.edat.whereerr(10), [0, 1, 6])

    def testprinterrors(self):
        # generate a warning and couple of errors
        obuf = io.StringIO()
        testlvl = 1
        testtype = 10
        testtxt = "Test for errors"
        self.edat.adderror(testtype,testlvl,testtxt)
        testlvl = 3
        self.edat.adderror(testtype,testlvl,testtxt)
        self.edat.adderror(testtype,testlvl,testtxt)
        # check the correct values get returned from the function
        w, e = self.edat.printerrors(obuf=obuf)
        self.assertEqual(w, 1)
        self.assertEqual(e, 2)
        # now check that the outputs written look like they have the correct
        # sort of info
        printed_data = obuf.getvalue()
        obuf.close()
        self.assertEqual(len(printed_data.split("ERROR:")), 3)
        self.assertEqual(len(printed_data.split("WARNING:")), 2)

    def testprinterrorsoftype(self):
        # create a mix of error information
        obuf = io.StringIO()
        obuf2 = io.StringIO()
        testlvl = 1
        testtype = 10
        testtxt = "Test for errors2"
        self.edat.adderror(testtype,testlvl,testtxt)
        testlvl = 3
        self.edat.adderror(testtype,testlvl,testtxt)
        self.edat.adderror(testtype,testlvl,testtxt)
        testtype = 11
        testlvl = 1
        self.edat.adderror(testtype,testlvl,testtxt)
        testlvl = 4
        self.edat.adderror(testtype,testlvl,testtxt)
        # now check that correct value get returned for testtype = 10
        w, e = self.edat.printerrorsoftype(10, obuf=obuf)
        self.assertEqual(w, 1)
        self.assertEqual(e, 2)
        # and again for testtype = 11
        w, e = self.edat.printerrorsoftype(11, obuf=obuf2)
        self.assertEqual(w, 1)
        self.assertEqual(e, 1)
        # now check that output data looks like what is expected
        printed_data = obuf.getvalue()
        obuf.close()
        printed_data2 = obuf2.getvalue()
        obuf2.close()
        self.assertEqual(len(printed_data.split("ERROR:")), 3)
        self.assertEqual(len(printed_data.split("WARNING:")), 2)
        self.assertEqual(len(printed_data2.split("ERROR:")), 2)
        self.assertEqual(len(printed_data2.split("WARNING:")), 2)


class TestNPIF_Header(unittest.TestCase):

    def setUp(self):
        self.Tabdata = NPIF.NPIF_Header()

    def tearDown(self):
        pass

    def test_datamodel(self):
        # check the default data model values are set up ok
        self.assertEqual(self.Tabdata.edition, None)
        self.assertEqual(self.Tabdata.compressflag, None)
        self.assertEqual(self.Tabdata.crcflag, None)
        self.assertEqual(self.Tabdata.ambleflag, None)
        self.assertEqual(self.Tabdata.segmentnum, None)
        self.assertEqual(self.Tabdata.sourceaddress, None)
        self.assertEqual(self.Tabdata.datafileaddress, None)
        self.assertEqual(self.Tabdata.datafilesize, None)
        self.assertEqual(self.Tabdata.datafilenum, None)
        self.assertEqual(self.Tabdata.timetag, None)
        self.assertEqual(self.Tabdata.synctype, None)
        self.assertEqual(self.Tabdata.reserved, None)
        self.assertEqual(self.Tabdata.headcrc, None)
        self.assertEqual(self.Tabdata.Requester_Idx_Num, None)
        self.assertEqual(self.Tabdata.Group_ID_Num, None)
        self.assertEqual(self.Tabdata.Event_ID_Num, None)
        self.assertEqual(self.Tabdata.Segment_ID_Num, None)
        self.assertEqual(self.Tabdata.Location_ID_Num, None)
        self.assertEqual(self.Tabdata.Target_ID_Num, None)
        self.assertEqual(self.Tabdata.Gimbal_ID_Num, None)
        self.assertEqual(self.Tabdata.Sensor_ID_Num, None)
        self.assertEqual(self.Tabdata.Platform_ID_Num, None)
        self.assertEqual(self.Tabdata.tablecode, 0)
        self.assertEqual(self.Tabdata.sourcecode, 0)
        self.assertEqual(self.Tabdata.totlen, None)
        self.assertEqual(self.Tabdata.claimlen, None)
        self.assertEqual(self.Tabdata.extraraw, None)
        self.assertEqual(self.Tabdata.packetnum, None)
        self.assertEqual(self.Tabdata.blockdataextract, False)
        self.assertEqual(self.Tabdata.tablename, None)
        self.assertTrue(hasattr(self.Tabdata, 'errors'))


class TestNPIF_DataContent(unittest.TestCase):

    def setUp(self):
        self.Tabdata = NPIF.NPIF_DataContent()

    def tearDown(self):
        pass

    def test_datamodel(self):
        # check the default data model values are set up ok
        self.assertEqual(self.Tabdata.dataraw, None)
        self.assertEqual(self.Tabdata.datacrc, None)
        self.assertEqual(self.Tabdata.numfieldsrepeating, None)
        self.assertEqual(self.Tabdata.numrepeats, None)
        self.assertEqual(self.Tabdata.fieldnames, None)
        self.assertEqual(self.Tabdata.fieldtypes, None)
        self.assertEqual(self.Tabdata.fieldfuncs, None)
        self.assertEqual(self.Tabdata.fieldlflags, None)
        self.assertEqual(self.Tabdata.fieldreqs, None)
        self.assertEqual(self.Tabdata.data_flens, None)
        self.assertEqual(self.Tabdata.tcontents, None)
        self.assertTrue(hasattr(self.Tabdata, 'errors'))


class TestNPIF(unittest.TestCase):

    def setUp(self):
        self.Tabdata = NPIF.NPIF()

    def test_datamodel(self):
        # check the default data model values are set up ok
        self.assertTrue(hasattr(self.Tabdata, 'hdr'))
        self.assertTrue(hasattr(self.Tabdata, 'tdat'))
        self.assertEqual(self.Tabdata.edition(), None)
        self.assertEqual(self.Tabdata.compressflag(), None)
        self.assertEqual(self.Tabdata.crcflag(), None)
        self.assertEqual(self.Tabdata.ambleflag(), None)
        self.assertEqual(self.Tabdata.segment(), None)
        self.assertEqual(self.Tabdata.sa(), None)
        self.assertEqual(self.Tabdata.dfa(), None)
        self.assertEqual(self.Tabdata.datasize(), None)
        self.assertEqual(self.Tabdata.dfn(), None)
        self.assertEqual(self.Tabdata.timetag(), None)
        self.assertEqual(self.Tabdata.synctype(), None)
        self.assertEqual(self.Tabdata.reserved(), None)
        self.assertEqual(self.Tabdata.headcrc(), None)
        self.assertEqual(self.Tabdata.Requester_Idx_Num(), None)
        self.assertEqual(self.Tabdata.Group_ID_Num(), None)
        self.assertEqual(self.Tabdata.Event_ID_Num(), None)
        self.assertEqual(self.Tabdata.Segment_ID_Num(), None)
        self.assertEqual(self.Tabdata.Location_ID_Num(), None)
        self.assertEqual(self.Tabdata.Target_ID_Num(), None)
        self.assertEqual(self.Tabdata.Gimbal_ID_Num(), None)
        self.assertEqual(self.Tabdata.Sensor_ID_Num(), None)
        self.assertEqual(self.Tabdata.Platform_ID_Num(), None)
        self.assertEqual(self.Tabdata.tablecode(), 0)
        self.assertEqual(self.Tabdata.sourcecode(), 0)
        self.assertEqual(self.Tabdata.totlen(), None)
        self.assertEqual(self.Tabdata.claimlen(), None)
        self.assertEqual(self.Tabdata.extraraw(), None)
        self.assertEqual(self.Tabdata.packetnum(), None)
        self.assertEqual(self.Tabdata.blockdataextract(), False)
        self.assertEqual(self.Tabdata.hdr.tablename, None)
        self.assertTrue(hasattr(self.Tabdata.hdr, 'errors'))
        # now in tdat bit
        self.assertEqual(self.Tabdata.dataraw(), None)
        self.assertEqual(self.Tabdata.datacrc(), None)
        self.assertEqual(self.Tabdata.numfieldsrepeating(), None)
        self.assertEqual(self.Tabdata.numrepeats(), None)
        self.assertEqual(self.Tabdata.fieldnames(), None)
        self.assertEqual(self.Tabdata.fieldtypes(), None)
        self.assertEqual(self.Tabdata.fieldfuncs(), None)
        self.assertEqual(self.Tabdata.fieldlflags(), None)
        self.assertEqual(self.Tabdata.fieldreqs(), None)
        self.assertEqual(self.Tabdata.data_flens(), None)
        self.assertEqual(self.Tabdata.tcontents(), None)
        self.assertTrue(hasattr(self.Tabdata.tdat, 'errors'))

    def test_constantsastuples(self):
        # check that the various dict constants are set up correctly with
        # all values as tuples
        for k in self.Tabdata.S7023_TABLE_SIZES:
            self.assertIsInstance(self.Tabdata.S7023_TABLE_SIZES[k],tuple)
        for k in self.Tabdata.S7023_FLD_LENGTHS:
            self.assertIsInstance(self.Tabdata.S7023_FLD_LENGTHS[k],tuple)
        for k in self.Tabdata.S7023_FLD_TYPES:
            self.assertIsInstance(self.Tabdata.S7023_FLD_TYPES[k],tuple)
        for k in self.Tabdata.S7023_FLD_REQS:
            self.assertIsInstance(self.Tabdata.S7023_FLD_REQS[k],tuple)
        for k in self.Tabdata.S7023_FLD_NAMES:
            self.assertIsInstance(self.Tabdata.S7023_FLD_NAMES[k],tuple)
        for k in self.Tabdata.S7023_FLD_LIST_FLAGS:
            self.assertIsInstance(self.Tabdata.S7023_FLD_LIST_FLAGS[k],tuple)
        for k in self.Tabdata.S7023_FLD_FUNCS:
            self.assertIsInstance(self.Tabdata.S7023_FLD_FUNCS[k],tuple)

    def test_samedictkeys(self):
        # check that the various dicts have the same core set of keys
        for k in self.Tabdata.S7023_DEFINED_TABLES:
            self.assertIn(
                k, self.Tabdata.S7023_TABLE_NAMES,
                msg=str(k) + " not in TABLE_NAMES")
            self.assertIn(
                k, self.Tabdata.S7023_TABLE_SIZES,
                msg=str(k) + " not in TABLE_SIZES")
            self.assertIn(
                k, self.Tabdata.S7023_FLD_LENGTHS,
                msg=str(k) + " not in FLD_LENGTHS")
            self.assertIn(
                k, self.Tabdata.S7023_FLD_TYPES,
                msg=str(k) + " not in FLD_TYPES")
            self.assertIn(
                k, self.Tabdata.S7023_FLD_REQS,
                msg=str(k) + " not in FLD_REQS")
            self.assertIn(
                k, self.Tabdata.S7023_FLD_NAMES,
                msg=str(k) + " not in FLD_NAMES")
            self.assertIn(
                k, self.Tabdata.S7023_FLD_LIST_FLAGS,
                msg=str(k) + " not in LIST_FLAGS")
            self.assertIn(
                k, self.Tabdata.S7023_FLD_FUNCS,
                msg=str(k) + " not in FLD_FUNCS")
            self.assertIn(
                k, self.Tabdata._VARIABLE_NAMES,
                msg=str(k) + " not in VAR_NAMES")

    def test_samelengthtuplesindicts(self):
        # check that the various dicts with data element tuple lists have the
        # same length tuples for each key
        for k in self.Tabdata.S7023_FLD_NAMES:
            mm = (len(self.Tabdata.S7023_FLD_NAMES[k]),k)
            self.assertEqual((len(self.Tabdata.S7023_FLD_TYPES[k]),k),mm)
            self.assertEqual((len(self.Tabdata.S7023_FLD_REQS[k]),k),mm)
            self.assertEqual((len(self.Tabdata.S7023_FLD_LIST_FLAGS[k]),k),mm)
            self.assertEqual((len(self.Tabdata.S7023_FLD_FUNCS[k]),k),mm)
            # field length data is a bit more awkward - test what we can
            if len(self.Tabdata.S7023_FLD_LENGTHS[k]) > 0:
                if self.Tabdata.S7023_FLD_LENGTHS[k][0] != 'v':
                    self.assertEqual(
                        (len(self.Tabdata.S7023_FLD_LENGTHS[k]),k),mm)

    def testedition(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_edition(4)
        self.assertEqual(self.Tabdata.edition(), 4)

    def testSet_edition(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_edition(3)
        self.assertEqual(self.Tabdata.edition(), 3)

    def testcompressflag(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_compressflag(1)
        self.assertEqual(self.Tabdata.compressflag(), 1)

    def testSet_compressflag(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_compressflag(0)
        self.assertEqual(self.Tabdata.compressflag(), 0)

    def testcrcflag(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_crcflag(1)
        self.assertEqual(self.Tabdata.crcflag(), 1)

    def testSet_crcflag(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_crcflag(0)
        self.assertEqual(self.Tabdata.crcflag(), 0)

    def testambleflag(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_ambleflag(1)
        self.assertEqual(self.Tabdata.ambleflag(), 1)

    def testSet_ambleflag(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_ambleflag(0)
        self.assertEqual(self.Tabdata.ambleflag(), 0)

    def testsegment(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_segment(5)
        self.assertEqual(self.Tabdata.segment(), 5)

    def testSet_segment(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_segment(1)
        self.assertEqual(self.Tabdata.segment(), 1)

    def testsa(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_sa(10)
        self.assertEqual(self.Tabdata.sa(), 10)

    def testSet_sa(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_sa(9)
        self.assertEqual(self.Tabdata.sa(), 9)

    def testdfa(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_dfa(20)
        self.assertEqual(self.Tabdata.dfa(), 20)

    def testSet_dfa(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_dfa(10)
        self.assertEqual(self.Tabdata.dfa(), 10)

    def testdatasize(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_datasize(300)
        self.assertEqual(self.Tabdata.datasize(), 300)

    def testSet_datasize(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_datasize(200)
        self.assertEqual(self.Tabdata.datasize(), 200)

    def testnocrcdatasize(self):
        # check two cases - one with the crc flag on (1) and one off (0)
        self.Tabdata.Set_datasize(200)
        self.Tabdata.Set_crcflag(1)
        self.assertEqual(self.Tabdata.nocrcdatasize(), 198)
        self.Tabdata.Set_crcflag(0)
        self.assertEqual(self.Tabdata.nocrcdatasize(), 200)

    def testdfn(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_dfn(9)
        self.assertEqual(self.Tabdata.dfn(), 9)

    def testSet_dfn(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_dfn(22)
        self.assertEqual(self.Tabdata.dfn(), 22)

    def testtimetag(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_timetag(1000)
        self.assertEqual(self.Tabdata.timetag(), 1000)

    def testSet_timetag(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_timetag(1200)
        self.assertEqual(self.Tabdata.timetag(), 1200)

    def testsynctype(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_synctype("None")
        self.assertEqual(self.Tabdata.synctype(), "None")

    def testSet_synctype(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_synctype("SUPER FRAME SYNC")
        self.assertEqual(self.Tabdata.synctype(), "SUPER FRAME SYNC")

    def testreserved(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_reserved("0000000000")
        self.assertEqual(self.Tabdata.reserved(), "0000000000")

    def testSet_reserved(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_reserved("0100000000")
        self.assertEqual(self.Tabdata.reserved(), "0100000000")

    def testheadcrc(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_headcrc("FFAD")
        self.assertEqual(self.Tabdata.headcrc(), "FFAD")

    def testSet_headcrc(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_headcrc("FFAC")
        self.assertEqual(self.Tabdata.headcrc(), "FFAC")

    def testRequester_Idx_Num(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_Requester_Idx_Num(1)
        self.assertEqual(self.Tabdata.Requester_Idx_Num(), 1)

    def testSet_Requester_Idx_Num(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_Requester_Idx_Num(2)
        self.assertEqual(self.Tabdata.Requester_Idx_Num(), 2)

    def testGroup_ID_Num(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_Group_ID_Num(1)
        self.assertEqual(self.Tabdata.Group_ID_Num(), 1)

    def testSet_Group_ID_Num(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_Group_ID_Num(3)
        self.assertEqual(self.Tabdata.Group_ID_Num(), 3)

    def testEvent_ID_Num(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_Event_ID_Num(1)
        self.assertEqual(self.Tabdata.Event_ID_Num(), 1)

    def testSet_Event_ID_Num(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_Event_ID_Num(100)
        self.assertEqual(self.Tabdata.Event_ID_Num(), 100)

    def testSegment_ID_Num(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_Segment_ID_Num(1)
        self.assertEqual(self.Tabdata.Segment_ID_Num(), 1)

    def testSet_Segment_ID_Num(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_Segment_ID_Num(4)
        self.assertEqual(self.Tabdata.Segment_ID_Num(), 4)

    def testLocation_ID_Num(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_Location_ID_Num(1)
        self.assertEqual(self.Tabdata.Location_ID_Num(), 1)

    def testSet_Location_ID_Num(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_Location_ID_Num(31)
        self.assertEqual(self.Tabdata.Location_ID_Num(), 31)

    def testTarget_ID_Num(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_Target_ID_Num(1)
        self.assertEqual(self.Tabdata.Target_ID_Num(), 1)

    def testSet_Target_ID_Num(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_Target_ID_Num(11)
        self.assertEqual(self.Tabdata.Target_ID_Num(), 11)

    def testGimbal_ID_Num(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_Gimbal_ID_Num(15)
        self.assertEqual(self.Tabdata.Gimbal_ID_Num(), 15)

    def testSet_Gimbal_ID_Num(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_Gimbal_ID_Num(5)
        self.assertEqual(self.Tabdata.Gimbal_ID_Num(), 5)

    def testSensor_ID_Num(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_Sensor_ID_Num(5)
        self.assertEqual(self.Tabdata.Sensor_ID_Num(), 5)

    def testSet_Sensor_ID_Num(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_Sensor_ID_Num(60)
        self.assertEqual(self.Tabdata.Sensor_ID_Num(), 60)

    def testPlatform_ID_Num(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_Platform_ID_Num(0)
        self.assertEqual(self.Tabdata.Platform_ID_Num(), 0)

    def testSet_Platform_ID_Num(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_Platform_ID_Num(2)
        self.assertEqual(self.Tabdata.Platform_ID_Num(), 2)

    def testtablecode(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_tablecode(1)
        self.assertEqual(self.Tabdata.tablecode(), 1)

    def testsourcecode(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_sourcecode(1)
        self.assertEqual(self.Tabdata.sourcecode(), 1)

    def testSet_tablecode(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_tablecode(10)
        self.assertEqual(self.Tabdata.tablecode(), 10)

    def testSet_sourcecode(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_sourcecode(10)
        self.assertEqual(self.Tabdata.sourcecode(), 10)

    def testtotlen(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_totlen(2000)
        self.assertEqual(self.Tabdata.totlen(), 2000)

    def testSet_totlen(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_totlen(5000)
        self.assertEqual(self.Tabdata.totlen(), 5000)

    def testclaimlen(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_claimlen(2000)
        self.assertEqual(self.Tabdata.claimlen(), 2000)

    def testSet_claimlen(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_claimlen(3000)
        self.assertEqual(self.Tabdata.claimlen(), 3000)

    def testextraraw(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_extraraw(b"143464576543435325ABCDEF")
        self.assertEqual(self.Tabdata.extraraw(), b"143464576543435325ABCDEF")

    def testSet_extraraw(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_extraraw(b"143464576543435325ABCDEFAAA")
        self.assertEqual(
            self.Tabdata.extraraw(), b"143464576543435325ABCDEFAAA")

    def testpacketnum(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_packetnum(20)
        self.assertEqual(self.Tabdata.packetnum(), 20)

    def testSet_packetnum(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_packetnum(35)
        self.assertEqual(self.Tabdata.packetnum(), 35)

    def testblockdataextract(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_blockdataextract(True)
        self.assertEqual(self.Tabdata.blockdataextract(), True)

    def testSet_blockdataextract(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_blockdataextract(False)
        self.assertEqual(self.Tabdata.blockdataextract(), False)

    def testherrors(self):
        # get the output and check basic value are in it ok
        self.Tabdata.hdr.errors.adderror(2,2,"test abc")
        a = self.Tabdata.herrors()
        self.assertTrue(isinstance(a,NPIF.NPIF_Error))
        self.assertEqual(a.einfo(0),(2,2,"test abc"))

    def testtablename(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_tablename("blah")
        self.assertEqual(self.Tabdata.tablename(), "blah")

    def testSet_tablename(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_tablename("blah2")
        self.assertEqual(self.Tabdata.tablename(), "blah2")

    def testdataraw(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_dataraw(b"143464576543435325ABCDEF")
        self.assertEqual(self.Tabdata.dataraw(), b"143464576543435325ABCDEF")

    def testSet_dataraw(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_dataraw(b"\x12\x13\x14\x15\x16\x17\x1a\x1b\x20")
        self.assertEqual(
            self.Tabdata.dataraw(), b"\x12\x13\x14\x15\x16\x17\x1a\x1b\x20")

    def testdatacrc(self):
        self.Tabdata.Set_datacrc(b"123A")
        self.assertEqual(self.Tabdata.datacrc(), b"123A")

    def testSet_datacrc(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_datacrc(b"126A")
        self.assertEqual(self.Tabdata.datacrc(), b"126A")

    def testnumfieldsrepeating(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_numfieldsrepeating(3)
        self.assertEqual(self.Tabdata.numfieldsrepeating(), 3)

    def testSet_numfieldsrepeating(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_numfieldsrepeating(9)
        self.assertEqual(self.Tabdata.numfieldsrepeating(), 9)

    def testnumrepeats(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_numrepeats(4)
        self.assertEqual(self.Tabdata.numrepeats(), 4)

    def testSet_numrepeats(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_numrepeats(8)
        self.assertEqual(self.Tabdata.numrepeats(), 8)

    def testfieldnames(self):
        # check we can put a value in and read it out
        indat = ('a', 'b', 'c')
        self.Tabdata.Set_fieldnames(indat)
        self.assertEqual(self.Tabdata.fieldnames(), indat)

    def testSet_fieldnames(self):
        # check we can put a value in and read it out
        indat = ('a', 'b', 'c', 'blah')
        self.Tabdata.Set_fieldnames(indat)
        self.assertEqual(self.Tabdata.fieldnames(), indat)

    def testfieldtypes(self):
        # check we can put a value in and read it out
        indat = ('h', 'i', 'e', 'x')
        self.Tabdata.Set_fieldtypes(indat)
        self.assertEqual(self.Tabdata.fieldtypes(), indat)

    def testSet_fieldtypes(self):
        # check we can put a value in and read it out
        indat = ('h', 'i', 'e')
        self.Tabdata.Set_fieldtypes(indat)
        self.assertEqual(self.Tabdata.fieldtypes(), indat)

    def testfieldfuncs(self):
        # check we can put a value in and read it out
        indat = (None, self.Tabdata.Lookup_Tgt_Cat_Desig_Scheme, None)
        self.Tabdata.Set_fieldfuncs(indat)
        self.assertEqual(self.Tabdata.fieldfuncs(), indat)

    def testSet_fieldfuncs(self):
        # check we can put a value in and read it out
        indat = (None, self.Tabdata.Lookup_Tgt_Cat_Desig_Scheme, None, None)
        self.Tabdata.Set_fieldfuncs(indat)
        self.assertEqual(self.Tabdata.fieldfuncs(), indat)

    def testfieldlflags(self):
        # check we can put a value in and read it out
        indat = (0, 1, 1, 1, 1, 1, 1)
        self.Tabdata.Set_fieldlflags(indat)
        self.assertEqual(self.Tabdata.fieldlflags(), indat)

    def testSet_fieldlflags(self):
        # check we can put a value in and read it out
        indat = (0, 0, 0, 1, 1, 1)
        self.Tabdata.Set_fieldlflags(indat)
        self.assertEqual(self.Tabdata.fieldlflags(), indat)

    def testfieldreqs(self):
        # check we can put a value in and read it out
        indat = ('m', 'm', 'm', 'c', 'm')
        self.Tabdata.Set_fieldreqs(indat)
        self.assertEqual(self.Tabdata.fieldreqs(), indat)

    def testSet_fieldreqs(self):
        # check we can put a value in and read it out
        indat = ('m', 'm', 'm', 'c', 'm', 'o')
        self.Tabdata.Set_fieldreqs(indat)
        self.assertEqual(self.Tabdata.fieldreqs(), indat)

    def testdata_flens(self):
        # check we can put a value in and read it out
        indat = (8, 8, 2, 1, 1)
        self.Tabdata.Set_data_flens(indat)
        self.assertEqual(self.Tabdata.data_flens(), indat)

    def testSet_data_flens(self):
        # check we can put a value in and read it out
        indat = (3,)
        self.Tabdata.Set_data_flens(indat)
        self.assertEqual(self.Tabdata.data_flens(), indat)

    def testtcontents(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_tcontents({("Time Tag", 0.03)})
        self.assertEqual(self.Tabdata.tcontents(), {("Time Tag", 0.03)})

    def testSet_tcontents(self):
        # check we can put a value in and read it out
        self.Tabdata.Set_tcontents({("Time Tag", 0.02)})
        self.assertEqual(self.Tabdata.tcontents(), {("Time Tag", 0.02)})

    def testderrors(self):
        # get the output and check basic value are in it ok
        self.Tabdata.tdat.errors.adderror(2,2,"test abcd")
        a = self.Tabdata.derrors()
        self.assertTrue(isinstance(a,NPIF.NPIF_Error))
        self.assertEqual(a.einfo(0),(2,2,"test abcd"))

    def testLookup_Sync_Type_Code(self):
        # check one good and one bad value
        self.assertEqual(self.Tabdata.Lookup_Sync_Type_Code(0), "INACTIVE")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM, self.Tabdata.Lookup_Sync_Type_Code(300))

    def testLookup_Antenna_weight(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Antenna_weight(5), "-40dB m = 81 Taylor")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM, self.Tabdata.Lookup_Antenna_weight(300))

    def testLookup_Autofocus_proc_alg(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Autofocus_proc_alg(1),
            "Motion compensation (MOCO) only")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Autofocus_proc_alg(300))

    def testLookup_Azimuth_comp_proc(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Azimuth_comp_proc(2), "Real beam")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Azimuth_comp_proc(300))

    def testLookup_Codestream_cap(self):
        # check one good and one bad value
        self.assertEqual(self.Tabdata.Lookup_Codestream_cap(2), "Profile 1")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Codestream_cap(300))

    def testLookup_Comb_op(self):
        # check one good and one bad value
        self.assertEqual(self.Tabdata.Lookup_Comb_op(1), "Subtraction")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Comb_op(300))

    def testLookup_Comp_Alg(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Comp_Alg(2), "JPEG (ISO/IEC 10918-1:1994)")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Comp_Alg(300))

    def testLookup_Coverage_Rel(self):
        # check one good and one bad value
        self.assertEqual(self.Tabdata.Lookup_Coverage_Rel(3), "Abutted")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Coverage_Rel(300))

    def testLookup_Dir_road_curv(self):
        # check one good and one bad value
        self.assertEqual(self.Tabdata.Lookup_Dir_road_curv(1), "Clockwise")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Dir_road_curv(300))

    def testLookup_Dir_vehicle_radvel(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Dir_vehicle_radvel(2), "Towards the sensor")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Dir_vehicle_radvel(300))

    def testLookup_Event_Type(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Event_Type(4), "Manual Duration START")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Event_Type(300))

    def testLookup_Group_type(self):
        # check one good and one bad value
        self.assertEqual(self.Tabdata.Lookup_Group_type(0), "Coverage")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Group_type(300))

    def testLookup_Image_Build_Dir(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Image_Build_Dir(8),
            "PDA is Y negative; SDA is X negative")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Image_Build_Dir(300))

    def testLookup_Interpulse_mod_type(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Interpulse_mod_type(2),
            "Binary phase code - Barker")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Interpulse_mod_type(300))

    def testLookup_JPEG_2000_IREP(self):
        # check one good and one bad value
        self.assertEqual(self.Tabdata.Lookup_JPEG_2000_IREP(6), "NVECTOR")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_JPEG_2000_IREP(300))

    def testLookup_JPEG_2000_Tiling(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_JPEG_2000_Tiling(0),
            "No JPEG 2000 Tiling has been used")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_JPEG_2000_Tiling(300))

    def testLookup_Mission_Priority_Type(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Mission_Priority_Type(3), "PRIORITY 3")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Mission_Priority_Type(300))

    def testLookup_Nav_Conf(self):
        # check one good and one bad value
        self.assertEqual(self.Tabdata.Lookup_Nav_Conf(1), "POSSIBLE FAILURE")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Nav_Conf(300))

    def testLookup_Num_Fields(self):
        # check two good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Num_Fields(1), "NON-INTERLACED FRAMING SENSOR")
        # has some range checks so do another test
        self.assertEqual(
            self.Tabdata.Lookup_Num_Fields(5), "5 FIELDS")
        # now a bad example
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Num_Fields(300))

    def testLookup_PassSens_Mode(self):
        # check one good and one bad value
        self.assertEqual(self.Tabdata.Lookup_PassSens_Mode(2), "Standby")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_PassSens_Mode(300))

    def testLookup_PassSens_Ordering(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_PassSens_Ordering(1),
            "BAND INTERLEAVED BY PIXEL")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_PassSens_Ordering(300))

    def testLookup_PassSens_Scan_Dir(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_PassSens_Scan_Dir(0), "negative direction")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_PassSens_Scan_Dir(300))

    def testLookup_Physical_characteristic(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Physical_characteristic(6),
            "Radar measurement MTI")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Physical_characteristic(300))

    def testLookup_Polarisation(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Polarisation(255), "Polarisation unassigned")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Polarisation(300))

    def testLookup_proc_weight(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_proc_weight(9), "Spatially varying apodisation")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_proc_weight(300))

    def testLookup_Prog_order(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Prog_order(3),
            "Position-Component-Resolution-Layer")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Prog_order(300))

    def testLookup_Projection_type(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Projection_type(2), "Stereographic")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Projection_type(300))

    def testLookup_Pulse_to_pulse_mod(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Pulse_to_pulse_mod(4),
            "Step plus pseudo-random")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Pulse_to_pulse_mod(300))

    def testLookup_RAD_Coord_Sys_Orient(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_RAD_Coord_Sys_Orient(7),
            "vld is Y negative; cvld is X negative")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_RAD_Coord_Sys_Orient(300))

    def testLookup_RAD_Data_order(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_RAD_Data_order(2), "Element sequential")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_RAD_Data_order(300))

    def testLookup_RAD_mode(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_RAD_mode(4), "Doppler beam sharpened map")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_RAD_mode(300))

    def testLookup_RAD_Phys_coord_sys(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_RAD_Phys_coord_sys(0), "Range; Cross Range")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_RAD_Phys_coord_sys(300))

    def testLookup_RAD_Sensor_mode(self):
        # check one good and one bad value
        self.assertEqual(self.Tabdata.Lookup_RAD_Sensor_mode(5), "FAIL")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_RAD_Sensor_mode(300))

    def testLookup_RAD_vld_orientation(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_RAD_vld_orientation(2),
            "Port; i.e. value of alpha is negative")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_RAD_vld_orientation(300))

    def testLookup_Range_comp_proc_alg(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Range_comp_proc_alg(5),
            "Step plus matched filter")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Range_comp_proc_alg(300))

    def testLookup_Report_Message_Type(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Report_Message_Type(1), "INFLIGHTREP")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Report_Message_Type(300))

    def testLookup_Req_Collect_Tech(self):
        # check one good and one bad value
        self.assertEqual(self.Tabdata.Lookup_Req_Collect_Tech(16), "SWATH")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Req_Collect_Tech(300))

    def testLookup_Req_Sensor_Resp_Band(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Req_Sensor_Resp_Band(17), "mm WAVE")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Req_Sensor_Resp_Band(300))

    def testLookup_Req_Sensor_Type(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Req_Sensor_Type(17), "MTI (other than 4607)")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Req_Sensor_Type(300))

    def testLookup_Requester_Type(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Requester_Type(2), "INFORMATION REQUESTER")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Requester_Type(300))

    def testLookup_Sensor_Coding_Type(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Sensor_Coding_Type(18), "RADAR virtual")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Sensor_Coding_Type(300))

    def testLookup_Sensor_Mod_Meth(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Sensor_Mod_Meth(3), "RECTIFIED IMAGE")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Sensor_Mod_Meth(300))

    def testLookup_Tgt_Cat_Desig_Scheme(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Tgt_Cat_Desig_Scheme(1), "NATO STANAG 3596")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Tgt_Cat_Desig_Scheme(300))

    def testLookup_Target_Type(self):
        # check one good and one bad value
        self.assertEqual(self.Tabdata.Lookup_Target_Type(4), "STRIP")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Target_Type(300))

    def testLookup_Terrain_model(self):
        # check one good and one bad value
        self.assertEqual(self.Tabdata.Lookup_Terrain_model(0), "no DTM used")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Terrain_model(300))

    def testLookup_Timing_accuracy(self):
        # check one good and one bad value
        self.assertEqual(self.Tabdata.Lookup_Timing_accuracy(0), "Real Number")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Timing_accuracy(300))

    def testLookup_Timing_method(self):
        # check one good and one bad value
        self.assertEqual(self.Tabdata.Lookup_Timing_method(1), "DIFFERENTIAL")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Timing_method(300))

    def testLookup_Timing_relationship(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Timing_relationship(1), "Sequential")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Timing_relationship(300))

    def testLookup_Track_type(self):
        # check one good and one bad value
        self.assertEqual(self.Tabdata.Lookup_Track_type(1), "Link 16")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Track_type(300))

    def testLookup_Trans_Func_Type(self):
        # check one good and one bad value
        self.assertEqual(self.Tabdata.Lookup_Trans_Func_Type(2), "Exponential")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Trans_Func_Type(300))

    def testLookup_Type_of_Element(self):
        # check one good and one bad value
        self.assertEqual(self.Tabdata.Lookup_Type_of_Element(2), "Real Number")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Type_of_Element(300))

    def testLookup_Unit_Meas_CrossVirt(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Unit_Meas_CrossVirt(1), "distance (metres)")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Unit_Meas_CrossVirt(300))

    def testLookup_Use_of_element(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Use_of_element(16), "(Magnitude)**2")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Use_of_element(300))

    def testLookup_Vect_or_Tim_Mod(self):
        # check one good and one bad value
        self.assertEqual(
            self.Tabdata.Lookup_Vect_or_Tim_Mod(1), "Pixel by pixel")
        self.assertIn(
            self.Tabdata.TXT_UNKN_ENUM,
            self.Tabdata.Lookup_Vect_or_Tim_Mod(300))

    def testConv_DTG(self):
        # check a well formed dtg value
        tval = b"\x07\xda\x09\x19\x10\x37\x11\x94"
        self.assertEqual(
            self.Tabdata.Conv_DTG(tval), "2010-09-25, 16:55:04.500000")
        # check case where there is a bad date, but ok time
        tval = b"\x00\x00\x09\x19\x10\x37\x11\x94"
        self.assertTrue(
            self.Tabdata.TXT_BAD_DTG in self.Tabdata.Conv_DTG(tval))
        # check that a Null result is returned when appropriate
        tval = b"\x00\x00\x00\x00\x00\x00\x00\x00"
        self.assertEqual(self.Tabdata.Conv_DTG(tval), self.Tabdata.TXT_NULL)

    def testConv_Coord(self):
        # check that acceptable values returned at edge of ok range
        self.assertEqual(
            self.Tabdata.Conv_Coord(struct.pack('>d', -math.pi / 2) +
            struct.pack('>d', -math.pi)), (-90.0, -180.0))
        self.assertEqual(
            self.Tabdata.Conv_Coord(struct.pack('>d', math.pi / 2) +
            struct.pack('>d', math.pi)),
            (90.0, "180.0, ANGLE OUT OF RANGE ####****"))
        self.assertFalse(
            "ANGLE OUT OF RANGE ####****" in
            self.Tabdata.Conv_Coord(struct.pack('>d', math.pi / 2) +
            struct.pack('>d', math.pi - 0.001)))
        # check in out of range latitude case
        self.assertEqual(
            self.Tabdata.Conv_Coord(struct.pack('>d', math.pi * 3 / 4) +
            struct.pack('>d', math.pi / 2)),
            ("135.0, ANGLE OUT OF RANGE ####****", 90.0))
        # check in out of range longditude case
        self.assertEqual(
            self.Tabdata.Conv_Coord(struct.pack('>d', math.pi / 4) +
            struct.pack('>d', math.pi * 1.5)),
            (45.0, "270.0, ANGLE OUT OF RANGE ####****"))

    def testConv_Real(self):
        # test that a particular value gets converted correctly
        self.assertEqual(
            self.Tabdata.Conv_Real(struct.pack('>d', 2.514)), 2.514)
        # also check that a NULL value is returned correctly
        self.assertEqual(
            self.Tabdata.Conv_Real(struct.pack('>d', float('nan'))),
            self.Tabdata.TXT_NULL)

    def testConv_Int_NC(self):
        # test that a particular value gets converted correctly
        self.assertEqual(
            self.Tabdata.Conv_Int_NC(struct.pack('>Q', 106012)), 106012)
        # make sure that this does not convert all 0xFF values to NULL
        self.assertEqual(
            self.Tabdata.Conv_Int_NC(binascii.unhexlify(b"FFFF")), 65535)

    def testConv_Int(self):
        # pick a couple of random values
        self.assertEqual(
            self.Tabdata.Conv_Int(struct.pack('>Q', 306012)), 306012)
        self.assertEqual(
            self.Tabdata.Conv_Int(struct.pack('>Q', 12)), 12)
        # make sure a NULL value gets returned when appropriate
        self.assertEqual(
            self.Tabdata.Conv_Int(binascii.unhexlify(b"FFFF")),
            self.Tabdata.TXT_NULL)

    def testConv_ASCII(self):
        # test one case with good ASCII - and some blanks at the end
        # (to ensure they get stripped)
        s = (b"\x61\x62\x63\x64\x65\x66\x67\x20\x41\x42\x43\x44\x45\x46\x47"
            b"\x00\x00\x00\x00")
        e = "abcdefg ABCDEFG"
        self.assertEqual(self.Tabdata.Conv_ASCII(s), e)
        # test a case to ensure NULL get returned when everything is 0x00
        s = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        e = self.Tabdata.TXT_NULL
        self.assertEqual(self.Tabdata.Conv_ASCII(s), e)
        #  test a case where there are non ascii characters included and ensure
        # we get the BAD ascii note raised
        s = b"\xc8\x61\x62\x63\x64\x65\x00\x00"
        btxt = self.Tabdata.TXT_BAD_ASCII
        self.assertIn(btxt,self.Tabdata.Conv_ASCII(s))

    def testConv_I2Blist(self):
        # include a test case to ensure it behaves as expected
        self.assertEqual(self.Tabdata.Conv_I2Blist(4500), ['0', '0', '0', '0',
            '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0',
            '0', '0', '1', '0', '0', '0', '1', '1', '0', '0', '1', '0', '1',
            '0', '0'])

    def testConv_bin1ind(self):
        # include a test case to ensure it behaves as expected
        self.assertListEqual(self.Tabdata.Conv_bin1ind(4500), [2, 4, 7, 8, 12])

    def testConv_nav_full(self):
        # include a test case to ensure it behaves as expected: min dynamic
        # platform 1st
        outlist = ['FULL SPECIFICATION', 'DE-RATED', 'FAIL',
            'FULL SPECIFICATION', 'FAIL', 'FULL SPECIFICATION', 'FAIL',
            'FULL SPECIFICATION', 'FULL SPECIFICATION', 'FULL SPECIFICATION',
            'FULL SPECIFICATION', 'FULL SPECIFICATION']
        self.assertListEqual(
            self.Tabdata.Conv_nav_full(16764107, 24, 12), outlist)
        # now comprehensive dynmic platform
        outlist = (
            ['FAIL', 'DE-RATED'] * 4 + ['DE-RATED', 'POSSIBLE FAILURE'] * 4 +
            ['FULL SPECIFICATION'] * 11)
        self.assertListEqual(
            self.Tabdata.Conv_nav_full(72057591460956296, 56, 27), outlist)

    def testConv_nav(self):
        # test a couple of cases based on min tables
        inraw1 = b'\xFF' * 3
        outlist1 = ['FULL SPECIFICATION'] * 12
        self.assertListEqual(self.Tabdata.Conv_nav(inraw1), outlist1)
        inraw2 = b'\x66' * 3
        outlist2 = ['DE-RATED', 'POSSIBLE FAILURE'] * 6
        self.assertListEqual(self.Tabdata.Conv_nav(inraw2), outlist2)
        # test a couple of cases based on max tables
        inraw3 = b'\xFF' * 7
        outlist3 = ['FULL SPECIFICATION'] * 27
        self.assertListEqual(self.Tabdata.Conv_nav(inraw3), outlist3)
        inraw4 = b'\x88' * 7
        outlist4a = ['FAIL', 'DE-RATED'] * 14
        outlist4 = outlist4a[:-1]
        self.assertListEqual(self.Tabdata.Conv_nav(inraw4), outlist4)

    def testConv_Hex(self):
        # test a couple of cases
        self.assertEqual(self.Tabdata.Conv_Hex(struct.pack('>B', 255)), "FF")
        self.assertEqual(self.Tabdata.Conv_Hex(struct.pack('>B', 101)), "65")

    def testConv_Raw(self):
        # test a couple of cases
        self.assertEqual(self.Tabdata.Conv_Raw(struct.pack('>B', 255)), b"\xff")
        self.assertEqual(self.Tabdata.Conv_Raw(b"ABCDEF"), b"ABCDEF")

    def testConv_Degrees(self):
        # test one good case
        self.assertEqual(self.Tabdata.Conv_Degrees(-math.pi), -180.0)
        # test out of range angle (right on boundary)
        self.assertTrue(
            self.Tabdata.TXT_BAD_ANGLE in self.Tabdata.Conv_Degrees(math.pi))

    def testConv_Degrees2(self):
        q = math.pi / 2.0
        # test one good case
        self.assertEqual(self.Tabdata.Conv_Degrees2(q), 90.0)
        # test out of range angle
        self.assertTrue(
            self.Tabdata.TXT_SUS_VALUE in self.Tabdata.Conv_Degrees2(-q))

    def testConv_Degrees3(self):
        q = -math.pi / 2.0
        # test one good case
        self.assertEqual(self.Tabdata.Conv_Degrees3(q), -90.0)
        # test out of range angle
        self.assertTrue(
            self.Tabdata.TXT_SUS_VALUE in self.Tabdata.Conv_Degrees3(q * 3))

    def testConv_Degrees_NC(self):
        # test a valid value
        self.assertEqual(self.Tabdata.Conv_Degrees_NC(math.pi), 180.0)
        # test case which should just work here but would be error in non
        # NC case
        self.assertEqual(self.Tabdata.Conv_Degrees_NC(-math.pi), -180.0)

    def testConv_JPEG_PqTq(self):
        # task cases to give both precision answers
        self.assertEqual(
            self.Tabdata.Conv_JPEG_PqTq(3), "Table 3, 8-bit precision")
        self.assertEqual(
            self.Tabdata.Conv_JPEG_PqTq(18), "Table 2, 16-bit precision")

    def testConv_Huff_TcTh(self):
        # task cases to give both of AC and DC answers
        self.assertEqual(self.Tabdata.Conv_Huff_TcTh(3), "Table 3 DC")
        self.assertEqual(self.Tabdata.Conv_Huff_TcTh(18), "Table 2 AC")

    def testConv_Hufflengths(self):
        # test a couple of cases with constant and mixed values
        inraw = struct.pack('>B', 10) * 16
        self.assertEqual(self.Tabdata.Conv_Hufflengths(inraw), [10] * 16)
        inraw2 = b""
        for i in range(16):
            inraw2 += struct.pack('>B', i)
        self.assertEqual(self.Tabdata.Conv_Hufflengths(inraw2), list(range(16)))

    def testConv_notinuse(self):
        # test a case with the NULL present
        n = self.Tabdata.TXT_NULL
        u = self.Tabdata.TXT_NOTINUSE
        self.assertEqual(self.Tabdata.Conv_notinuse(n), u)
        # and one where it is not present
        self.assertEqual(self.Tabdata.Conv_notinuse(10), 10)

    def testS7023_TABLE_NAMES(self):
        # test a couple of cases and include some bad examples
        self.assertEqual(
            self.Tabdata.S7023_TABLE_NAMES[10], "General Target EEI")
        self.assertEqual(
            self.Tabdata.S7023_TABLE_NAMES[60], "JPEG 2000 Index")
        self.assertEqual(
            self.Tabdata.S7023_TABLE_NAMES[0], "Unrecognised Table")
        self.assertEqual(
            self.Tabdata.S7023_TABLE_NAMES[100], "Unrecognised Table")

    def testSA_INFO(self):
        # test a couple of cases and include some bad examples
        self.assertEqual(self.Tabdata.SA_INFO[2], "Mission")
        self.assertEqual(self.Tabdata.SA_INFO[8], "Sensor")
        self.assertEqual(
            self.Tabdata.SA_INFO[0], "Unrecognised Source Address")
        self.assertEqual(
            self.Tabdata.SA_INFO[20], "Unrecognised Source Address")

    def testS7023_FLD_TYPES(self):
        # test a couple of cases against known correct answers
        self.assertEqual(self.Tabdata.S7023_FLD_TYPES[15], ('i',))
        self.assertEqual(self.Tabdata.S7023_FLD_TYPES[0], ())

    def testS7023_FLD_REQS(self):
        # test a couple of cases against known correct answers
        self.assertEqual(self.Tabdata.S7023_FLD_REQS[25], ('o',) * 4)
        self.assertEqual(self.Tabdata.S7023_FLD_REQS[0], ())

    def testS7023_FLD_NAMES(self):
        # test a couple of cases against known correct answers
        aa = ("Vector model", "Size of 'x' vector component",
            "Type of 'x' vector component", "Size of 'y' vector component",
            "Type of 'y' vector component", "Size of 'z' vector component",
            "Type of 'z' vector component")
        self.assertEqual(self.Tabdata.S7023_FLD_NAMES[35], aa)
        self.assertEqual(self.Tabdata.S7023_FLD_NAMES[0], ())

    def testS7023_FLD_FUNCS(self):
        # test a single case against a known correct answer
        self.assertEqual(
            self.Tabdata.S7023_FLD_FUNCS[25], ((None,) * 4))
        # test with a given input value
        self.assertEqual(self.Tabdata.S7023_FLD_FUNCS[0], ())

    def testS7023_FLD_LIST_FLAGS(self):
        # test a couple of cases against known correct answers
        self.assertEqual(self.Tabdata.S7023_FLD_LIST_FLAGS[5], (0,) * 6)
        self.assertEqual(self.Tabdata.S7023_FLD_LIST_FLAGS[0], ())

    def testS7023_TABLE_SIZES(self):
        # test a couple of cases and include some bad examples
        self.assertEqual(self.Tabdata.S7023_TABLE_SIZES[10], (40,40))
        self.assertEqual(self.Tabdata.S7023_TABLE_SIZES[39], (33,1108))
        self.assertEqual(self.Tabdata.S7023_TABLE_SIZES[0], (0,0))
        self.assertEqual(self.Tabdata.S7023_TABLE_SIZES[100], (0,0))


class TestTabledata(unittest.TestCase):

    def setUp(self):
        self.Tabdata = NPIF.Tabledata()

    def tearDown(self):
        pass

    def testSplitFields(self):
        # test a few valid sample cases
        self.assertEqual(
            self.Tabdata.SplitFields('abcdef', [1] * 6, 0),
            ['a', 'b', 'c', 'd', 'e', 'f'])
        self.assertEqual(
            self.Tabdata.SplitFields('abcdef\xff\xff', [1] * 6, 1),
            ['a', 'b', 'c', 'd', 'e', 'f', '\xff\xff'])
        self.assertEqual(
            self.Tabdata.SplitFields('abcdef', [3] * 2, 0), ['abc', 'def'])
        # also test a bad case, where buffer is too short
        self.assertEqual(
            self.Tabdata.SplitFields('abcde', [3] * 2, 0), [])

    def testcrc16(self):
        # test the example given in the standard
        self.assertEqual(
            self.Tabdata.crc16(b'\xff\xff\xff\xff\xff\xff\xff\x01'), '0026')
        # test the empty case
        self.assertEqual(self.Tabdata.crc16(b''), '0000')

    def testfieldlengths(self):
        # test a number of sample cases
        # avoid jpeg and huffman table here as they call other functions tested
        # below
        # start with a fixed size case
        self.Tabdata.Set_tablecode(self.Tabdata.DT_General_Tgt_Loc_DT)
        self.Tabdata.Set_crcflag(0)
        self.Tabdata.Set_datasize(71)
        self.assertEqual(
            self.Tabdata.fieldlengths(), (8 + 8, 8, 8, 8, 14, 8, 1, 8))
        # now try various variable length tables
        # pick tables to ensure we pass through all potential code paths
        self.Tabdata.Set_data_flens(None)
        self.Tabdata.Set_tablecode(self.Tabdata.DT_Sensor_Grouping_DT)
        self.Tabdata.Set_datasize(8)
        self.assertEqual(self.Tabdata.fieldlengths(), (1,) * 8)
        # next
        self.Tabdata.Set_data_flens(None)
        self.Tabdata.Set_tablecode(self.Tabdata.DT_Sensor_Samp_Coord_Des_DT)
        self.Tabdata.Set_datasize(19)
        self.assertEqual(self.Tabdata.fieldlengths(), (1,) * 19)
        # next
        self.Tabdata.Set_data_flens(None)
        self.Tabdata.Set_tablecode(self.Tabdata.DT_Passive_Sensor_El_DT)
        self.Tabdata.Set_datasize(63)
        self.assertEqual(self.Tabdata.fieldlengths(), (1, 2, 2, 8, 8) * 3)
        # next
        self.Tabdata.Set_data_flens(None)
        self.Tabdata.Set_tablecode(self.Tabdata.DT_Sensor_Samp_Timing_DT)
        self.Tabdata.Set_datasize(150)
        self.assertEqual(self.Tabdata.fieldlengths(), (150,))
        # test a bad case now
        self.Tabdata.Set_data_flens(None)
        self.Tabdata.Set_tablecode(self.Tabdata.DT_UNRECOGNISED_DFA_DT)
        self.Tabdata.Set_datasize(150)
        self.assertEqual(self.Tabdata.fieldlengths(), ())

    def test_JPEG_quant_flengths(self):
        # create a dummy data array - not real data, but we will put the
        # important bits for this function in correctly
        front = b"\x00" * 4
        d64 = b"\x00" * 64
        d128 = d64 * 2
        t1 = b"\x00"  # 64 and tab 0
        t2 = b"\x11"  # 128 and tab 1
        t3 = b"\x02"  # 64 and tab 2
        t4 = b"\x13"  # 128 and tab 3
        self.Tabdata.Set_dataraw(
            front + t1 + d64 + t2 + d128 + t3 + d64 + t4 + d128)
        flens = (2, 2, 1, 387)
        self.assertEqual(
            self.Tabdata._JPEG_quant_flengths(flens),
            (2, 2, 1, 64, 1, 128, 1, 64, 1, 128))

    def test_JPEG_huff_flengths(self):
        # create a dummy data array - not real data, but we will put the
        # important bits for this function in correctly
        front = b"\x00" * 4
        d12 = b"\x00" * 12
        d16 = b"\x00" * 16
        d162 = b"\x00" * 162
        d226 = b"\x00" * 226
        dt1 = b"\x00"  # DC tab 0
        dt2 = b"\x01"  # DC tab 1
        dt3 = b"\x02"  # DC tab 2
        dt4 = b"\x03"  # DC tab 3
        at1 = b"\x10"  # AC tab 0
        at2 = b"\x11"  # AC tab 1
        at3 = b"\x12"  # AC tab 2
        at4 = b"\x13"  # AC tab 3
        # 0; 2; 1; 3; 3; 2; 4; 3; 5; 5; 4; 4; 0; 0; 1; 125
        ac162len = (b"\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00"
            b"\x00\x01\x7d" + d162)
        # 0; 1; 5; 1; 1; 1; 1; 1; 1; 0; 0; 0; 0; 0; 0; 0
        dc12len = (b"\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00"
            b"\x00\x00\x00\x00" + d12)
        dc16len = (b"\x00\x01\x05\x01\x01\x01\x01\x01\x01\x04\x00\x00\x00"
            b"\x00\x00\x00" + d16)
        ac226len = (b"\x40\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00"
            b"\x00\x01\x7d" + d226)
        self.Tabdata.Set_dataraw(
            front + dt1 + dc12len + at1 + ac162len + dt2 + dc16len + at2 +
            ac226len + dt3 + dc12len + at3 + ac162len + dt4 + dc16len + at4 +
            ac226len)
        flens = (2, 2, 1, 16, len(self.Tabdata.dataraw()) - 21)
        self.assertEqual(
            self.Tabdata._JPEG_huff_flengths(flens),
            (2, 2, 1, 16, 12, 1, 16, 162, 1, 16, 16, 1, 16, 226, 1, 16, 12, 1,
            16, 162, 1, 16, 16, 1, 16, 226))

    def testCalc_sourcecode(self):
        # test simple value
        self.Tabdata.Set_sa(0)
        self.assertEqual(
            self.Tabdata.Calc_sourcecode(),
            self.Tabdata.SA_Format_Description_Data)
        # test something in sensor range
        self.Tabdata.Set_sa(159)
        self.assertEqual(
            self.Tabdata.Calc_sourcecode(), self.Tabdata.SA_Sensor_Data)
        # test a bad value
        self.Tabdata.Set_sa(600)
        self.assertEqual(
            self.Tabdata.Calc_sourcecode(), self.Tabdata.SA_Urecognised)

    def testCalc_tablecode(self):
        # check a sample of values, with at least one from each valid Source
        # address
        self.Tabdata.Set_sa(0)
        self.Tabdata.Set_dfa(1)
        self.assertEqual(
            self.Tabdata.Calc_tablecode(), self.Tabdata.DT_Format_Time_Tag_DT)
        self.Tabdata.Set_sa(16)
        self.Tabdata.Set_dfa(16)
        self.assertEqual(
            self.Tabdata.Calc_tablecode(), self.Tabdata.DT_Mission_Security_DT)
        self.Tabdata.Set_sa(17)
        self.Tabdata.Set_dfa(10926)
        self.assertEqual(
            self.Tabdata.Calc_tablecode(), self.Tabdata.DT_General_Tgt_EEI_DT)
        self.Tabdata.Set_sa(32)
        self.Tabdata.Set_dfa(3145729)
        self.assertEqual(
            self.Tabdata.Calc_tablecode(), self.Tabdata.DT_Comp_Dynamic_Plat_DT)
        self.Tabdata.Set_sa(48)
        self.Tabdata.Set_dfa(56576)
        self.assertEqual(
            self.Tabdata.Calc_tablecode(), self.Tabdata.DT_Segment_Index_DT)
        self.Tabdata.Set_sa(63)
        self.Tabdata.Set_dfa(5)
        self.assertEqual(
            self.Tabdata.Calc_tablecode(), self.Tabdata.DT_User_Defined_DT)
        self.Tabdata.Set_sa(65)
        self.Tabdata.Set_dfa(32)
        self.assertEqual(
            self.Tabdata.Calc_tablecode(), self.Tabdata.DT_Min_Sensor_Att_DT)
        self.Tabdata.Set_sa(150)
        self.Tabdata.Set_dfa(80)
        self.assertEqual(
            self.Tabdata.Calc_tablecode(),
            self.Tabdata.DT_Sensor_Samp_Timing_DT)
        # now check invalid values - with one case form each of the invalid
        # options
        self.Tabdata.Set_sa(15)
        self.Tabdata.Set_dfa(80)
        self.assertEqual(
            self.Tabdata.Calc_tablecode(), self.Tabdata.DT_UNRECOGNISED_SA_DT)
        self.Tabdata.Set_sa(201)
        self.Tabdata.Set_dfa(80)
        self.assertEqual(
            self.Tabdata.Calc_tablecode(), self.Tabdata.DT_Reserved_DT)
        self.Tabdata.Set_sa(0)
        self.Tabdata.Set_dfa(100)
        self.assertEqual(
            self.Tabdata.Calc_tablecode(), self.Tabdata.DT_UNRECOGNISED_DFA_DT)

    def test_calc_headflags(self):
        # check a sample of valuies with at least 1 on/off for each flag
        self.Tabdata._calc_headflags(14)
        self.assertEqual(self.Tabdata.ambleflag(), 1)
        self.assertEqual(self.Tabdata.compressflag(), 1)
        self.assertEqual(self.Tabdata.crcflag(), 1)
        self.Tabdata._calc_headflags(8)
        self.assertEqual(self.Tabdata.ambleflag(), 1)
        self.assertEqual(self.Tabdata.compressflag(), 0)
        self.assertEqual(self.Tabdata.crcflag(), 0)
        self.Tabdata._calc_headflags(6)
        self.assertEqual(self.Tabdata.ambleflag(), 0)
        self.assertEqual(self.Tabdata.compressflag(), 1)
        self.assertEqual(self.Tabdata.crcflag(), 1)

    def testextract_header(self):
        # extract a test case
        edition = b"\x04"
        flags = b"\x00"
        segnum = b"\x02"
        sa = b"\x00"
        dfa = b"\x00\x00\x00\x01"
        size = b"\x00\x00\x00\x08"
        dfn = b"\x00\x00\x00\xee"
        time = b"\x00\x00\x00\x00\x00\x00\x56\x78"
        sync = b"\x00"
        reserved = b"\x00\x00\x00\x00\x00"
        crc = b"\xa6\xaa"
        data = struct.pack('>d', 0.005)
        extra = b"\xab\xcd\xef"
        buff = (edition + flags + segnum + sa + dfa + size + dfn + time +
            sync + reserved + crc + data + extra)
        a = NPIF.Tabledata()
        a.extract_header(buff,0)
        self.assertEqual(a.edition(), 4)
        self.assertEqual(a.ambleflag(), 0)
        self.assertEqual(a.crcflag(), 0)
        self.assertEqual(a.compressflag(), 0)
        self.assertEqual(a.segment(), 2)
        self.assertEqual(a.tablecode(), a.DT_Format_Time_Tag_DT)
        self.assertEqual(a.sa(), 0)
        self.assertEqual(a.dfa(), 1)
        self.assertEqual(a.dfn(), 238)
        self.assertEqual(a.timetag(), 22136)
        self.assertEqual(a.synctype(), "INACTIVE")
        self.assertEqual(a.headcrc(), "A6AA")
        self.assertEqual(a.reserved(), "0000000000")
        self.assertEqual(a.sourcecode(), a.SA_Format_Description_Data)
        self.assertEqual(a.totlen(), 53)
        self.assertEqual(a.claimlen(), 50)
        self.assertEqual(a.extraraw(), b"\xab\xcd\xef")
        self.assertEqual(a.datasize(), 8)
        self.assertEqual(a.herrors().ecount(),1)
        self.assertGreater(len(a.herrors().whereerr(a.herrors().E_EXTRABYTE)),0)
        # test bad input and check for at least one error of correct class
        # start with header length
        buff = b"\x00\x00\x00\x00\x00\x00\x00\x00"
        b = NPIF.Tabledata()
        b.extract_header(buff,0)
        self.assertGreater(len(b.herrors().whereerr(b.herrors().E_HEADLEN)),0)
        # try a bad dfa now
        dfa2 = b"\xff\xff\x00\x01"
        buff = (edition + flags + segnum + sa + dfa2 + size + dfn + time +
            sync + reserved + crc + data + extra)
        c = NPIF.Tabledata()
        c.extract_header(buff,0)
        self.assertGreater(len(c.herrors().whereerr(c.herrors().E_DFAADD)),0)
        self.assertGreater(len(c.herrors().whereerr(c.herrors().E_UKNPACKET)),0)
        # try a bad datalength now - short
        size2 = b"\x00\x00\x00\x06"
        buff = (edition + flags + segnum + sa + dfa + size2 + dfn + time +
            sync + reserved + crc + data + extra)
        d = NPIF.Tabledata()
        d.extract_header(buff,0)
        self.assertGreater(len(d.herrors().whereerr(d.herrors().E_DATALEN)),0)
        # try a bad datalength now - long
        size2 = b"\x00\x00\x00\x0A"
        buff = (edition + flags + segnum + sa + dfa + size2 + dfn + time +
            sync + reserved + crc + data + extra)
        d = NPIF.Tabledata()
        d.extract_header(buff,0)
        self.assertGreater(len(d.herrors().whereerr(d.herrors().E_DATALEN)),0)
        # try a bad edition now
        edition2 = b"\xEE"
        buff = (edition2 + flags + segnum + sa + dfa + size + dfn + time +
            sync + reserved + crc + data + extra)
        d = NPIF.Tabledata()
        d.extract_header(buff,0)
        self.assertGreater(len(d.herrors().whereerr(d.herrors().E_EDITION)),0)
        # try bad sync enumeration
        sync2 = b"\xDD"
        buff = (edition + flags + segnum + sa + dfa + size + dfn + time +
            sync2 + reserved + crc + data + extra)
        d = NPIF.Tabledata()
        d.extract_header(buff,0)
        self.assertGreater(
            len(d.herrors().whereerr(d.herrors().E_ENUMERATION)),0)
        # try non empty reserved
        reserved2 = b"\x01\x01\x01\x01\x01"
        buff = (edition + flags + segnum + sa + dfa + size + dfn + time +
            sync + reserved2 + crc + data + extra)
        d = NPIF.Tabledata()
        d.extract_header(buff,0)
        self.assertGreater(
            len(d.herrors().whereerr(d.herrors().E_RESERVED)),0)
        # now bad header CRC
        crc2 = b"\xbb\xbb"
        buff = (edition + flags + segnum + sa + dfa + size + dfn + time +
            sync + reserved + crc2 + data + extra)
        d = NPIF.Tabledata()
        d.extract_header(buff,0)
        self.assertGreater(
            len(d.herrors().whereerr(d.herrors().E_HEADCRC)),0)
        # now with a reserved source address
        sa2 = b"\xee"
        buff = (edition + flags + segnum + sa2 + dfa + size + dfn + time +
            sync + reserved + crc + data + extra)
        d = NPIF.Tabledata()
        d.extract_header(buff,0)
        self.assertGreater(
            len(d.herrors().whereerr(d.herrors().E_SOURCEADD)),0)
        # now with a user defined table
        sa2 = b"\x3f"
        buff = (edition + flags + segnum + sa2 + dfa + size + dfn + time +
            sync + reserved + crc + data + extra)
        d = NPIF.Tabledata()
        d.extract_header(buff,0)
        self.assertGreater(
            len(d.herrors().whereerr(d.herrors().E_USERDEFINED)),0)

    def testextract_data(self):
        # create and test 3 cases
        # a) simple table (Time Tag)
        # b) minimum dynamic platform (has nav confidence codes)
        # c) sensor sample timing description (has lists)
        # start by creating enough info to run on these
        a = NPIF.Tabledata()
        b = NPIF.Tabledata()
        c = NPIF.Tabledata()
        a.Set_tablecode(a.DT_Format_Time_Tag_DT)
        b.Set_tablecode(a.DT_Min_Dynamic_Plat_DT)
        c.Set_tablecode(a.DT_Sensor_Samp_Timing_Des_DT)
        a.Set_crcflag(0)
        b.Set_crcflag(0)
        c.Set_crcflag(0)
        a.Set_dfa(1)
        a.Set_sa(0)
        b.Set_dfa(65536) # plat id =1
        b.Set_sa(32)
        c.Set_dfa(4128)
        c.Set_sa(74) # sen id =10
        a.Set_packetnum(1)
        b.Set_packetnum(1)
        c.Set_packetnum(1)
        a.hdr.tablename = a.S7023_TABLE_NAMES[a.tablecode()]
        b.hdr.tablename = b.S7023_TABLE_NAMES[b.tablecode()]
        c.hdr.tablename = c.S7023_TABLE_NAMES[c.tablecode()]
        #
        abuff = struct.pack('>d', 0.005)
        a.Set_datasize(8)
        bbuff = (b"\x00\x00\x00\x00\x00\x00\x00\x00" + struct.pack(
            '>dddddddddddd', math.pi/4, math.pi/4, 500.0, 500.0, 500.0, 10.0,
            10.0, math.pi/4, math.pi/4, math.pi/4, math.pi/4, math.pi/4) +
            b"\xfe\xa5\x40")
        b.Set_datasize(107)
        cbuff = b"\x00\x01\x00\x01\xff\x05\x00"
        c.Set_datasize(7)
        a.extract_data(abuff)
        b.extract_data(bbuff)
        c.extract_data(cbuff)
        # now check these
        self.assertEqual(a.tcontents()['Tick Value'], 0.005)
        self.assertEqual(a.fieldtypes(), ('r', ))
        self.assertEqual(a.fieldreqs(), ('m',))
        self.assertTrue(b.TXT_NULL in b.tcontents()['Platform Time'])
        self.assertEqual(b.tcontents()['GPS Altitude'], 500.0)
        self.assertEqual(
            b.tcontents()['Platform Pitch'], math.degrees(math.pi/4))
        self.assertEqual(
            b.tcontents()['Navigational Confidence'],
            (["FAIL"] * 3 + ["POSSIBLE FAILURE"] * 3 + ["DE-RATED"] * 3 +
            ["FULL SPECIFICATION"] * 3))
        self.assertEqual(
            b.fieldreqs(), ('m', 'm') + ('c',) * 6 + ('m', 'm', 'm', 'c', 'm'))
        self.assertEqual(
            c.tcontents()['Timing method'], ["CUMULATIVE", "DIFFERENTIAL",
            "UNUSED", "5, " + c.TXT_UNKN_ENUM, "CUMULATIVE"])

    def testCheck_DT_Enum_Errors(self):
        # create a fake table and test it
        a = NPIF.Tabledata()
        a.Set_packetnum(1)
        a.Set_tablename("Rubbish")
        a.Set_fieldnames(('enum', 'dtg', 'ascii', 'angle', 'x1', 'x2'))
        a.Set_fieldtypes(('e', 'd', 'a', 'r', 'i', 'e'))
        stuff = {
            'enum': "valid",
            'dtg': "16/06/2003, 15:43:00.000000",
            'ascii': "some random text",
            'angle' : 1.2345,
            'x1' : 22,
            'x2' : ["aa", "aa", "bb"]
        }
        a.Set_tcontents(stuff)
        a.Check_DT_Enum_Errors()
        # should be no errors
        self.assertEqual(a.derrors().ecount(),0)
        # now introduce errors - one in a list and one a single element
        stuff['enum'] = a.TXT_UNKN_ENUM
        stuff['x2'][1] = a.TXT_UNKN_ENUM
        a.Set_tcontents(stuff)
        a.Check_DT_Enum_Errors()
        # should be two errors now
        self.assertEqual(a.derrors().ecount(),2)

    def testCheck_DT_DTG_Errors(self):
        # create a fake table and test it
        a = NPIF.Tabledata()
        a.Set_packetnum(1)
        a.Set_tablename("Rubbish")
        a.Set_fieldnames(('enum', 'dtg', 'ascii', 'angle', 'x1', 'x2'))
        a.Set_fieldtypes(('e', 'd', 'a', 'r', 'i', 'd'))
        stuff = {
            'enum': "valid",
            'dtg': "15/06/2003, 15:43:00.000000",
            'ascii': "some random text",
            'angle' : 1.2345,
            'x1' : 22,
            'x2' : ["16/06/2003, 15:43:00.000000",
                "17/06/2003, 15:43:00.000000", "18/06/2003, 15:43:00.000000"]
        }
        a.Set_tcontents(stuff)
        a.Check_DT_DTG_Errors()
        # should be no errors
        self.assertEqual(a.derrors().ecount(),0)
        # now introduce errors - one in a list and one a single element
        stuff['dtg'] = "00/00/2003, 15:43:00.000000" + a.TXT_BAD_DTG
        stuff['x2'][1] = "00/00/0000, 15:53:00.000000" + a.TXT_BAD_DTG
        a.Set_tcontents(stuff)
        a.Check_DT_DTG_Errors()
        # should be two errors now
        self.assertEqual(a.derrors().ecount(),2)

    def testCheck_DT_ASCII_Errors(self):
        # create a fake table and test it
        a = NPIF.Tabledata()
        a.Set_packetnum(1)
        a.Set_tablename("Rubbish")
        a.Set_fieldnames(('enum', 'dtg', 'ascii', 'angle', 'x1', 'x2'))
        a.Set_fieldtypes(('e', 'd', 'a', 'r', 'i', 'a'))
        stuff = {
            'enum': "valid",
            'dtg': "15/06/2003, 15:43:00.000000",
            'ascii': "some random text",
            'angle' : 1.2345,
            'x1' : 22,
            'x2' : ["words", "more words", "stuff"]
        }
        a.Set_tcontents(stuff)
        a.Check_DT_ASCII_Errors()
        # should be no errors
        self.assertEqual(a.derrors().ecount(),0)
        # now introduce errors - one in a list and one a single element
        stuff['ascii'] = "new words" + a.TXT_BAD_ASCII
        stuff['x2'][1] = "other words" + a.TXT_BAD_ASCII
        a.Set_tcontents(stuff)
        a.Check_DT_ASCII_Errors()
        # should be two errors now
        self.assertEqual(a.derrors().ecount(),2)

    def testCheck_DT_Angle_Errors(self):
        # create a fake table and test it
        a = NPIF.Tabledata()
        a.Set_packetnum(1)
        a.Set_tablename("Rubbish")
        a.Set_fieldnames(('coord', 'dtg', 'ascii', 'angle', 'x1', 'x2'))
        a.Set_fieldtypes(('c', 'd', 'a', 'r', 'c', 'r'))
        stuff = {
            'coord': (1.1, 1.2),
            'dtg': "15/06/2003, 15:43:00.000000",
            'ascii': "some random text",
            'angle' : 1.2345,
            'x1' : [(1.23, 1.23), (0.2, 0.3), (0.4, 0.5)],
            'x2' : [1.2312, 0.2432134, 0.12]
        }
        a.Set_tcontents(stuff)
        a.Check_DT_Angle_Errors()
        # should be no errors
        self.assertEqual(a.derrors().ecount(),0)
        # now introduce errors - one in a list and one a single element
        # also put an equivalent pair in coordinates
        stuff['angle'] = "5.55" + a.TXT_BAD_ANGLE
        stuff['x2'][1] = "3.35423" + a.TXT_BAD_ANGLE
        stuff['coord'] = ("5.55" + a.TXT_BAD_ANGLE, 0.55)
        stuff['x1'][1] = (0.345, "3.35423" + a.TXT_BAD_ANGLE)
        a.Set_tcontents(stuff)
        a.Check_DT_Angle_Errors()
        # should be four errors now
        self.assertEqual(a.derrors().ecount(),4)

    def testCheck_DT_Mand_Fields(self):
        # create a fake table and test it
        a = NPIF.Tabledata()
        a.Set_packetnum(1)
        a.Set_tablename("Rubbish")
        a.Set_fieldnames(('coord', 'enum', 'dtg', 'ascii', 'angle', 'x1', 'x2'))
        a.Set_fieldtypes(('c', 'e', 'd', 'a', 'r', 'i', 'a'))
        a.Set_fieldreqs(('m', 'm', 'o', 'm', 'm', 'o', 'm'))
        stuff = {
            'coord': (1.0, 2.0),
            'enum': "valid",
            'dtg': "15/06/2003, 15:43:00.000000",
            'ascii': "some random text",
            'angle' : 1.2345,
            'x1' : [22, 21, 20],
            'x2' : ["words", "more words", "stuff"]
        }
        a.Set_tcontents(stuff)
        a.Check_DT_Mand_Fields()
        # should be no errors
        self.assertEqual(a.derrors().ecount(),0)
        # now introduce errors - in a lists and in single elements
        stuff['ascii'] = a.TXT_NULL
        stuff['x2'][1] = a.TXT_NULL
        stuff['x1'][1] = a.TXT_NULL  # not error as optional
        stuff['coord'] = (a.TXT_NULL, 2.0)
        a.Set_tcontents(stuff)
        a.Check_DT_Mand_Fields()
        # should be three errors now
        self.assertEqual(a.derrors().ecount(),3)

    def testCheck_DT_Cond_Fields(self):
        # create a fake tables and test them
        a = NPIF.Tabledata()
        a.Set_packetnum(1)
        a.Set_tablename("Rubbish")
        a.Set_tablecode(a.DT_Min_Dynamic_Plat_DT)
        names = ('MSL Altitude', 'AGL Altitude', 'GPS Altitude',
            'Platform true airspeed', 'Platform ground speed',
            'Platform true Course', 'Platform Yaw')
        a.Set_fieldnames(names)
        mydict = {}
        for n in names:
            mydict[n] = 1.1
        a.Set_tcontents(mydict)
        a.Check_DT_Cond_Fields()
        # should be no errors
        self.assertEqual(a.derrors().ecount(),0)
        # add some errors
        mydict2 = {}
        for n in names:
            mydict2[n] = a.TXT_NULL
        a.Set_tcontents(mydict2)
        a.Check_DT_Cond_Fields()
        # should be 3 errors
        self.assertEqual(a.derrors().ecount(),3)
        # use same data for DT_Comp_Dynamic_Plat_DT
        a = NPIF.Tabledata()
        a.Set_packetnum(1)
        a.Set_tablename("Rubbish")
        a.Set_tablecode(a.DT_Comp_Dynamic_Plat_DT)
        a.Set_tcontents(mydict)
        a.Check_DT_Cond_Fields()
        # should be no errors
        self.assertEqual(a.derrors().ecount(),0)
        a.Set_tcontents(mydict2)
        a.Check_DT_Cond_Fields()
        # should be 3 errors
        self.assertEqual(a.derrors().ecount(),3)
        # self.DT_Event_Index_DT - have not covered all cases here
        a = NPIF.Tabledata()
        a.Set_packetnum(1)
        a.Set_tablename("Rubbish")
        a.Set_tablecode(a.DT_Event_Index_DT)
        names = ('Event Type', 'Target Number', 'Target Sub-section')
        a.Set_fieldnames(names)
        mydict = {'Event Type':a.Lookup_Event_Type(0),
            'Target Number': a.TXT_NULL,
            'Target Sub-section': 2}
        a.Set_tcontents(mydict)
        a.Check_DT_Cond_Fields()
        # should be two errors
        self.assertEqual(a.derrors().ecount(),2)
        # DT_RADAR_Sensor_Des_DT
        a = NPIF.Tabledata()
        a.Set_packetnum(1)
        a.Set_tablename("Rubbish")
        a.Set_tablecode(a.DT_RADAR_Sensor_Des_DT)
        names = ('Coordinate System Orientation', 'vld orientation')
        a.Set_fieldnames(names)
        mydict = {
            'Coordinate System Orientation': a.Lookup_RAD_Coord_Sys_Orient(8),
            'vld orientation': a.Lookup_RAD_vld_orientation(1)}
        a.Set_tcontents(mydict)
        a.Check_DT_Cond_Fields()
        # should be one error
        self.assertEqual(a.derrors().ecount(),1)
        # DT_Reference_Track_DT
        a = NPIF.Tabledata()
        a.Set_packetnum(1)
        a.Set_tablename("Rubbish")
        a.Set_tablecode(a.DT_Reference_Track_DT)
        names = ('Sensor Virtual Position MSL altitude',
            'Sensor Virtual Position AGL altitude',
            'Sensor Virtual Position GPS altitude')
        a.Set_fieldnames(names)
        mydict = {
            'Sensor Virtual Position MSL altitude': a.TXT_NULL,
            'Sensor Virtual Position AGL altitude': a.TXT_NULL,
            'Sensor Virtual Position GPS altitude': 22}
        a.Set_tcontents(mydict)
        a.Check_DT_Cond_Fields()
        # should be no errors
        self.assertEqual(a.derrors().ecount(),0)
        mydict['Sensor Virtual Position GPS altitude'] = a.TXT_NULL
        a.Set_tcontents(mydict)
        a.Check_DT_Cond_Fields()
        # should be one error
        self.assertEqual(a.derrors().ecount(),1)
        # DT_Rectified_ImGeo_DT
        a = NPIF.Tabledata()
        a.Set_packetnum(1)
        a.Set_tablename("Rubbish")
        a.Set_tablecode(a.DT_Rectified_ImGeo_DT)
        names = ('Projection type', 'Data 1', 'Data 2', 'Data 3', 'Data 4',
            'Data 5', 'Data 6', 'Data 7','Data 8', 'Data 9', 'Data 10',
            'Data 11', 'Data 12', 'Data 13', 'Data 14', 'Data 15', 'Data 16',
            'Data 17', 'Data 18', 'Data 19', 'Data 20')
        a.Set_fieldnames(names)
        mydict = {}
        for n in names:
            mydict[n] = a.TXT_NULL
        mydict['Data 1'] = 1.0
        mydict['Data 2'] = 1.0
        mydict['Data 3'] = 1.0
        mydict['Data 4'] = 1.0
        mydict['Data 5'] = 1.0
        mydict['Projection type'] = a.Lookup_Projection_type(1)
        a.Set_tcontents(mydict)
        a.Check_DT_Cond_Fields()
        # should be one error
        self.assertEqual(a.derrors().ecount(),1)
        a = NPIF.Tabledata()
        a.Set_packetnum(1)
        a.Set_tablename("Rubbish")
        a.Set_tablecode(a.DT_Rectified_ImGeo_DT)
        a.Set_fieldnames(names)
        mydict['Data 6'] = 1.0
        a.Set_tcontents(mydict)
        a.Check_DT_Cond_Fields()
        # should be no errors
        self.assertEqual(a.derrors().ecount(),0)
        a = NPIF.Tabledata()
        a.Set_packetnum(1)
        a.Set_tablename("Rubbish")
        a.Set_tablecode(a.DT_Rectified_ImGeo_DT)
        a.Set_fieldnames(names)
        mydict['Data 7'] = 1.0
        a.Set_tcontents(mydict)
        a.Check_DT_Cond_Fields()
        # should be one error
        self.assertEqual(a.derrors().ecount(),1)
        # DT_ISAR_Track_DT
        a = NPIF.Tabledata()
        a.Set_packetnum(1)
        a.Set_tablename("Rubbish")
        a.Set_tablecode(a.DT_ISAR_Track_DT)
        names = ('Track ID', 'Track type')
        a.Set_fieldnames(names)
        mydict = {
            'Track ID': "blah",
            'Track type': a.Lookup_Track_type(0)}
        a.Set_tcontents(mydict)
        a.Check_DT_Cond_Fields()
        # should be one error
        self.assertEqual(a.derrors().ecount(),1)

    def testcheck_dt_specific(self):
        # test each case separately
        a = NPIF.Tabledata()
        a.Set_packetnum(1)
        a.Set_tablename("Rubbish")
        a.Set_tablecode(a.DT_JPEG_Sensor_Quant_DT)
        key1 = a.S7023_FLD_NAMES[a.DT_JPEG_Sensor_Quant_DT][0]
        key2 = a.S7023_FLD_NAMES[a.DT_JPEG_Sensor_Quant_DT][1]
        mydict = {}
        mydict[key1] = "FFDB"
        mydict[key2] = 20
        a.Set_datasize(22)
        a.Set_tcontents(mydict)
        a.check_dt_specific()
        # should be no errors
        self.assertEqual(a.derrors().ecount(),0)
        mydict[key1] = "EFDB"
        a.Set_tcontents(mydict)
        a.check_dt_specific()
        # should be 1 errors
        self.assertEqual(a.derrors().ecount(),1)
        #
        #
        a = NPIF.Tabledata()
        a.Set_packetnum(1)
        a.Set_tablename("Rubbish")
        a.Set_tablecode(a.DT_JPEG_Sensor_Huffman_DT)
        key1 = a.S7023_FLD_NAMES[a.DT_JPEG_Sensor_Huffman_DT][0]
        key2 = a.S7023_FLD_NAMES[a.DT_JPEG_Sensor_Huffman_DT][1]
        mydict = {}
        mydict[key1] = "FFC4"
        mydict[key2] = 20
        a.Set_datasize(22)
        a.Set_tcontents(mydict)
        a.check_dt_specific()
        # should be no errors
        self.assertEqual(a.derrors().ecount(),0)
        mydict[key1] = "EFDB"
        a.Set_tcontents(mydict)
        a.check_dt_specific()
        # should be 1 errors
        self.assertEqual(a.derrors().ecount(),1)
        #
        #
        a = NPIF.Tabledata()
        a.Set_packetnum(1)
        a.Set_tablename("Rubbish")
        a.Set_tablecode(a.DT_Sensor_Grouping_DT)
        key2 = a.S7023_FLD_NAMES[a.DT_Sensor_Grouping_DT][1]
        mydict = {}
        mydict[key2] = 4
        a.Set_datasize(8)
        a.Set_tcontents(mydict)
        a.check_dt_specific()
        # should be no errors
        self.assertEqual(a.derrors().ecount(),0)
        mydict[key2] = 5
        a.Set_tcontents(mydict)
        a.check_dt_specific()
        # should be 1 errors
        self.assertEqual(a.derrors().ecount(),1)
        #
        #
        a = NPIF.Tabledata()
        a.Set_packetnum(1)
        a.Set_tablename("Rubbish")
        a.Set_tablecode(a.DT_Event_Index_DT)
        key6 = a.S7023_FLD_NAMES[a.DT_Event_Index_DT][5]
        mydict = {}
        mydict[key6] = (1.0, 1.2)
        a.Set_tcontents(mydict)
        a.check_dt_specific()
        # should be no errors
        self.assertEqual(a.derrors().ecount(),0)
        mydict[key6] = (a.TXT_NULL, a.TXT_NULL)
        a.Set_tcontents(mydict)
        a.check_dt_specific()
        # should be no errors
        self.assertEqual(a.derrors().ecount(),0)
        mydict[key6] = (0.5, a.TXT_NULL)
        a.Set_tcontents(mydict)
        a.check_dt_specific()
        # should be one errors
        self.assertEqual(a.derrors().ecount(),1)

    def testcheck_dt_suspicious_vals(self):
        # create a fake table and test it
        a = NPIF.Tabledata()
        a.Set_packetnum(1)
        a.Set_tablename("Rubbish")
        a.Set_fieldnames(('coord', 'dtg', 'ascii', 'angle', 'x1', 'x2'))
        a.Set_fieldtypes(('c', 'd', 'a', 'r', 'c', 'r'))
        stuff = {
            'coord': (1.1, 1.2),
            'dtg': "15/06/2003, 15:43:00.000000",
            'ascii': "some random text",
            'angle' : 1.2345,
            'x1' : [(1.23, 1.23), (0.2, 0.3), (0.4, 0.5)],
            'x2' : [1.2312, 0.2432134, 0.12]
        }
        a.Set_tcontents(stuff)
        a.check_dt_suspicious_vals()
        # should be no errors (warnings)
        self.assertEqual(a.derrors().ecount(),0)
        # now introduce errors - one in a list and one a single element
        # also put an equivalent pair in coordinates
        stuff['angle'] = "5.55" + a.TXT_SUS_VALUE
        stuff['x2'][1] = "3.35423" + a.TXT_SUS_VALUE
        stuff['coord'] = ("5.55" + a.TXT_SUS_VALUE, 0.55)
        stuff['x1'][1] = (0.345, "3.35423" + a.TXT_SUS_VALUE)
        a.Set_tcontents(stuff)
        a.check_dt_suspicious_vals()
        # should be four errors now
        self.assertEqual(a.derrors().ecount(),4)

    def testCalc_Requester_ID(self):
        # test a good value
        self.Tabdata.Set_dfa(69)
        self.Tabdata.Set_tablecode(self.Tabdata.DT_Requester_DT)
        self.assertEqual(self.Tabdata.Calc_Requester_ID(), 5)
        # test alternative good value (using other calc)
        self.Tabdata.Set_dfa(102)
        self.Tabdata.Set_tablecode(self.Tabdata.DT_Requester_Remarks_DT)
        self.assertEqual(self.Tabdata.Calc_Requester_ID(), 6)
        # check that if values are passed in they override the stored ones
        self.assertEqual(
            self.Tabdata.Calc_Requester_ID(self.Tabdata.DT_Requester_DT, 70), 6)
        # and again for alternative calc
        self.assertEqual(
            self.Tabdata.Calc_Requester_ID(self.Tabdata.DT_Requester_Remarks_DT,
            104), 8)
        # check that that an inappropriate table results in None
        self.assertEqual(
            self.Tabdata.Calc_Requester_ID(self.Tabdata.DT_Sensor_Grouping_DT,
            70), None)
        self.Tabdata.Set_dfa(None)
        # check that if all datafile addresses are None that None is returned
        self.assertEqual(
            self.Tabdata.Calc_Requester_ID(self.Tabdata.DT_Requester_DT, None),
            None)
        # check that a bad dfa value results in -1
        self.assertEqual(
            self.Tabdata.Calc_Requester_ID(self.Tabdata.DT_Requester_DT, 100),
            -1)
        # finally check that passed in values work with none stored in table dfa
        self.assertEqual(
            self.Tabdata.Calc_Requester_ID(self.Tabdata.DT_Requester_Remarks_DT,
            104), 8)

    def testCalc_Group_ID(self):
        # test a good value
        self.Tabdata.Set_dfa(4259960)
        self.Tabdata.Set_tablecode(self.Tabdata.DT_Sensor_Grouping_DT)
        self.assertEqual(self.Tabdata.Calc_Group_ID(), 120)
        # check that irrelevant table results in none
        self.assertEqual(
            self.Tabdata.Calc_Group_ID(self.Tabdata.DT_Requester_DT, 4259960),
            None)
        # set stored dfa to none and check that with given value of None, None
        # is also returned
        self.Tabdata.Set_dfa(None)
        self.assertEqual(
            self.Tabdata.Calc_Group_ID(self.Tabdata.DT_Sensor_Grouping_DT,
            None), None)
        # check also that with the stored value as None, that a given value
        # overrides it
        self.assertEqual(
            self.Tabdata.Calc_Group_ID(self.Tabdata.DT_Sensor_Grouping_DT,
            4259961), 121)

    def testCalc_Event_ID(self):
        # test a good value
        self.Tabdata.Set_dfa(61166)
        self.Tabdata.Set_tablecode(self.Tabdata.DT_Event_Index_DT)
        self.assertEqual(self.Tabdata.Calc_Event_ID(), 238)
        # check that irrelevant table results in none
        self.assertEqual(
            self.Tabdata.Calc_Event_ID(self.Tabdata.DT_Requester_DT, 61166),
            None)
        # set stored dfa to none and check that with given value of None, None
        # is also returned
        self.Tabdata.Set_dfa(None)
        self.assertEqual(
            self.Tabdata.Calc_Event_ID(self.Tabdata.DT_Event_Index_DT, None),
            None)
        # check also that with the stored value as None, that a given value
        # overrides it
        self.assertEqual(
            self.Tabdata.Calc_Event_ID(self.Tabdata.DT_Event_Index_DT, 61167),
            239)

    def testCalc_Segment_ID(self):
        # test a good value
        self.Tabdata.Set_dfa(45568)
        self.Tabdata.Set_tablecode(self.Tabdata.DT_Segment_Index_DT)
        self.assertEqual(self.Tabdata.Calc_Segment_ID(), 178)
        # and again for the alternative way to claculate
        self.Tabdata.Set_dfa(666)
        self.Tabdata.Set_tablecode(self.Tabdata.DT_Sensor_Index_DT)
        self.assertEqual(self.Tabdata.Calc_Segment_ID(), 154)
        # check that irrelevant table results in none
        self.assertEqual(
            self.Tabdata.Calc_Segment_ID(self.Tabdata.DT_Requester_DT, 666),
            None)
        # set stored dfa to none and check that with given value of None, None
        # is also returned
        self.Tabdata.Set_dfa(None)
        self.assertEqual(
            self.Tabdata.Calc_Segment_ID(self.Tabdata.DT_Sensor_Index_DT, None),
            None)
        # check also that with the stored value as None, that a given value
        # overrides it (for both calculation methods)
        self.assertEqual(
            self.Tabdata.Calc_Segment_ID(self.Tabdata.DT_Sensor_Index_DT, 667),
            155)
        self.assertEqual(
            self.Tabdata.Calc_Segment_ID(self.Tabdata.DT_Event_Index_DT, 45569),
            178)

    def testCalc_Location_ID(self):
        # test a good value
        self.Tabdata.Set_dfa(8169)
        self.Tabdata.Set_tablecode(self.Tabdata.DT_General_Tgt_Loc_DT)
        self.assertEqual(self.Tabdata.Calc_Location_ID(), 9)
        # check that irrelevant table results in none
        self.assertEqual(
            self.Tabdata.Calc_Location_ID(self.Tabdata.DT_Requester_DT, 8169),
            None)
        # set stored dfa to none and check that with given value of None, None
        # is also returned
        self.Tabdata.Set_dfa(None)
        self.assertEqual(
            self.Tabdata.Calc_Location_ID(self.Tabdata.DT_General_Tgt_EEI_DT,
            None), None)
        # check also that with the stored value as None, that a given value
        # overrides it
        self.assertEqual(
            self.Tabdata.Calc_Location_ID(self.Tabdata.DT_General_Tgt_EEI_DT,
            8170), 10)

    def testCalc_Target_ID(self):
        # test a good value
        self.Tabdata.Set_dfa(2720)
        self.Tabdata.Set_tablecode(self.Tabdata.DT_General_Tgt_Info_DT)
        self.assertEqual(self.Tabdata.Calc_Target_ID(), 170)
        # check that irrelevant table results in none
        self.assertEqual(
            self.Tabdata.Calc_Target_ID(self.Tabdata.DT_Requester_DT, 2720),
            None)
        # set stored dfa to none and check that with given value of None, None
        # is also returned
        self.Tabdata.Set_dfa(None)
        self.assertEqual(
            self.Tabdata.Calc_Target_ID(self.Tabdata.DT_General_Tgt_Loc_DT,
            None), None)
        # check also that with the stored value as None, that a given value
        # overrides it
        self.assertEqual(
            self.Tabdata.Calc_Target_ID(self.Tabdata.DT_General_Tgt_Loc_DT,
            2736), 171)

    def testCalc_Gimbal_ID(self):
        # test a good value
        self.Tabdata.Set_dfa(82)
        self.Tabdata.Set_tablecode(self.Tabdata.DT_Gimbals_Position_DT)
        self.assertEqual(self.Tabdata.Calc_Gimbal_ID(), 2)
        # check that irrelevant table results in none
        self.assertEqual(
            self.Tabdata.Calc_Gimbal_ID(self.Tabdata.DT_Requester_DT, 82),
            None)
        # set stored dfa to none and check that with given value of None, None
        # is also returned
        self.Tabdata.Set_dfa(None)
        self.assertEqual(
            self.Tabdata.Calc_Gimbal_ID(self.Tabdata.DT_Min_Gimbals_Att_DT,
            None), None)
        # check also that with the stored value as None, that a given value
        # overrides it
        self.assertEqual(
            self.Tabdata.Calc_Gimbal_ID(self.Tabdata.DT_Min_Gimbals_Att_DT,
            83), 3)

    def testCalc_Sensor_ID(self):
        # test a good value
        self.Tabdata.Set_sa(85)
        self.Tabdata.Set_tablecode(self.Tabdata.DT_Sensor_ID_DT)
        self.assertEqual(self.Tabdata.Calc_Sensor_ID(), 21)
        # check that irrelevant table results in none
        self.assertEqual(
            self.Tabdata.Calc_Sensor_ID(self.Tabdata.DT_Requester_DT, 85),
            None)
        # set stored sa to none and check that with given value of None, None
        # is also returned
        self.Tabdata.Set_sa(None)
        self.assertEqual(
            self.Tabdata.Calc_Sensor_ID(self.Tabdata.DT_Min_Gimbals_Att_DT,
            None), None)
        # check also that with the stored value as None, that a given value
        # overrides it
        self.assertEqual(
            self.Tabdata.Calc_Sensor_ID(self.Tabdata.DT_Min_Gimbals_Att_DT,
            86), 22)

    def testCalc_Platform_ID(self):
        # test a good value
        self.Tabdata.Set_dfa(2097152)
        self.Tabdata.Set_tablecode(self.Tabdata.DT_Comp_Dynamic_Plat_DT)
        self.assertEqual(self.Tabdata.Calc_Platform_ID(), 32)
        # check that irrelevant table results in none
        self.assertEqual(
            self.Tabdata.Calc_Platform_ID(self.Tabdata.DT_Requester_DT,
            2097152), None)
        # set stored dfa to none and check that with given value of None, None
        # is also returned
        self.Tabdata.Set_dfa(None)
        self.assertEqual(
            self.Tabdata.Calc_Platform_ID(self.Tabdata.DT_Min_Dynamic_Plat_DT,
            None), None)
        # check also that with the stored value as None, that a given value
        # overrides it
        self.assertEqual(
            self.Tabdata.Calc_Platform_ID(self.Tabdata.DT_Min_Dynamic_Plat_DT,
            2097152), 32)

    def testPrint_Table_Details(self):
        pass

    def testPrint_Table(self):
        pass

    def testFind_Datatypes_in_Table(self):
        # create a fake table and test it
        a = NPIF.Tabledata()
        a.Set_packetnum(1)
        a.Set_tablename("Rubbish")
        a.Set_fieldnames(('enum', 'dtg', 'ascii', 'angle', 'x1', 'x2'))
        a.Set_fieldtypes(('e', 'd', 'a', 'r', 'i', 'e'))
        stuff = {
            'enum': "valid",
            'dtg': "15/06/2003, 15:43:00.000000",
            'ascii': "some random text",
            'angle' : 1.2345,
            'x1' : 22,
            'x2' : ["words", "more words", "stuff"]
        }
        a.Set_tcontents(stuff)
        self.assertEqual(len(a.Find_Datatypes_in_Table('e')),2)
        self.assertEqual(a.Find_Datatypes_in_Table('e')[0],('enum', "valid"))
        self.assertEqual(len(a.Find_Datatypes_in_Table('c')),0)

class TestTablelist(unittest.TestCase):

    def setUp(self):
        self.Tablist = NPIF.Tablelist()

    def tearDown(self):
        pass

    def testCheck_Is_7023_File(self):
        testfile = './test.7023'
        testfile2 = './test2.7023'
        self.assertEqual(self.Tablist.Check_Is_7023_File(testfile), 1)
        self.assertEqual(self.Tablist.Check_Is_7023_File(testfile2), -2)
        self.assertEqual(
            self.Tablist.Check_Is_7023_File("madeupfilename_fkjsfiwvmnds"), -1)

    def testOpen_7023_File(self):
        testfile = './test.7023'
        testfile2 = './test2.7023'
        self.Tablist.Open_7023_File(testfile)
        self.assertEqual(self.Tablist.numpackets, 57)
        self.assertEqual(self.Tablist.filesize, os.stat(testfile).st_size)
        self.assertEqual(len(self.Tablist.packets), 57)
        self.assertEqual(len(self.Tablist.packetstarts), 57)
        self.assertEqual(self.Tablist.filename, os.path.abspath(testfile))
        self.assertEqual(self.Tablist.frontbytes, None)
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile2)
        self.assertEqual(a.errors.errorinfo[0][0], a.errors.E_FILENOTNPIF)
        self.assertEqual(a.errors.errorinfo[0][1], a.errors.ELVL_HIGH)
        b = NPIF.Tablelist()
        b.Open_7023_File("madeupfilename_fkjsfiwvmnds")
        self.assertEqual(b.errors.errorinfo[0][0], b.errors.E_FILEOPEN)
        self.assertEqual(b.errors.errorinfo[0][1], b.errors.ELVL_HIGH)

    def testPrint_All_Tables(self):
        pass

    def testTable_Summary(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        tdict = a.Table_Summary()
        self.assertEqual(sum(tdict.values()),a.numpackets)
        self.assertEqual(tdict[a.DT_Min_Dynamic_Plat_DT],1)
        testfile = './test3.7023'
        b = NPIF.Tablelist()
        b.Open_7023_File(testfile)
        tdict = b.Table_Summary()
        self.assertEqual(sum(tdict.values()),b.numpackets)
        self.assertEqual(tdict[b.DT_Min_Dynamic_Plat_DT],3)
        self.assertTrue(b.DT_Comp_Dynamic_Plat_DT not in tdict)

    def testPrint_Table_Summary(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        obuf = io.StringIO()
        a.Print_Table_Summary(obuf=obuf)
        newdata1 = obuf.getvalue()
        obuf.close()
        refname1 = './testPrint_Table_Summary.txt'
        reffile1 = open(refname1, 'r')
        refdata1 = reffile1.readlines()
        reffile1.close()
        result1 = difflib.unified_diff(refdata1,newdata1.splitlines(True))
        test1 = ''.join(result1)
        self.assertEqual(test1, "")

    def testPrint_Basic_File_Data(self):
        pass

    def testfile_error_checks(self):
        # just runs a bunch of the other functions
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        a.file_error_checks()
        self.assertEqual(a.errors.ecount(), 59)

    def testprintallerrorssorted(self):
        pass

    def testcheck_total_segments(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        a.check_total_segments()
        check = a.errors.whereerr(a.errors.E_NUMSEGMENTS)
        self.assertEqual(len(check), 1)

    def testcheck_segment_order(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        a.check_segment_order()
        check = a.errors.whereerr(a.errors.E_SEGORDER)
        self.assertEqual(len(check), 2)

    def testcheck_end_seg_marks(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        a.check_end_seg_marks()
        check = a.errors.whereerr(a.errors.E_ENDSEGMARK)
        self.assertEqual(len(check), 5)

    def testcheck_end_record_mark(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        a.check_end_record_mark()
        check = a.errors.whereerr(a.errors.E_ENDRECMARK)
        self.assertEqual(len(check), 1)

    def testcheck_end_segment_sizes(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        a.check_end_segment_sizes()
        check = a.errors.whereerr(a.errors.E_SEGSIZES)
        self.assertEqual(len(check), 1)

    def testcheck_compression_flag(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        a.check_compression_flag()
        check = a.errors.whereerr(a.errors.E_COMPFLAG)
        self.assertEqual(len(check), 1)

    def testcheck_datafilenumbering(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        a.check_datafilenumbering()
        check = a.errors.whereerr(a.errors.E_DFNUM)
        self.assertEqual(len(check), 30)

    def testcheck_preambleflag(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        a.check_preambleflag()
        check = a.errors.whereerr(a.errors.E_SEG0AMBLE)
        self.assertEqual(len(check), 1)

    def testidentifypostamblestyle(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)  # runs identifypostamblestyle
        self.assertEqual(a.postamblestyle, 1)

    def testcheck_postambleflags(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        a.check_postambleflags()
        check = a.errors.whereerr(a.errors.E_POSTAMBLE)
        self.assertEqual(len(check), 0)

    def testcheck_postambletables1(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        a.check_postambletables1()
        check = a.errors.whereerr(a.errors.E_POSTAMBLE)
        self.assertEqual(len(check), 0)

    def testcheck_postsegindex(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        a.check_postsegindex()
        check = a.errors.whereerr(a.errors.E_POSTAMBLE)
        self.assertEqual(len(check), 0)

    def testcheck_postsenindex(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        a.check_postsenindex()
        check = a.errors.whereerr(a.errors.E_POSTAMBLE)
        self.assertEqual(len(check), 0)

    def testcheck_posteventindex(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        a.check_posteventindex()
        check = a.errors.whereerr(a.errors.E_POSTAMBLE)
        self.assertEqual(len(check), 0)

    def testcheck_fileeditions(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        a.check_fileeditions()
        check = a.errors.whereerr(a.errors.E_EDITION)
        self.assertEqual(len(check), 1)

    def testcheck_segmentindextables(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        a.check_segmentindextables()
        check = a.errors.whereerr(a.errors.E_SEGINDEX)
        self.assertEqual(len(check), 3)

    def testcheck_eventindextables(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        a.check_eventindextables()
        check = a.errors.whereerr(a.errors.E_EVENTINDEX)
        self.assertEqual(len(check), 2)

    def testcheck_sensornumbersintables(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        a.check_sensornumbersintables()
        check = a.errors.whereerr(a.errors.E_SENSORNUM)
        self.assertEqual(len(check), 9)

    def testcheck_timetagtableexists(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        a.check_timetagtableexists()
        check = a.errors.whereerr(a.errors.E_TIMETAG)
        self.assertEqual(len(check), 0)

    def testcheck_sensoridtablesexist(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        a.check_sensoridtablesexist()
        check = a.errors.whereerr(a.errors.E_SENSORNUM)
        self.assertEqual(len(check), 2)

    def testcheck_dynamicplatformtables(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        a.check_dynamicplatformtables()
        check = a.errors.whereerr(a.errors.E_DYNAMICTABS)
        self.assertEqual(len(check), 0)

    def testcheck_sensorattitudetables(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        a.check_sensorattitudetables()
        check = a.errors.whereerr(a.errors.E_SENATTTABS)
        self.assertEqual(len(check), 0)

    def testcheck_gimbalattitudetables(self):
        testfile = './test.7023'
        a = NPIF.Tablelist()
        a.Open_7023_File(testfile)
        a.check_gimbalattitudetables()
        check = a.errors.whereerr(a.errors.E_GIMBALTABS)
        self.assertEqual(len(check), 0)

class TestGoldentables(unittest.TestCase):
	# these are all tests that are based on comparisons with another nations tool
	# they requre access to the "golden files" - edit the location in the set-up method below.
	#
	# All values have been checked manually, with the checks converted to the test cases below.
	#
    @classmethod
    def setUpClass(self):
		## Hard coded values follow. Golden Files.
        # enter the location of the three golden files here
		# first the file: 64-sensors.7023
        f64sen_file = f64sensors_GOLDEN
		# second the file: line-8.7023
        fline8_file = fline8_GOLDEN
		# third the file: step-frame-8.7023
        fstep8_file = fstepframe8_GOLDEN
        # now open them all and extract basic data
        f64sen = NPIF.Tablelist()
        fline8 = NPIF.Tablelist()
        fstep8 = NPIF.Tablelist()
        f64sen.Open_7023_File(f64sen_file, allerr=False)
        fline8.Open_7023_File(fline8_file, allerr=False)
        fstep8.Open_7023_File(fstep8_file, allerr=False)
        self.f64sen = f64sen
        self.fline8 = fline8
        self.fstep8 = fstep8

    def tearDown(self):
        pass

    def test_minimumgimbalsattitude(self):
        a = self.fstep8.packets[11]
        self.assertAlmostEqual(
            a.tcontents()["Rotation about Z-axis"],
            -5.729577951308233, places=13)
        self.assertEqual(a.tcontents()["Rotation about Y-axis"], 0)
        self.assertEqual(a.tcontents()["Rotation about X-axis"], 0)
        self.assertEqual(a.Sensor_ID_Num(), 4)
        self.assertEqual(a.Gimbal_ID_Num(), 2)

    def test_comprehensivedynamicplatform(self):
        a = self.fstep8.packets[26]
        n = a.TXT_NULL
        self.assertEqual(
            a.tcontents()['Platform Time'], "2003-03-27, 10:16:00.020000")
        self.assertAlmostEqual(
            a.tcontents()['Platform Geo-Location'][0], 51.0000036610912,
            places=13)
        self.assertAlmostEqual(
            a.tcontents()['Platform Geo-Location'][1] * 10000,
            0.14392463055206753, places=13)
        self.assertEqual(a.tcontents()['MSL Altitude'], n)
        self.assertAlmostEqual(
            a.tcontents()['AGL Altitude'], 1000.0, places=13)
        self.assertEqual(a.tcontents()['GPS Altitude'], n)
        self.assertAlmostEqual(
            a.tcontents()['Platform true airspeed'], 60.0, places=13)
        self.assertEqual(a.tcontents()['Platform ground speed'], n)
        self.assertAlmostEqual(
            a.tcontents()['Platform true Course'], 57.35860971249908, places=13)
        self.assertAlmostEqual(
            a.tcontents()['Platform true Heading'], 57.29577951308232,
            places=13)
        self.assertAlmostEqual(a.tcontents()['Platform Pitch'], 0, places=13)
        self.assertAlmostEqual(a.tcontents()['Platform Roll'], 0, places=13)
        self.assertAlmostEqual(
            a.tcontents()['Platform Yaw'], 0.06283019941676306, places=13)
        self.assertAlmostEqual(
            a.tcontents()['Platform Velocity North'], 32.362753757099256,
            places=13)
        self.assertAlmostEqual(
            a.tcontents()['Platform Velocity East'], 50.52377825595942,
            places=13)
        self.assertAlmostEqual(
            a.tcontents()['Platform Velocity Down'], 0, places=13)
        self.assertAlmostEqual(
            a.tcontents()['Platform Acceleration North'], -2.7692297494564144,
            places=13)
        self.assertAlmostEqual(
            a.tcontents()['Platform Acceleration East'], 1.775958374281572,
            places=13)
        self.assertAlmostEqual(
            a.tcontents()['Platform Acceleration Down'], 0, places=13)
        self.assertAlmostEqual(
            a.tcontents()['Platform Heading Rate'], 0, places=13)
        self.assertAlmostEqual(
            a.tcontents()['Platform Pitch Rate'], 0, places=13)
        self.assertAlmostEqual(
            a.tcontents()['Platform Roll Rate'], 0, places=13)
        self.assertAlmostEqual(
            a.tcontents()['Platform Yaw Rate'], 3.1415099708381526, places=13)
        self.assertAlmostEqual(
            a.tcontents()['Platform Heading angular Acceleration'], 0,
            places=13)
        self.assertAlmostEqual(
            a.tcontents()['Platform Pitch angular Acceleration'], 0, places=13)
        self.assertAlmostEqual(
            a.tcontents()['Platform Roll angular Acceleration'], 0, places=13)
        self.assertAlmostEqual(
            a.tcontents()['Platform Yaw angular Acceleration'],
            157.07549854190762, places=13)
        self.assertEqual(a.tcontents()['V/H'], 0.06)
        z = ['FULL SPECIFICATION', 'DE-RATED', 'FAIL', 'FULL SPECIFICATION',
            'FAIL', 'FULL SPECIFICATION', 'FAIL', 'FULL SPECIFICATION',
            'FULL SPECIFICATION', 'FULL SPECIFICATION', 'FULL SPECIFICATION',
            'FULL SPECIFICATION', 'DE-RATED', 'DE-RATED', 'DE-RATED',
            'DE-RATED', 'DE-RATED', 'DE-RATED', 'FULL SPECIFICATION',
            'FULL SPECIFICATION', 'FULL SPECIFICATION', 'FULL SPECIFICATION',
            'FULL SPECIFICATION', 'FULL SPECIFICATION', 'FULL SPECIFICATION',
            'FULL SPECIFICATION', 'DE-RATED']
        self.assertEqual(a.tcontents()['Navigational Confidence'], z)
        self.assertEqual(a.Platform_ID_Num(), 0)

    def test_generaltargeteei(self):
        a = self.fline8.packets[2]
        n = a.TXT_NULL
        self.assertEqual(
            a.tcontents()['Target Category/Essential Elements of Information'],
            "EEI for target 0 location 0")
        self.assertEqual(
            a.tcontents()['EEI/Target Category Designation Scheme'],
            "NATO STANAG 3596")
        self.assertEqual(
            a.tcontents()['Weather Over the Target Reporting Code'], "3668ALP")
        self.assertEqual(a.Target_ID_Num(), 0)
        self.assertEqual(a.Location_ID_Num(), 0)

    def test_generaltargetlocation(self):
        a = self.fline8.packets[3]
        n = a.TXT_NULL
        self.assertAlmostEqual(
            a.tcontents()['Start_ Target or Corner Location'][0], 51.35469,
            places=13)
        self.assertAlmostEqual(
            a.tcontents()['Start_ Target or Corner Location'][1], -1.868,
            places=13)
        self.assertAlmostEqual(
            a.tcontents()['Start_ Target or Corner Elevation'], 10, places=13)
        self.assertAlmostEqual(
            a.tcontents()['Target Diameter or Width'], 5, places=13)
        self.assertEqual(a.tcontents()['Map Series'], "OS")
        self.assertEqual(
            a.tcontents()['Sheet Number of Target Location'], "198")
        self.assertAlmostEqual(
            a.tcontents()['Inverse Map Scale'], 25000, places=13)
        self.assertEqual(a.tcontents()['Map Edition Number'], 1)
        self.assertEqual(a.tcontents()['Map Edition Date'], n)
        self.assertEqual(a.Target_ID_Num(), 0)
        self.assertEqual(a.Location_ID_Num(), 0)

    def test_generaltargetremarks(self):
        a = self.fline8.packets[4]
        n = a.TXT_NULL
        self.assertEqual(
            a.tcontents()['Remarks'], "Target 0 is point feature 10m diameter")
        self.assertEqual(a.Target_ID_Num(), 0)
        self.assertEqual(a.Location_ID_Num(), 0)

    def test_missionsecurity(self):
        a = self.fline8.packets[13]
        n = a.TXT_NULL
        self.assertEqual(
            a.tcontents()['Mission Security Classification'], "UNCLASSIFIED")
        self.assertEqual(
            a.tcontents()['Date'], "2003-06-12, 12:11:00.000000")
        self.assertEqual(a.tcontents()['Authority'], "General Dynamics UK")
        self.assertEqual(
            a.tcontents()['Downgrading Instructions'], "Not applicable")

    def test_airtaskingorder(self):
        a = self.fline8.packets[14]
        n = a.TXT_NULL
        self.assertEqual(
            a.tcontents()['Air Tasking Order Title'], "LINE-8")
        self.assertEqual(
            a.tcontents()['Air Tasking Order Originator'],
            "General Dynamics UK")
        self.assertEqual(
            a.tcontents()['Air Tasking Order Serial Number'], "LINE-8")
        self.assertEqual(
            a.tcontents()['Date Time Group'], "2003-06-12, 12:11:00.000000")
        self.assertEqual(a.tcontents()['Qualifier'], "001")
        self.assertEqual(a.tcontents()['Qualifier Serial Number'], 1)

    def test_requestorremarks(self):
        a = self.fline8.packets[17]
        n = a.TXT_NULL
        self.assertEqual(
            a.tcontents()['Remarks'], "Remarks from requester ID 0")
        self.assertEqual(a.Requester_Idx_Num(), 0)

    def test_sensorposition(self):
        a = self.fline8.packets[21]
        n = a.TXT_NULL
        self.assertAlmostEqual(
            a.tcontents()['X vector component'], 5, places=13)
        self.assertAlmostEqual(
            a.tcontents()['Y vector component'], 0, places=13)
        self.assertAlmostEqual(
            a.tcontents()['Z vector component'], 0, places=13)
        self.assertEqual(a.Sensor_ID_Num(), 0)

    def test_sensorcalibration(self):
        a = self.fline8.packets[26]
        n = a.TXT_NULL
        self.assertEqual(
            a.tcontents()['Calibration date'], "2003-02-01, 12:50:00.000000")
        self.assertEqual(
            a.tcontents()['Calibration Agency'], "General Dynamics UK")
        self.assertEqual(a.Sensor_ID_Num(), 0)

    def test_sensordatatiming(self):
        a = self.fline8.packets[30]
        n = a.TXT_NULL
        self.assertEqual(a.tcontents()['Frame period'], n)
        self.assertEqual(a.tcontents()['Intra Frame Time'], n)
        self.assertAlmostEqual(a.tcontents()['Line period'], 0.0051, places=13)
        self.assertAlmostEqual(
            a.tcontents()['Intra Line time'], 0.0001, places=13)
        self.assertEqual(a.Sensor_ID_Num(), 0)

    def test_generaltargetinformation(self):
        a = self.f64sen.packets[1]
        n = a.TXT_NULL
        self.assertEqual(a.tcontents()['Target Type'], "POINT")
        self.assertEqual(a.tcontents()['Target Priority'], "PRIORITY 2")
        self.assertEqual(a.tcontents()['Basic Encyclopaedia (BE) Number'], n)
        self.assertEqual(a.tcontents()['Target Security Classification'], n)
        self.assertEqual(a.tcontents()['Required Time on Target'], n)
        self.assertEqual(a.tcontents()['Requested Sensor Type'], "FRAMING")
        self.assertEqual(
            a.tcontents()['Requested Sensor Response Band'],
            "0, "+ a.TXT_UNKN_ENUM)
        self.assertEqual(
            a.tcontents()['Requested Collection Technique'],
            "0, "+ a.TXT_UNKN_ENUM)
        self.assertEqual(a.tcontents()['Number of Locations'], 1)
        self.assertEqual(a.tcontents()['Requester Address Index'], [0])
        self.assertEqual(a.tcontents()['Target Name'], "Target0")
        self.assertEqual(a.Target_ID_Num(), 0)

    def test_requester(self):
        a = self.f64sen.packets[4]
        n = a.TXT_NULL
        self.assertEqual(a.tcontents()['Report Message Type'], "RECCEXREP")
        self.assertEqual(
            a.tcontents()['Message Communications Channel'], "internet")
        self.assertEqual(
            a.tcontents()['Secondary Imagery Dissemination Channel'], "n/a")
        self.assertEqual(
            a.tcontents()['Latest Time of Intelligence Value'],
            "2003-06-12, 23:00:30.000000")
        self.assertEqual(a.tcontents()['Requester Serial Number'], "0")
        self.assertEqual(a.tcontents()['Mission Priority'], "PRIORITY 2")
        self.assertEqual(
            a.tcontents()['Requester Address'],
            "General Dynamics United Kingdom Ltd")
        self.assertEqual(
            a.tcontents()['Requester Type'], "INFORMATION REQUESTER")
        self.assertEqual(a.tcontents()['Operation Codeword'], n)
        self.assertEqual(a.tcontents()['Operation Plan Originator & Number'], n)
        self.assertEqual(a.tcontents()['Operation Option Name - Primary'], n)
        self.assertEqual(a.tcontents()['Operation Option Name - Secondary'], n)
        self.assertEqual(a.tcontents()['Exercise Nickname'], n)
        self.assertEqual(a.tcontents()['Message Additional Identifier'], n)
        self.assertEqual(a.Requester_Idx_Num(), 0)

    def test_passivesensorelement(self):
        a = self.f64sen.packets[5]
        n = a.TXT_NULL
        self.assertEqual(a.numrepeats(), 1)
        self.assertEqual(a.tcontents()['Element size'][0], 8)
        self.assertEqual(a.tcontents()['Element Bit offset'][0], 0)
        self.assertEqual(a.tcontents()['Sensor Element ID'][0], 0)
        self.assertAlmostEqual(
            a.tcontents()['Minimum wavelength'][0], 0.00000038, places=13)
        self.assertAlmostEqual(
            a.tcontents()['Maximum wavelength'][0], 0.000000705, places=13)
        self.assertEqual(a.Sensor_ID_Num(), 0)

    def test_minimumsensorattitude(self):
        a = self.f64sen.packets[6]
        n = a.TXT_NULL
        self.assertAlmostEqual(
            a.tcontents()['Rotation about Z-axis'], 0, places=13)
        self.assertAlmostEqual(
            a.tcontents()['Rotation about Y-axis'], -85.94366926962348,
            places=13)
        self.assertAlmostEqual(
            a.tcontents()['Rotation about X-axis'], 0, places=13)
        self.assertEqual(a.Sensor_ID_Num(), 0)

    def test_passivesensordescription(self):
        a = self.f64sen.packets[7]
        n = a.TXT_NULL
        self.assertEqual(a.tcontents()['Frame or Swath size'], 480)
        self.assertAlmostEqual(
            a.tcontents()['Active Line time'], 0.0015625, places=13)
        self.assertEqual(a.tcontents()['Line size of active data'], 640)
        self.assertEqual(a.tcontents()['Packets per Frame or Swath'], 1)
        self.assertEqual(
            a.tcontents()['Size of tile in the high frequency scanning direction'],
            640)
        self.assertEqual(
            a.tcontents()['Size of tile in the low frequency scanning direction'],
            480)
        self.assertEqual(a.tcontents()['Number of tiles across a line'], 1)
        self.assertEqual(a.tcontents()['Number of swaths per frame'], 1)
        self.assertEqual(a.tcontents()['Sensor mode'], "Off")
        self.assertEqual(a.tcontents()['Pixel size'], 8)
        self.assertEqual(a.tcontents()['Elements per pixel'], 1)
        self.assertEqual(
            a.tcontents()['Data Ordering'], "INACTIVE (Unispectral data)")
        self.assertAlmostEqual(
            a.tcontents()['Line FOV'], 8.594366926962348, places=13)
        self.assertAlmostEqual(
            a.tcontents()['Frame or Swath FOV'], 5.729577951308233, places=13)
        self.assertEqual(
            a.tcontents()['Number of Fields'], "NON-INTERLACED FRAMING SENSOR")
        self.assertEqual(
            a.tcontents()['High frequency scanning direction'],
            "positive direction")
        self.assertEqual(
            a.tcontents()['Low frequency scanning direction'],
            "positive direction")
        self.assertEqual(a.Sensor_ID_Num(), 0)

    def test_sensorcompression(self):
        a = self.f64sen.packets[9]
        n = a.TXT_NULL
        self.assertEqual(
            a.tcontents()['Compression algorithm'],
            "JPEG (ISO/IEC 10918-1:1994)")
        self.assertEqual(a.Sensor_ID_Num(), 0)

    def test_jpegsensorhuffman(self):
        a = self.f64sen.packets[10]
        n = a.TXT_NULL
        self.assertEqual(a.numrepeats(), 4)
        self.assertEqual(
            a.tcontents()['DHT Define Huffman Table marker'], "FFC4")
        self.assertEqual(
            a.tcontents()['Lh Length of parameters'], 418)
        self.assertEqual(
            a.tcontents()['TcTh Huffman Table Class and Table Identifier'][0],
            "Table 0 AC")
        self.assertListEqual(
            a.tcontents()['L1 Number of codes in each length'][0],
            [0, 2, 1, 3, 3, 2, 4, 3, 5, 5, 4, 4, 0, 0, 1, 125])
        self.assertIn(
            b"\x01\x02\x03\x00\x04\x11\x05\x12\x21\x31\x41\x06\x13\x51\x61\x07",
            a.tcontents()['Vij Huffman Code Values'][0])
        self.assertEqual(
            a.tcontents()['TcTh Huffman Table Class and Table Identifier'][1],
            "Table 1 AC")
        self.assertListEqual(
            a.tcontents()['L1 Number of codes in each length'][1],
            [0, 2, 1, 2, 4, 4, 3, 4, 7, 5, 4, 4, 0, 1, 2, 119])
        self.assertIn(
            b"\x00\x01\x02\x03\x11\x04\x05\x21\x31\x06\x12\x41\x51\x07\x61\x71",
            a.tcontents()['Vij Huffman Code Values'][1])
        self.assertEqual(
            a.tcontents()['TcTh Huffman Table Class and Table Identifier'][2],
            "Table 0 DC")
        self.assertListEqual(
            a.tcontents()['L1 Number of codes in each length'][2],
            [0, 1, 5, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0])
        self.assertEqual(
            b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B",
            a.tcontents()['Vij Huffman Code Values'][2])
        self.assertEqual(
            a.tcontents()['TcTh Huffman Table Class and Table Identifier'][3],
            "Table 1 DC")
        self.assertListEqual(
            a.tcontents()['L1 Number of codes in each length'][3],
            [0, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0])
        self.assertEqual(
            b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B",
            a.tcontents()['Vij Huffman Code Values'][3])
        self.assertEqual(a.Sensor_ID_Num(), 0)

    def test_jpegsensorquantisation(self):
        a = self.f64sen.packets[11]
        n = a.TXT_NULL
        self.assertEqual(a.numrepeats(), 2)
        self.assertEqual(
            a.tcontents()['DQT Define Quantisation Table Marker'], "FFDB")
        self.assertEqual(a.tcontents()['Lq Length of parameters'], 132)
        self.assertEqual(
            a.tcontents()['PqTq Quantisation table element precision'][0],
            "Table 0, 8-bit precision")
        self.assertIn(
            b"\x10\x0B\x0C\x0E\x0C\x0A\x10\x0E\x0D\x0E\x12\x11\x10\x13\x18\x28",
            a.tcontents()['Qk Quantisation table elements in zigzag order'][0])
        self.assertEqual(
            a.tcontents()['PqTq Quantisation table element precision'][1],
            "Table 1, 8-bit precision")
        self.assertIn(
            b"\x11\x12\x12\x18\x15\x18\x2F\x1A\x1A\x2F\x63\x42\x38\x42\x63\x63",
            a.tcontents()['Qk Quantisation table elements in zigzag order'][1])
        self.assertEqual(a.Sensor_ID_Num(), 0)

    def test_syncheirachyandimagebuild(self):
        a = self.f64sen.packets[12]
        n = a.TXT_NULL
        self.assertEqual(a.tcontents()['SUPER FRAME hierarchy'], 0)
        self.assertEqual(a.tcontents()['FRAME hierarchy'], 1)
        self.assertEqual(a.tcontents()['FIELD hierarchy'], 0)
        self.assertEqual(a.tcontents()['SWATH hierarchy'], 0)
        self.assertEqual(a.tcontents()['TILE hierarchy'], 0)
        self.assertEqual(a.tcontents()['LINE hierarchy'], 0)
        self.assertEqual(
            a.tcontents()['Build direction of TILE image components'],
            "not used")
        self.assertEqual(a.tcontents()['Frame Coverage Relationship'], "None")
        self.assertEqual(a.Sensor_ID_Num(), 0)

    def test_eventmarker(self):
        a = self.f64sen.packets[1514]
        n = a.TXT_NULL
        self.assertEqual(a.tcontents()['Event Number'], 1)
        self.assertEqual(
            a.tcontents()['Event Type'], "Manual Point Event/Target")
        self.assertEqual(a.tcontents()['Primary Sensor Number'], 2)
        self.assertEqual(a.tcontents()['Secondary Sensor Number'], 4)
        self.assertEqual(a.tcontents()['Third Sensor Number'], 6)
        self.assertEqual(a.tcontents()['Target number'], 0)

    def test_segmentindex(self):
        a = self.f64sen.packets[4491]
        n = a.TXT_NULL
        self.assertEqual(a.tcontents()['Start of data segment'], 47462141)
        self.assertEqual(a.tcontents()['End of data segment'], 50924984)
        self.assertEqual(
            a.tcontents()['Start time of recording'],
            "2003-06-16, 15:44:11.320000")
        self.assertEqual(
            a.tcontents()['Stop time of recording'],
            "2003-06-16, 15:45:19.720000")
        self.assertEqual(a.tcontents()['Start of Header Time Tag'], 1016)
        self.assertEqual(a.tcontents()['End of Header Time Tag'], 4436)
        self.assertEqual(
            a.tcontents()['Aircraft location at the start of recording of the segment'],
            (n, n))
        self.assertAlmostEqual(
            a.tcontents()['Aircraft location at the end of recording of the segment'][0],
            54.32785241964967, places=13)
        self.assertAlmostEqual(
            a.tcontents()['Aircraft location at the end of recording of the segment'][1],
            -2.2994690998003535, places=13)
        self.assertEqual(a.Segment_ID_Num(), 2)

    def test_eventindex(self):
        a = self.f64sen.packets[4492]
        n = a.TXT_NULL
        self.assertEqual(
            a.tcontents()['Event Type'], "Manual Point Event/Target")
        self.assertEqual(a.tcontents()['Target Number'], n)
        self.assertEqual(a.tcontents()['Target Sub-section'], 0)
        self.assertEqual(a.tcontents()['Time Tag'], 2598)
        self.assertEqual(
            a.tcontents()['Event Time'], "2003-06-16, 15:44:42.920000")
        self.assertAlmostEqual(
            a.tcontents()['Aircraft Geo-Location'][0], 54.31629794603659,
            places=13)
        self.assertAlmostEqual(
            a.tcontents()['Aircraft Geo-Location'][1], -2.299979227433912,
            places=13)
        self.assertEqual(a.tcontents()['Primary Sensor Number'], 0)
        self.assertEqual(a.tcontents()['Secondary Sensor Number'], 0)
        self.assertEqual(a.tcontents()['Third Sensor Number'], 0)
        self.assertEqual(
            a.tcontents()['Event position in the record'], 48758654)
        self.assertEqual(a.tcontents()['Event Name'], n)
        self.assertEqual(a.Segment_ID_Num(), 2)
        self.assertEqual(a.Event_ID_Num(), 1)

    def test_eventindex(self):
        a = self.f64sen.packets[4494]
        n = a.TXT_NULL
        self.assertEqual(a.numrepeats(), 1)
        self.assertEqual(
            a.tcontents()['Collection Start Time'][0],
            "2003-06-16, 15:44:27.220000")
        self.assertEqual(
            a.tcontents()['Collection Stop Time'][0],
            "2003-06-16, 15:45:19.720000")
        self.assertEqual(a.tcontents()['Start Header Time Tag'][0], 1811)
        self.assertEqual(a.tcontents()['End Header Time Tag'][0], 4436)
        self.assertAlmostEqual(
            a.tcontents()['Aircraft location at Collection Start Time'][0][0],
            54.31138382030491, places=13)
        self.assertAlmostEqual(
            a.tcontents()['Aircraft location at Collection Start Time'][0][1],
            -2.29926919724103, places=13)
        self.assertAlmostEqual(
            a.tcontents()['Aircraft location at Collection End Time'][0][0],
            54.32785241964967, places=13)
        self.assertAlmostEqual(
            a.tcontents()['Aircraft location at Collection End Time'][0][1],
            -2.2994690998003535, places=13)
        self.assertEqual(a.tcontents()['Sensor Start Position'][0], 47514460)
        self.assertEqual(a.tcontents()['Sensor End Position'][0], 50924984)
        self.assertEqual(a.Segment_ID_Num(), 2)
        self.assertEqual(a.Sensor_ID_Num(), 1)

    def test_formattimetag(self):
        a = self.f64sen.packets[0]
        n = a.TXT_NULL
        self.assertEqual(a.tcontents()['Tick Value'], 0.02)

    def test_generaladministrativereference(self):
        a = self.f64sen.packets[3]
        n = a.TXT_NULL
        self.assertEqual(a.tcontents()['Mission Number'], "64-S")
        self.assertEqual(
            a.tcontents()['Mission Start Time'], "2003-06-16, 15:43:00.000000")
        self.assertEqual(a.tcontents()['Project Identifier Code'], n)
        self.assertEqual(a.tcontents()['Number of Targets'], 1)
        self.assertEqual(a.tcontents()['Number of Requesters'], 1)

    def test_sensoridentification(self):
        a = self.f64sen.packets[8]
        n = a.TXT_NULL
        self.assertEqual(a.tcontents()['Sensor Type'], "FRAMING")
        self.assertEqual(a.tcontents()['Sensor Serial Number'], n)
        self.assertEqual(a.tcontents()['Sensor Model Number'], n)
        self.assertEqual(
            a.tcontents()['Sensor Modelling Method'],
            "BASIC SEQUENTIAL MODELLING")
        self.assertEqual(a.tcontents()['Number of Gimbals'], 0)
        self.assertEqual(a.Platform_ID_Num(), 0)
        self.assertEqual(a.Sensor_ID_Num(), 0)

    def test_endofsegmentmarker(self):
        a = self.f64sen.packets[517]
        n = a.TXT_NULL
        self.assertEqual(a.tcontents()['Size of segment'], 67898)

    def test_minimumdynamicplatform(self):
        a = self.f64sen.packets[518]
        n = a.TXT_NULL
        self.assertEqual(
            a.tcontents()['Platform Time'], "2003-06-16, 15:43:51.020000")
        self.assertAlmostEqual(
            a.tcontents()['Platform Geo-Location'][0], 54.300006291156265,
            places=13)
        self.assertAlmostEqual(
            a.tcontents()['Platform Geo-Location'][1], -2.299999979804288,
            places=13)
        self.assertEqual(a.tcontents()['MSL Altitude'], n)
        self.assertAlmostEqual(
            a.tcontents()['AGL Altitude'], 210.0, places=13)
        self.assertEqual(a.tcontents()['GPS Altitude'], n)
        self.assertAlmostEqual(
            a.tcontents()['Platform true airspeed'], 60.0, places=13)
        self.assertEqual(a.tcontents()['Platform ground speed'], n)
        self.assertAlmostEqual(
            a.tcontents()['Platform true Course'], 0.06283019941676306,
            places=13)
        self.assertAlmostEqual(
            a.tcontents()['Platform true Heading'], 0, places=13)
        self.assertAlmostEqual(a.tcontents()['Platform Pitch'], 0, places=13)
        self.assertAlmostEqual(a.tcontents()['Platform Roll'], 0, places=13)
        self.assertAlmostEqual(
            a.tcontents()['Platform Yaw'], 0.06283019941676306, places=13)
        z = ['FULL SPECIFICATION', 'DE-RATED', 'FAIL', 'FULL SPECIFICATION',
            'FAIL', 'FULL SPECIFICATION', 'FAIL', 'FULL SPECIFICATION',
            'FULL SPECIFICATION', 'FULL SPECIFICATION', 'FULL SPECIFICATION',
            'FULL SPECIFICATION']
        self.assertEqual(a.tcontents()['Navigational Confidence'], z)
        self.assertEqual(a.Platform_ID_Num(), 0)

    def test_endofrecordmarker(self):
        a = self.f64sen.packets[4496]
        n = a.TXT_NULL
        self.assertEqual(a.tcontents()['Size of record'], 51001548)

    def test_sensor(self):
        a = self.f64sen.packets[876]
        n = a.TXT_NULL
        self.assertIn(
            b"\xFF\xD8\xFF\xDB\x00\x43\x00\x10\x0B\x0C\x0E\x0C\x0A\x10\x0E\x0D",
            a.tcontents()['Sensor data'])
        self.assertEqual(a.Sensor_ID_Num(), 0)

    def test_collectionplatformidentification(self):
        a = self.fline8.packets[15]
        n = a.TXT_NULL
        self.assertEqual(a.tcontents()['Squadron'], "Squad1")
        self.assertEqual(a.tcontents()['Wing'], "Wng1")
        self.assertEqual(a.tcontents()['Aircraft Type'], "Simulation")
        self.assertEqual(a.tcontents()['Aircraft Tail Number'], "000001")
        self.assertEqual(a.tcontents()['Sortie Number'], 1)
        self.assertEqual(a.tcontents()['Pilot ID'], "GD")

    def test_sensoroperatingstatus(self):
        a = self.fline8.packets[23]
        n = a.TXT_NULL
        self.assertEqual(a.tcontents()['Status'], "In fine working order")
        self.assertEqual(a.Sensor_ID_Num(), 0)


if __name__ == '__main__':
    unittest.main()
