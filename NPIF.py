#-------------------------------------------------------------------------
# Name:        NPIF
# Purpose:     Module to manipulate, explore and test NPIF files.
#
# Author:      sfhelsdon-dstl
# Originally Created:     05/07/2013
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
Module to manipulate, explore and test NPIF files.
"""

import struct
import sys
import binascii
import math
import datetime
import re
import os
import collections


class NPIF_Error():
    """
    Error information. Intended to capture information about mistakes in input
    data, as well as cases where input data crashes code.
    """
    def __init__(self):
        """
        Initialises a set of class attributes.
        """
        self.errorcount = 0         # 0 no errors, >0 has errors
        self.errorinfo = []         # array of 3 element tuples
            # error category, error seriousness, error string
        self.maxerrorlevel = 0      # largest value in errorlevel array

    # error seriousness constants
    ELVL_WARN = 1   # warning
    ELVL_LOW = 2    # managed error (i.e. detected but handled)
    ELVL_MED = 3    # serious error (detected, but can't be handled)
    ELVL_HIGH = 4   # fatal unknown error (i.e. causes code crash)

    ERRORLVLS = (ELVL_WARN, ELVL_LOW, ELVL_MED, ELVL_HIGH)

    # error category constants
    E_HEADCRC = 1      # error with packet header CRC
    E_HEADLEN = 2      # Packet not long enough for header info
    E_EDITION = 3      # Edition number error
    E_ENUMERATION = 4  # Unknown Enumeration
    E_RESERVED = 5     # reserved field is not empty
    E_SOURCEADD = 6    # Source Address Error
    E_DFAADD = 7       # Data File Address Error
    E_UKNPACKET = 8    # unidentified packet
    E_DATALEN = 9      # length of data packet
    E_EXTRABYTE = 10   # extra bytes present, outside of packet
    E_ADDRESSEXTRACT = 11  # error extracting from sa or dfa
    E_USERDEFINED = 12  # user defined table
    E_DATACRC = 13     # data crc error
    E_DTG = 14         # DTG error
    E_ASCII = 15       # ASCII error
    E_ANGLE = 16       # Angle Error
    E_CONDFIELD = 17   # Conditional Field
    E_MANDFIELD = 18   # Mandatory Field
    E_JPEGVALS = 19    # Huffman table lengths
    E_FILEOPEN = 20    # file cannot be opened
    E_FILENOTNPIF = 21  # file is not a 7023 file
    E_NUMSEGMENTS = 22  # too many segments
    E_SEGORDER = 23    # segment ordering
    E_ENDSEGMARK = 24  # end of segment markers don't exist
    E_ENDRECMARK = 25  # end of record marker
    E_SEGSIZES = 26    # segment sizes
    E_COMPFLAG = 27    # Compression Flag
    E_FRONTFILLER = 28  # Front Filler bytes
    E_DFNUM = 29       # data file numbering
    E_SEG0AMBLE = 30   # segment zero preamble
    E_INDEXAMBLE = 31  # index tables outside postamble
    E_POSTAMBLE = 32   # Postamble related error
    E_SENGROUP = 33    # sensor grouping related error
    E_OPTCOORD = 34    # error in optional coordinate field
    E_SEGINDEX = 35    # error in segement index table
    E_EVENTINDEX = 36  # error in event index table
    E_SENSORNUM = 37   # error in sensor number
    E_TIMETAG = 38     # errors with existence of time tag tables
    E_DYNAMICTABS = 39  # errors with dynamic tables
    E_SENATTTABS = 40  # errors with sensor attitude tables
    E_GIMBALTABS = 41  # errors with gimbal attitude tables
    E_SUSVALUE = 42    # suspicious values

    E_UNKNOWN = 999   # unknown error

    # Tuple of all error types - all values above should be included here
    ETYPES = (E_HEADCRC, E_HEADLEN, E_EDITION,
        E_ENUMERATION, E_RESERVED, E_SOURCEADD, E_DFAADD,
        E_UKNPACKET, E_DATALEN, E_EXTRABYTE, E_ADDRESSEXTRACT,
        E_USERDEFINED, E_DATACRC, E_DTG, E_ASCII, E_ANGLE,
        E_CONDFIELD, E_MANDFIELD, E_JPEGVALS, E_FILEOPEN,
        E_FILENOTNPIF, E_NUMSEGMENTS, E_SEGORDER, E_ENDSEGMARK,
        E_ENDRECMARK, E_SEGSIZES, E_COMPFLAG, E_FRONTFILLER,
        E_DFNUM, E_SEG0AMBLE, E_INDEXAMBLE, E_POSTAMBLE,
        E_SENGROUP, E_OPTCOORD, E_SEGINDEX, E_EVENTINDEX,
        E_SENSORNUM, E_TIMETAG, E_DYNAMICTABS, E_SENATTTABS,
        E_GIMBALTABS, E_SUSVALUE,
        E_UNKNOWN)

    # for each of the error types a chunk of text to indicate what is being checked for
    # should be an entry for everything in ETYPES
    ETYPES_TXT = collections.defaultdict (lambda: "Checking for <Unrecognised Error Type> ...", {
        E_HEADCRC: "Checking for any errors in Header CRC values ...",
        E_HEADLEN: "Checking for packet headers that are too short ...",
        E_EDITION: "Checking for packets with invalid Edition numbers ...",
        E_ENUMERATION: "Checking for any errors in Enumeration values ...",
        E_RESERVED: "Checking if reserved header fields are empty ...",
        E_SOURCEADD: "Checking for unrecognised Source Addresses ...",
        E_DFAADD: "Checking for unrecognised Data File Addresses ...",
        E_UKNPACKET: "Checking for any unidentified tables ...",
        E_DATALEN: "Checking for data packet lengths outsize expected ranges ...",
        E_EXTRABYTE: "Checking for filler bytes after packets ...",
        E_ADDRESSEXTRACT: "Checking for errors with values derived from Source or Data File addresses ...",
        E_USERDEFINED: "Checking for any User Defined Tables ...",
        E_DATACRC: "Checking for any errors in Data CRC values ...",
        E_DTG: "Checking for any errors in DTG values ...",
        E_ASCII: "Checking for any invalid ASCII in ASCII data ...",
        E_ANGLE: "Checking for any out of range angles ...",
        E_CONDFIELD: "Checking that conditional fields are correctly used ...",
        E_MANDFIELD: "Checking for NULL values in Mandatory Fields ...",
        E_JPEGVALS: "Checking for invalid data in any jpeg tables ...",
        E_FILEOPEN: "Checking for errors opening files ...",
        E_FILENOTNPIF: "Checking if the file looks like STANAG 7023 ...",
        E_NUMSEGMENTS: "Checking for errors in numbers of segments ...",
        E_SEGORDER: "Checking for errors in the ordering of segments ...",
        E_ENDSEGMARK: "Checking that End of Segment tables exist at segment changes ...",
        E_ENDRECMARK: "Checking that End of Record tables exist in correct places and have correct segment number and claimed size ...",
        E_SEGSIZES: "Checking that End of Segment tables have the correct sizes in them ...",
        E_COMPFLAG: "Checking for correct use of compression flag ...",
        E_FRONTFILLER: "Checking for any filler bytes at front of file ...",
        E_DFNUM: "Checking data file numbers are correct ...",
        E_SEG0AMBLE: "Checking that preamble looks OK ...",
        E_INDEXAMBLE: "Checking that index tables exist in postambles ...",
        E_POSTAMBLE: "Checking that Postambles are set up correctly ...",
        E_SENGROUP: "Checking for errors in any sensor groupings ...",
        E_OPTCOORD: "Checking for errors in any optional coordinate fields ...",
        E_SEGINDEX: "Checking for errors within any Segment Index tables ...",
        E_EVENTINDEX: "Checking for errors within any Event Index tables ...",
        E_SENSORNUM: "Checking for errors associated with sensor numbers ...",
        E_TIMETAG: "Checking for existance of appropriate Format Time Tag Tables ...",
        E_DYNAMICTABS: "Checking for errors with Dynamic Platform tables ...",
        E_SENATTTABS: "Checking for errors with Sensor Attitude tables ...",
        E_GIMBALTABS: "Checking for errors with Gimbal Attitude tables ...",
        E_SUSVALUE: "Checking for values flagged as suspicious ...",

        E_UNKNOWN: "Checking for any unknown errors ..."
        })

    def adderror(self, etype, elevel, etext):
        """
        Adds error information to the data structure.
        etype is the errors class (class constants are defined)
        elevel is the seriousness of the error (class constants are defined)
        etext is a string containing info about the error
        """

        if etype not in self.ETYPES:
            etype = self.E_UNKNOWN  # default to unknown

        if elevel not in self.ERRORLVLS:
            elevel = self.ELVL_HIGH  # default to most serious

        self.errorinfo.append((etype, elevel, str(etext)))

        self.errorcount += 1
        if elevel > self.maxerrorlevel:
            self.maxerrorlevel = elevel

    def ecount(self):
        """
        Returns the total number of errors stored
        """
        return self.errorcount

    def einfo(self, num):
        """
        Returns 3 element tuple, containing the error info for error
        number <num> (from the errorinfo array).
        tuple contains: error category, error seriousness, error string
        """
        if num > self.errorcount or num < 0:
            return (None,None,None)
        else:
            return self.errorinfo[num]

    def emaxlvl(self):
        """
        Return a number indicating the highest error seriousness stored in the data
        """
        return self.maxerrorlevel

    def whereerr(self, etype):
        """
        Given an error type (from ETYPE), return a list with the indexes where
        instances of an error matching this type are.
        If none are found it returns an empty list.
        """
        return [i for i,z in enumerate(self.errorinfo) if z[0] == etype]

    def printerrors(self, obuf=sys.stdout, strictcsv=False):
        """
        Prints all error information stored in data structure.
        Default output is sys.stdout, but this can be redirected using obuf.
        With strictcsv as False, csv output will have added spaces so that it
        is easy to read in a simple text editor.
        Returns a tuple containing number of warnings and number of errors.
        """
        wcount = 0
        ecount = 0
        if strictcsv == False:
            outstring = "{0:<9}, {1:<80}\n"
        else:
            outstring = "{0},{1}\n"

        for etype, lvl, txt in self.errorinfo:
            if lvl == self.ELVL_WARN:
                firstbit = "WARNING:"
                wcount += 1
            else:
                firstbit = "ERROR:"
                ecount += 1
            obuf.write(outstring.format(firstbit, txt))
        return (wcount,ecount)

    def printerrorsoftype(self, errtype, obuf=sys.stdout, strictcsv=False):
        """
        Prints all error information stored in data structure corresponding to
        error type, errtype.
        Default output is sys.stdout, but this can be redirected using obuf.
        With strictcsv as False, csv output will have added spaces so that it
        is easy to read in a simple text editor.
        Returns a tuple containing number of warnings and number of errors
        matching errtype.
        """
        wcount = 0
        ecount = 0
        if strictcsv == False:
            outstring = "{0:<9}, {1:<80}\n"
        else:
            outstring = "{0},{1}\n"

        for etype, lvl, txt in self.errorinfo:
            if etype == errtype:
                if lvl == self.ELVL_WARN:
                    firstbit = "WARNING:"
                    wcount += 1
                else:
                    firstbit = "ERROR:"
                    ecount += 1
                obuf.write(outstring.format(firstbit, txt))
        return (wcount, ecount)


class NPIF_Header():
    """
    Defines a set of info relevant to packet header.
    """
    def __init__(self):
        """
        Initialises a set of class attributes to default values.
        """
        # basic stuff from 7023 header (as described in standard - representation as below)
        self.edition = None          # integer
        self.compressflag = None     # 1 (on) or 0 (off)
        self.crcflag = None          # 1 (on) or 0 (off)
        self.ambleflag = None        # 1 (on) or 0 (off)
        self.segmentnum = None       # integer
        self.sourceaddress = None    # integer
        self.datafileaddress = None  # integer
        self.datafilesize = None     # integer
        self.datafilenum = None      # integer
        self.timetag = None          # integer
        self.synctype = None         # Lookup table - Text
        self.reserved = None         # Hex string
        self.headcrc = None          # Hex string
        # encoded inferred header items (when appropriate)
        # these are calculated from above stuff using info from the standard
        self.Requester_Idx_Num = None  # integer, Requester Index
        self.Group_ID_Num = None     # integer, Group ID
        self.Event_ID_Num = None     # integer, Event ID
        self.Segment_ID_Num = None   # integer, Segment ID
        self.Location_ID_Num = None  # integer, Location ID
        self.Target_ID_Num = None    # integer, Target ID
        self.Gimbal_ID_Num = None    # integer, Gimbal ID
        self.Sensor_ID_Num = None    # integer, Sensor ID
        self.Platform_ID_Num = None  # integer, Platform ID
        # data housekeeping
        self.tablecode = 0           # integer, which data table present: values from S7023_ALL_VALID_TABLES
        self.sourcecode = 0          # integer, for source type: values defined later all begin with SA_
        self.errors = NPIF_Error()   # NPIF_Error object
        self.totlen = None           # integer
            # includes sync, hdr, data + any extras (e.g. filler)
        self.claimlen = None         # integer
            # as totlen, but excluding any extras (e.g. filler)
        self.extraraw = None         # Hex string
            # any filler bytes at end of packet
        self.packetnum = None        # integer
            # packet number in parent file (count from 0)
        self.blockdataextract = False  # bool
            # set to true to indicate no data packet extraction
        self.tablename = None        # text


class NPIF_DataContent():
    """
    Defines a set of info relevant to data in a packet.
    Excludes header data.
    """
    def __init__(self):
        """
        Initialises a set of class attributes to default values.
        """
        self.dataraw = None         # raw data packet values (excludes header)
        self.datacrc = None         # CRC value if present
        self.errors = NPIF_Error()  # NPIF_Error object
        self.numfieldsrepeating = None # if repeated groups of fields, this indicates how many fields repeat
        self.numrepeats = None      # how many times repeated fields repeat
        self.fieldnames = None      # tuple of the filed names in data packet
        self.fieldtypes = None      # tuple of the field types
        self.fieldfuncs = None      # tuple of what functions (if any) should be applied to field values
        self.fieldlflags = None     # tuple of list flags (used to derive repeated elements) - see S7023_FLD_LIST_FLAGS for examples
        self.fieldreqs = None       # tuple of obligation on fields (e.g. optional, mandatory, etc)
        self.data_flens = None      # tuple of lengths in bytes of each field
        self.tcontents = None       # dict with keys from fieldnames and derived values


class NPIF():

    """
    Defines basic definitions for NPIF data and simple methods to extract elements.
    """

    # Set up some class constants
    HDR_FLENGTHS = (1, 1, 1, 1, 4, 4, 4, 8, 1, 5, 2) # field lengths of the header data
    HDR_LEN = 32            # Length of the Header. Does not include synchronisation field
    SYNC_LEN = 10           # sync filed length
    SYNC_FIELD = b"\x0D\x79\xAB\x21\x6F\x34\x1A\x72\xB9\x1C" # value of the sync field
    TXT_UNKN_ENUM = "UNKNOWN EMUMERATION ####****"      # Text for an unknown enumeration value
    TXT_BAD_DTG = "INVALID DTG  ####****"               # Text for an invalid Date-Time value
    TXT_BAD_ASCII = "INVALID ASCII PRESENT ####****"    # text for a bad ASCII field (generally with non ASCII characters)
    TXT_NULL = "<NULL>"                                 # Text for a NULL value
    TXT_NOTINUSE = "Not in use"                         # Occasional fields override the NULL to mean not in use - this is the text for that
    TXT_BAD_ANGLE = "ANGLE OUT OF RANGE ####****"       # Text for an out of allowed range Angle
    TXT_SUS_VALUE = "SUSPICIOUS VALUE ####****"         # Text for a suspicious but not necesarilly incorrect value
    TXT_UNKN_ERROR = "UNKNOWN ERROR ####****"           # text for an Unknown Error
    DATA_MAXPKTSIZE = 4294967295                        # Maximum Packet size in bytes
    DATA_VALID_ED = (1, 2, 3, 4)                        # Tuple with valid standard edition numbers

    S7023_RAW_CAP = 0
    # if set to something other than 0, will cap any raw data (that created by
    # Conv_Raw) at the value above. If value is non zero and 16 or less,
    # this will definetly break the current code, so use a larger value.
    # This *may* help with memory usage on very large files, if you are not
    # specifically interested in detail of the raw data.

    # table data constants appear later

    def __init__(self):
        """
        Creates a NPIF_Header and NPIF_DataContent attributes within the class.
        """
        self.hdr = NPIF_Header()
        self.tdat = NPIF_DataContent()

    def edition(self):
        """
        Return the current value of edition in data model
        Packet Header related info.
        """
        return self.hdr.edition

    def Set_edition(self, new):
        """
        Set edition to the given integer value in data model
        Packet Header related info.
        """
        self.hdr.edition = new

    def compressflag(self):
        """
        Return the current value of compressflag in data model (1=on, 0=off)
        Packet Header related info.
        """
        return self.hdr.compressflag

    def Set_compressflag(self, new):
        """
        Set compressflag to the given value in data model (1=on, 0=off)
        Packet Header related info.
        """
        self.hdr.compressflag = new

    def crcflag(self):
        """
        Return the current value of crcflag in data model (1=on, 0=off)
        Packet Header related info.
        """
        return self.hdr.crcflag

    def Set_crcflag(self, new):
        """
        Set crcflag to the given integer value in data model (1=on, 0=off)
        Packet Header related info.
        """
        self.hdr.crcflag = new

    def ambleflag(self):
        """
        Return the current value of ambleflag in data model (1=on, 0=off)
        Packet Header related info.
        """
        return self.hdr.ambleflag

    def Set_ambleflag(self, new):
        """
        Set ambleflag to the given integer value in data model (1=on, 0=off)
        Packet Header related info.
        """
        self.hdr.ambleflag = new

    def segment(self):
        """
        Return the current value of segmentnum in data model
        Packet Header related info.
        """
        return self.hdr.segmentnum

    def Set_segment(self, new):
        """
        Set segmentnum to the given integer value (>=0) in data model
        Packet Header related info.
        """
        self.hdr.segmentnum = new

    def sa(self):
        """
        Return the current value of sourceaddress in data model
        Packet Header related info.
        """
        return self.hdr.sourceaddress

    def Set_sa(self, new):
        """
        Set sourceaddress to the given integer value in data model
        Packet Header related info.
        """
        self.hdr.sourceaddress = new

    def dfa(self):
        """
        Return the current value of datafileaddress in data model
        Packet Header related info.
        """
        return self.hdr.datafileaddress

    def Set_dfa(self, new):
        """
        Set datafileaddress to the given integer value in data model
        Packet Header related info.
        """
        self.hdr.datafileaddress = new

    def datasize(self):
        """
        Return the current value of datafilesize in data model
        Packet Header related info.
        """
        return self.hdr.datafilesize

    def Set_datasize(self, new):
        """
        Set datafilesize to the given value (bytes) in data model
        Packet Header related info.
        """
        self.hdr.datafilesize = new

    def nocrcdatasize(self):
        """
        Return the current value data file size, ignoring any CRC bytes if
        present
        Packet Header related info.
        """
        if self.hdr.crcflag != 0:
            return self.hdr.datafilesize - 2
        else:
            return self.hdr.datafilesize

    def dfn(self):
        """
        Return the current value of datafilenum in data model
        Packet Header related info.
        """
        return self.hdr.datafilenum

    def Set_dfn(self, new):
        """
        Set datafilenum to the given integer value in data model
        Packet Header related info.
        """
        self.hdr.datafilenum = new

    def timetag(self):
        """
        Return the current value of timetag in data model
        Packet Header related info.
        """
        return self.hdr.timetag

    def Set_timetag(self, new):
        """
        Set timetag to the given integer value in data model
        Packet Header related info.
        """
        self.hdr.timetag = new

    def synctype(self):
        """
        Return the current value of synctype in data model
        Packet Header related info.
        """
        return self.hdr.synctype

    def Set_synctype(self, new):
        """
        Set synctype to the given value in data model (text values from Lookup_Sync_Type_Code function)
        Packet Header related info.
        """
        self.hdr.synctype = new

    def reserved(self):
        """
        Return the current value of reserved in data model
        Packet Header related info.
        """
        return self.hdr.reserved

    def Set_reserved(self, new):
        """
        Set reserved to the given value in data model (note type undefined in standard)
        Packet Header related info.
        """
        self.hdr.reserved = new

    def headcrc(self):
        """
        Return the current value of headcrc in data model
        Packet Header related info.
        """
        return self.hdr.headcrc

    def Set_headcrc(self, new):
        """
        Set headcrc to the given value in data model (text string with hex characters)
        Packet Header related info.
        """
        self.hdr.headcrc = new

    def Requester_Idx_Num(self):
        """
        Return the current value of Requester_Idx_Num in data model
        Packet Header related info.
        """
        return self.hdr.Requester_Idx_Num

    def Set_Requester_Idx_Num(self, new):
        """
        Set Requester_Idx_Num to the given integer value in data model
        Packet Header related info.
        """
        self.hdr.Requester_Idx_Num = new

    def Group_ID_Num(self):
        """
        Return the current value of Group_ID_Num in data model
        Packet Header related info.
        """
        return self.hdr.Group_ID_Num

    def Set_Group_ID_Num(self, new):
        """
        Set Group_ID_Num to the given integer value in data model
        Packet Header related info.
        """
        self.hdr.Group_ID_Num = new

    def Event_ID_Num(self):
        """
        Return the current value of Event_ID_Num in data model
        Packet Header related info.
        """
        return self.hdr.Event_ID_Num

    def Set_Event_ID_Num(self, new):
        """
        Set Event_ID_Num to the given integer value in data model
        Packet Header related info.
        """
        self.hdr.Event_ID_Num = new

    def Segment_ID_Num(self):
        """
        Return the current value of Segment_ID_Num in data model
        Packet Header related info.
        """
        return self.hdr.Segment_ID_Num

    def Set_Segment_ID_Num(self, new):
        """
        Set Segment_ID_Num to the given integer value in data model
        Packet Header related info.
        """
        self.hdr.Segment_ID_Num = new

    def Location_ID_Num(self):
        """
        Return the current value of Location_ID_Num in data model
        Packet Header related info.
        """
        return self.hdr.Location_ID_Num

    def Set_Location_ID_Num(self, new):
        """
        Set Location_ID_Num to the given integer value in data model
        Packet Header related info.
        """
        self.hdr.Location_ID_Num = new

    def Target_ID_Num(self):
        """
        Return the current value of Target_ID_Num in data model
        Packet Header related info.
        """
        return self.hdr.Target_ID_Num

    def Set_Target_ID_Num(self, new):
        """
        Set Target_ID_Num to the given integer value in data model
        Packet Header related info.
        """
        self.hdr.Target_ID_Num = new

    def Gimbal_ID_Num(self):
        """
        Return the current value of Gimbal_ID_Num in data model
        Packet Header related info.
        """
        return self.hdr.Gimbal_ID_Num

    def Set_Gimbal_ID_Num(self, new):
        """
        Set Gimbal_ID_Num to the given integer value in data model
        Packet Header related info.
        """
        self.hdr.Gimbal_ID_Num = new

    def Sensor_ID_Num(self):
        """
        Return the current value of Sensor_ID_Num in data model
        Packet Header related info.
        """
        return self.hdr.Sensor_ID_Num

    def Set_Sensor_ID_Num(self, new):
        """
        Set Sensor_ID_Num to the given integer value in data model
        Packet Header related info.
        """
        self.hdr.Sensor_ID_Num = new

    def Platform_ID_Num(self):
        """
        Return the current value of Platform_ID_Num in data model
        Packet Header related info.
        """
        return self.hdr.Platform_ID_Num

    def Set_Platform_ID_Num(self, new):
        """
        Set Platform_ID_Num to the given integer value in data model
        Packet Header related info.
        """
        self.hdr.Platform_ID_Num = new

    def tablecode(self):
        """
        Return the current value of tablecode in data model
        Packet Header related info.
        """
        return self.hdr.tablecode

    def Set_tablecode(self, new):
        """
        Set tablecode to the given integer value in data model
        Packet Header related info.
        """
        self.hdr.tablecode = new

    def sourcecode(self):
        """
        Return the current value of sourcecode in data model
        Packet Header related info.
        """
        return self.hdr.sourcecode

    def Set_sourcecode(self, new):
        """
        Set sourcecode to the given integer value in data model
        Packet Header related info.
        """
        self.hdr.sourcecode = new

    def totlen(self):
        """
        Return the current value of totlen in data model
        Packet Header related info.
        """
        return self.hdr.totlen

    def Set_totlen(self, new):
        """
        Set totlen to the given integer value in data model
        Packet Header related info.
        """
        self.hdr.totlen = new

    def claimlen(self):
        """
        Return the current value of claimlen in data model
        Packet Header related info.
        """
        return self.hdr.claimlen

    def Set_claimlen(self, new):
        """
        Set claimlen to the given integer value in data model
        Packet Header related info.
        """
        self.hdr.claimlen = new

    def extraraw(self):
        """
        Return the current value of extraraw in data model
        Packet Header related info.
        """
        return self.hdr.extraraw

    def Set_extraraw(self, new):
        """
        Set extraraw to the given integer value in data model
        Packet Header related info.
        """
        self.hdr.extraraw = new

    def packetnum(self):
        """
        Return the current value of packetnum in data model
        Packet Header related info.
        """
        return self.hdr.packetnum

    def Set_packetnum(self, new):
        """
        Set packetnum to the given integer value in data model
        Packet Header related info.
        """
        self.hdr.packetnum = new

    def blockdataextract(self):
        """
        Return the current value of blockdataextract in data model
        Packet Header related info.
        """
        return self.hdr.blockdataextract

    def Set_blockdataextract(self, new):
        """
        Set blockdataextract to the given value (True/False) in data model
        Packet Header related info.
        """
        self.hdr.blockdataextract = new

    def herrors(self):
        """
        Return the current value error structure for the header in data model
        Packet Header related info.
        """
        return self.hdr.errors

    def tablename(self):
        """
        Return the current value of tablename in data model
        Packet Header related info.
        """
        return self.hdr.tablename

    def Set_tablename(self, new):
        """
        Set tablename to the given string value in data model
        Packet Header related info.
        """
        self.hdr.tablename = new

    def dataraw(self):
        """
        Return the current value of dataraw in data model
        Packet Data related info.
        """
        return self.tdat.dataraw

    def Set_dataraw(self, new):
        """
        Set dataraw to the given binary string value in data model
        Packet Data related info.
        """
        self.tdat.dataraw = new

    def datacrc(self):
        """
        Return the current value of datacrc in data model
        Packet Data related info.
        """
        return self.tdat.datacrc

    def Set_datacrc(self, new):
        """
        Set datacrc to the given value in data model (text string with hex characters)
        Packet Data related info.
        """
        self.tdat.datacrc = new

    def numfieldsrepeating(self):
        """
        Return the current value of numfieldsrepeating in data model
        Packet Data related info.
        """
        return self.tdat.numfieldsrepeating

    def Set_numfieldsrepeating(self, new):
        """
        Set numfieldsrepeating to the given integer value (>=0) in data model
        Packet Data related info.
        """
        self.tdat.numfieldsrepeating = new

    def numrepeats(self):
        """
        Return the current value of numrepeats in data model
        Packet Data related info.
        """
        return self.tdat.numrepeats

    def Set_numrepeats(self, new):
        """
        Set numrepeats to the given integer value (>=0) in data model
        Packet Data related info.
        """
        self.tdat.numrepeats = new

    def fieldnames(self):
        """
        Return the current value of fieldnames in data model
        Packet Data related info.
        """
        return self.tdat.fieldnames

    def Set_fieldnames(self, new):
        """
        Set fieldnames to the given value in data model (tuple of strings - see S7023_FLD_NAMES)
        Packet Data related info.
        """
        self.tdat.fieldnames = new

    def fieldtypes(self):
        """
        Return the current value of fieldtypes in data model
        Packet Data related info.
        """
        return self.tdat.fieldtypes

    def Set_fieldtypes(self, new):
        """
        Set fieldtypes to the given value in data model (tuple of strings - see S7023_FLD_TYPES)
        Packet Data related info.
        """
        self.tdat.fieldtypes = new

    def fieldfuncs(self):
        """
        Return the current value of fieldfuncs in data model
        Packet Data related info.
        """
        return self.tdat.fieldfuncs

    def Set_fieldfuncs(self, new):
        """
        Set fieldfuncs to the given value in data model (tuple containing None's or functions - see S7023_FLD_FUNCS)
        Packet Data related info.
        """
        self.tdat.fieldfuncs = new

    def fieldlflags(self):
        """
        Return the current value of fieldlflags in data model
        Packet Data related info.
        """
        return self.tdat.fieldlflags

    def Set_fieldlflags(self, new):
        """
        Set fieldlflags to the given value in data model (tuple with 0s and 1s - see S7023_FLD_LIST_FLAGS)
        Packet Data related info.
        """
        self.tdat.fieldlflags = new

    def fieldreqs(self):
        """
        Return the current value of fieldreqs in data model
        Packet Data related info.
        """
        return self.tdat.fieldreqs

    def Set_fieldreqs(self, new):
        """
        Set fieldreqs to the given value in data model (tuple of strings - see S7023_FLD_REQS)
        Packet Data related info.
        """
        self.tdat.fieldreqs = new

    def data_flens(self):
        """
        Return the current value of data_flens in data model
        Packet Data related info.
        """
        return self.tdat.data_flens

    def Set_data_flens(self, new):
        """
        Set data_flens (Field Lengths) to the given value in data model (tuple of integers - S7023_FLD_LENGTHS)
        Packet Data related info.
        """
        self.tdat.data_flens = new

    def tcontents(self):
        """
        Return the current value of the tcontents dict
        Packet Data related info.
        """
        return self.tdat.tcontents

    def Set_tcontents(self, new):
        """
        Set tcontents to the given dict value in data model 
        Packet Data related info.
        """
        self.tdat.tcontents = new

    def derrors(self):
        """
        Return the current value error structure for the data in data model
        Packet Data related info.
        """
        return self.tdat.errors

    # now follows a large number of lookup functions all of which convert codes to text values
    ###############################

    def Lookup_Sync_Type_Code(self, scode):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Sync code from
        a packet header return a string describing the Sync type.

        """
        if scode == 0:
            return "INACTIVE"
        elif scode == 1:
            return "SUPER FRAME SYNC"
        elif scode == 2:
            return "FRAME SYNC"
        elif scode == 4:
            return "FIELD SYNC"
        elif scode == 8:
            return "SWATH SYNC"
        elif scode == 10:
            return "LINE SYNC"
        elif scode == 12:
            return "TILE SYNC"
        else:
            return str(scode) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Antenna_weight(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Antenna
        weighting, return a string describing the meaning.

        """
        if eint == 0:
            return "Uniform"
        elif eint == 1:
            return "-20dB m = 6 Taylor"
        elif eint == 2:
            return "-25dB m = 12 Taylor"
        elif eint == 3:
            return "-30dB m = 23 Taylor"
        elif eint == 4:
            return "-35dB m = 44 Taylor"
        elif eint == 5:
            return "-40dB m = 81 Taylor"
        elif eint == 6:
            return "-40dB m = 6 Dolph-Chebyshev"
        elif eint == 7:
            return "-50dB m = 6 Dolph-Chebyshev"
        elif eint == 8:
            return "-60dB m = 6 Dolph-Chebyshev"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Autofocus_proc_alg(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Autofocus
        processing algorithms, return a string describing the meaning.

        """
        if eint == 0:
            return "None"
        elif eint == 1:
            return "Motion compensation (MOCO) only"
        elif eint == 2:
            return "Phase gradient plus MOCO"
        elif eint == 3:
            return "Phase difference plus MOCO"
        elif eint == 4:
            return "Multilook registration plus MOCO"
        elif eint == 5:
            return "Contrast optimisation plus MOCO"
        elif eint == 6:
            return "Prominent point processing plus MOCO"
        elif eint == 7:
            return "Mapdrift plus MOCO"
        elif eint == 8:
            return "Multiple Aperture Mapdrift plus MOCO"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Azimuth_comp_proc(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Azimuth
        compression processing algorithm, return a string describing the
        meaning.

        """
        if eint == 0:
            return "None"
        elif eint == 1:
            return "Enhanced real beam"
        elif eint == 2:
            return "Real beam"
        elif eint == 3:
            return "Doppler"
        elif eint == 4:
            return "Polar format"
        elif eint == 5:
            return "Range migration"
        elif eint == 6:
            return "Chirp scaling"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Codestream_cap(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Codestream
        capability, return a string describing the meaning.

        """
        if eint == 1:
            return "Profile 0 (see ITU-T T.800 | IS 15444-1 AMD-1)"
        elif eint == 2:
            return "Profile 1"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Comb_op(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Combination
        operation, return a string describing the meaning.

        """
        if eint == 0:
            return "Addition"
        elif eint == 1:
            return "Subtraction"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Comp_Alg(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for compression
        algorithm, return a string describing the meaning.

        """
        if eint == 2:
            return "JPEG (ISO/IEC 10918-1:1994)"
        elif eint == 3:
            return "JPEG 2000 (ISO/IEC 15444-1)"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Coverage_Rel(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Coverage
        Relationship, return a string describing the meaning.

        """
        if eint == 0:
            return "None"
        elif eint == 1:
            return "100% Overlapped (nominally identical coverage)"
        elif eint == 2:
            return "less than 100% Overlapped"
        elif eint == 3:
            return "Abutted"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Dir_road_curv(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Direction of
        road curvature, return a string describing the meaning.

        """
        if eint == 0:
            return "Unused"
        elif eint == 1:
            return "Clockwise"
        elif eint == 2:
            return "Anti-clockwise"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Dir_vehicle_radvel(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Direction of
        vehicle radial velocity, return a string describing the meaning.

        """
        if eint == 0:
            return "Unused"
        elif eint == 1:
            return "Away from the sensor"
        elif eint == 2:
            return "Towards the sensor"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Event_Type(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Event Type,
        return a string describing the meaning.

        """
        if eint == 0:
            return "Pre-programmed Point Event/Target"
        elif eint == 1:
            return "Pre-programmed Duration START"
        elif eint == 2:
            return "Pre-programmed Duration END"
        elif eint == 3:
            return "Manual Point Event/Target"
        elif eint == 4:
            return "Manual Duration START"
        elif eint == 5:
            return "Manual Duration END"
        elif eint == 6:
            return "Recce Waypoint"
        elif eint == 7:
            return "Automatically Generated Event"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Group_type(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Group type,
        return a string describing the meaning.

        """
        if eint == 0:
            return "Coverage"
        elif eint == 1:
            return "Spectral"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Image_Build_Dir(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Image Build
        direction, return a string describing the meaning.

        """
        if eint == 0:
            return "not used"
        elif eint == 1:
            return "PDA is X positive; SDA is Y positive"
        elif eint == 2:
            return "PDA is X positive; SDA is Y negative"
        elif eint == 3:
            return "PDA is X negative; SDA is Y positive"
        elif eint == 4:
            return "PDA is X negative; SDA is Y negative"
        elif eint == 5:
            return "PDA is Y positive; SDA is X positive"
        elif eint == 6:
            return "PDA is Y positive; SDA is X negative"
        elif eint == 7:
            return "PDA is Y negative; SDA is X positive"
        elif eint == 8:
            return "PDA is Y negative; SDA is X negative"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Interpulse_mod_type(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Interpulse
        modulation type, return a string describing the meaning.

        """
        if eint == 0:
            return "None"
        elif eint == 1:
            return "Chirp"
        elif eint == 2:
            return "Binary phase code - Barker"
        elif eint == 3:
            return "Binary phase code - Galois"
        elif eint == 4:
            return "Quadrature phase code"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_JPEG_2000_IREP(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for IREP,
        return a string describing the meaning.

        """
        if eint == 0:
            return "BCS-A"
        elif eint == 1:
            return "MONO"
        elif eint == 2:
            return "RGB"
        elif eint == 3:
            return "RGB/LUT"
        elif eint == 4:
            return "MULTI"
        elif eint == 5:
            return "NODISPLY"
        elif eint == 6:
            return "NVECTOR"
        elif eint == 7:
            return "POLAR"
        elif eint == 9:
            return "VPH"
        elif eint == 10:
            return "YCbCr601"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_JPEG_2000_Tiling(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for JPEG 2000
        Tiling performed, return a string describing the meaning.

        """
        if eint == 0:
            return "No JPEG 2000 Tiling has been used"
        elif eint == 1:
            return "JPEG 2000 Tiling has been used"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Mission_Priority_Type(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Mission
        Priority Type, return a string describing the meaning.

        """
        if eint == 1:
            return "PRIORITY 1 (TOP PRIORITY)"
        elif eint == 2:
            return "PRIORITY 2"
        elif eint == 3:
            return "PRIORITY 3"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Nav_Conf(self, nav_integer):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Navigational
        confidence, return a string describing the meaning.

        """
        if nav_integer == 0:
            return "FAIL"
        elif nav_integer == 1:
            return "POSSIBLE FAILURE"
        elif nav_integer == 2:
            return "DE-RATED"
        elif nav_integer == 3:
            return "FULL SPECIFICATION"
        else:
            return str(nav_integer) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Num_Fields(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Number of
        Fields, return a string describing the meaning.

        """
        if eint == 0:
            return "INVALID"
        elif eint == 1:
            return "NON-INTERLACED FRAMING SENSOR"
        elif eint >= 2 and eint <= 255:
            return str(eint) + " FIELDS"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_PassSens_Mode(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Sensor Mode,
        return a string describing the meaning.

        """
        if eint == 0:
            return "Off"
        elif eint == 1:
            return "On"
        elif eint == 2:
            return "Standby"
        # missing 3 is deliberate
        elif eint == 4:
            return "Test"
        elif eint == 5:
            return "Fail"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_PassSens_Ordering(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Data Ordering,
        return a string describing the meaning.

        """
        if eint == 0:
            return "INACTIVE (Unispectral data)"
        elif eint == 1:
            return "BAND INTERLEAVED BY PIXEL"
        elif eint == 2:
            return "BAND SEQUENTIAL"
        elif eint == 3:
            return "BAND INTERLEAVED BY LINE"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_PassSens_Scan_Dir(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Sensor Scan
        Direction, return a string describing the meaning.

        """
        if eint == 0:
            return "negative direction"
        elif eint == 1:
            return "positive direction"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Physical_characteristic(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Physical
        characteristic, return a string describing the meaning.

        """
        if eint == 0:
            return "Radar measurement"
        elif eint == 1:
            return "Height"
        elif eint == 2:
            return "Velocity (image referenced (x, y))"
        elif eint == 3:
            return "Velocity (ground referenced (N, E))"
        elif eint == 4:
            return "Radial velocity component from antenna to pixel"
        elif eint == 5:
            return "MTI indication"
        elif eint == 6:
            return "Radar measurement MTI"
        elif eint == 7:
            return "Pixel validity"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Polarisation(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Polarisation,
        return a string describing the meaning.

        """
        if eint == 0:
            return "HH"
        elif eint == 1:
            return "VV"
        elif eint == 2:
            return "HV"
        elif eint == 3:
            return "VH"
        elif eint == 255:
            return "Polarisation unassigned"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_proc_weight(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for processing
        weighting, return a string describing the meaning.

        """
        if eint == 0:
            return "Uniform"
        elif eint == 1:
            return "-20dB m = 6 Taylor"
        elif eint == 2:
            return "-25dB m = 12 Taylor"
        elif eint == 3:
            return "-30dB m = 23 Taylor"
        elif eint == 4:
            return "-35dB m = 44 Taylor"
        elif eint == 5:
            return "-40dB m = 81 Taylor"
        elif eint == 6:
            return "-40dB m = 6 Dolph-Chebyshev"
        elif eint == 7:
            return "-50dB m = 6 Dolph-Chebyshev"
        elif eint == 8:
            return "-60dB m = 6 Dolph-Chebyshev"
        elif eint == 9:
            return "Spatially varying apodisation"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Prog_order(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Progression
        order, return a string describing the meaning.

        """
        if eint == 0:
            return "Layer-Resolution-Component-Position"
        elif eint == 1:
            return "Resolution-Layer-Component-Position"
        elif eint == 2:
            return "Resolution-Position-Component-Layer"
        elif eint == 3:
            return "Position-Component-Resolution-Layer"
        elif eint == 4:
            return "Component-Position-Resolution-Layer"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Projection_type(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Projection
        type, return a string describing the meaning.

        """
        if eint == 0:
            return "Unused"
        elif eint == 1:
            return "Cartesian plane projection"
        elif eint == 2:
            return "Stereographic"
        elif eint == 3:
            return "Transverse Mercator"
        elif eint == 4:
            return "Mercator"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Pulse_to_pulse_mod(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Pulse-to-pulse
        modulation type, return a string describing the meaning.

        """
        if eint == 0:
            return "None"
        elif eint == 1:
            return "Linear step"
        elif eint == 2:
            return "Pseudo-random step"
        elif eint == 3:
            return "Pseudo-random"
        elif eint == 4:
            return "Step plus pseudo-random"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_RAD_Coord_Sys_Orient(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Coordinate
        System Orientation, return a string describing the meaning.

        """
        if eint == 0:
            return "vld is X positive; cvld is Y positive"
        elif eint == 1:
            return "vld is X positive; cvld is Y negative"
        elif eint == 2:
            return "vld is X negative; cvld is Y positive"
        elif eint == 3:
            return "vld is X negative; cvld is Y negative"
        elif eint == 4:
            return "vld is Y positive; cvld is X positive"
        elif eint == 5:
            return "vld is Y positive; cvld is X negative"
        elif eint == 6:
            return "vld is Y negative; cvld is X positive"
        elif eint == 7:
            return "vld is Y negative; cvld is X negative"
        elif eint == 8:
            return "Rectified imagery"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_RAD_Data_order(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Data ordering,
        return a string describing the meaning.

        """
        if eint == 0:
            return "Inactive (Single element data)"
        elif eint == 1:
            return "Element interleaved by pixel"
        elif eint == 2:
            return "Element sequential"
        elif eint == 3:
            return "Element interleaved by line"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_RAD_mode(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for RADAR mode,
        return a string describing the meaning.

        """
        if eint == 0:
            return "Swath"
        elif eint == 1:
            return "Spotlight"
        elif eint == 2:
            return "Real beam ground map"
        elif eint == 3:
            return "Enhanced real beam ground map"
        elif eint == 4:
            return "Doppler beam sharpened map"
        elif eint == 5:
            return "SAR overlaid with MTI"
        elif eint == 6:
            return "Interferometric SAR"
        elif eint == 7:
            return "Polarimetric SAR"
        elif eint == 8:
            return "Inverse SAR"
        elif eint == 9:
            return "Side-looking Array SAR (SLAR)"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_RAD_Phys_coord_sys(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Physical
        coordinate system, return a string describing the meaning.

        """
        if eint == 0:
            return "Range; Cross Range"
        elif eint == 1:
            return "Across Track; Along Track"
        elif eint == 2:
            return "Range; Azimuth"
        elif eint == 3:
            return "X; Y (Rectified imagery)"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_RAD_Sensor_mode(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Sensor mode,
        return a string describing the meaning.

        """
        if eint == 0:
            return "OFF"
        elif eint == 1:
            return "ON"
        elif eint == 2:
            return "STANDBY"
        # no 3 is deliberate
        elif eint == 4:
            return "TEST"
        elif eint == 5:
            return "FAIL"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_RAD_vld_orientation(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for vld
        orientation, return a string describing the meaning.

        """
        if eint == 0:
            return "Unused"
        elif eint == 1:
            return "Starboard; i.e. value of alpha is positive"
        elif eint == 2:
            return "Port; i.e. value of alpha is negative"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Range_comp_proc_alg(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Range
        compression processing algorithm, return a string describing the
        meaning.

        """
        if eint == 0:
            return "None"
        elif eint == 1:
            return "Stretch compression"
        elif eint == 2:
            return "Analogue matched filter"
        elif eint == 3:
            return "Digital matched filter"
        elif eint == 4:
            return "Stretch plus matched filter"
        elif eint == 5:
            return "Step plus matched filter"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Report_Message_Type(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Report Message
        Type, return a string describing the meaning.

        """
        if eint == 1:
            return "INFLIGHTREP"
        elif eint == 2:
            return "RECCEXREP"
        elif eint == 3:
            return "IPIR/SUPIR"
        elif eint == 4:
            return "IPIR/SUPIR (ADP)"
        elif eint == 5:
            return "RADARXREP"
        elif eint == 6:
            return "RECCEXREP (ADP)"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Req_Collect_Tech(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Requested
        Collection Technique, return a string describing the meaning.

        """
        if eint == 1:
            return "VERTICAL"
        elif eint == 2:
            return "FORWARD OBLIQUE"
        elif eint == 3:
            return "RIGHT OBLIQUE"
        elif eint == 4:
            return "LEFT OBLIQUE"
        elif eint == 5:
            return "BEST POSSIBLE"
        elif eint == 16:
            return "SWATH"
        elif eint == 17:
            return "SPOTLIGHT"
        elif eint == 18:
            return "RBGM"
        elif eint == 19:
            return "ENHANCED RBGM"
        elif eint == 20:
            return "DBSM"
        elif eint == 21:
            return "SAR OVERLAID WITH MTI"
        elif eint == 22:
            return "INSAR"
        elif eint == 23:
            return "POLSAR"
        elif eint == 24:
            return "INVSAR"
        elif eint == 25:
            return "SLAR"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Req_Sensor_Resp_Band(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Requested
        Sensor Response Band, return a string describing the meaning.

        """
        if eint == 1:
            return "VISUAL"
        elif eint == 2:
            return "NEAR IR"
        elif eint == 3:
            return "IR"
        elif eint == 4:
            return "DUAL BAND"
        elif eint == 16:
            return "MICROWAVE"
        elif eint == 17:
            return "mm WAVE"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Req_Sensor_Type(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Requested
        Sensor Type, return a string describing the meaning.

        """
        if eint == 1:
            return "FRAMING"
        elif eint == 2:
            return "LINESCAN"
        elif eint == 3:
            return "PUSHBROOM"
        elif eint == 4:
            return "PAN FRAME"
        elif eint == 5:
            return "STEP FRAME"
        elif eint == 16:
            return "SAR"
        elif eint == 17:
            return "MTI (other than 4607)"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Requester_Type(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Mission
        Priority Type, return a string describing the meaning.

        """
        if eint == 1:
            return "MISSION REQUESTER"
        elif eint == 2:
            return "INFORMATION REQUESTER"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Sensor_Coding_Type(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for sensor coding
        type, return a string describing the type.

        """
        if eint == 0:
            return "Reserved"
        elif eint == 1:
            return "FRAMING"
        elif eint == 2:
            return "LINESCAN"
        elif eint == 3:
            return "PUSHBROOM"
        elif eint == 4:
            return "PAN FRAME"
        elif eint == 5:
            return "STEP FRAME"
        elif eint == 16:
            return "RADAR real (single mode)"
        elif eint == 17:
            return "MTI (other than 4607)"
        elif eint == 18:
            return "RADAR virtual"
        elif eint == 19:
            return "RADAR multi-mode"
        elif eint == 20:
            return "4607"
        elif eint == 21:
            return "4609"
        elif eint == 22:
            return "RANGE FINDER"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Sensor_Mod_Meth(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Sensor
        Modelling Method, return a string describing the meaning.

        """
        if eint == 0:
            return "BASIC SEQUENTIAL MODELLING"
        elif eint == 1:
            return "VECTOR MODELLING"
        elif eint == 2:
            return "COLLECTION PLANE"
        elif eint == 3:
            return "RECTIFIED IMAGE"
        elif eint == 4:
            return "ABSOLUTE VALUE (FOR RANGE FINDER)"
        elif eint == 255:
            return "NOT APPLICABLE"
        elif eint >= 5 and eint <= 254:
            return "RESERVED"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Tgt_Cat_Desig_Scheme(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Target
        Category Designation Scheme, return a string describing the meaning.

        """
        if eint == 1:
            return "NATO STANAG 3596"
        # elif eint == 0 : return "None" # null value
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Target_Type(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Target Type,
        return a string describing the meaning.

        """
        if eint == 0:
            return "POINT"
        elif eint == 1:
            return "LINE"
        elif eint == 2:
            return "AREA"
        # deliberate that 3 is missing
        elif eint == 4:
            return "STRIP"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Terrain_model(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Terrain model,
        return a string describing the meaning.

        """
        if eint == 0:
            return "no DTM used"
        elif eint == 1:
            return "DTED"
        elif eint == 255:
            return "other DTM used"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Timing_accuracy(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Timing
        accuracy, return a string describing the meaning.

        """
        if eint == 0:
            return "Real Number"
        elif eint == 1:
            return "Short Float (IEEE 32-bit definition)"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Timing_method(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Timing method,
        return a string describing the meaning.

        """
        if eint == 0:
            return "CUMULATIVE"
        elif eint == 1:
            return "DIFFERENTIAL"
        elif eint == 255:
            return "UNUSED"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Timing_relationship(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Timing
        relationship, return a string describing the meaning.

        """
        if eint == 0:
            return "Simultaneous"
        elif eint == 1:
            return "Sequential"
        elif eint == 255:
            return "No timing relationship"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Track_type(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Track type,
        return a string describing the meaning.

        """
        if eint == 0:
            return "Unused"
        elif eint == 1:
            return "Link 16"
        elif eint == 2:
            return "NATO Track number (NTN)"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Trans_Func_Type(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Transfer
        Function Type, return a string describing the meaning.

        """
        if eint == 0:
            return "Linear"
        elif eint == 1:
            return "Logarithmic (natural)"
        elif eint == 2:
            return "Exponential"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Type_of_Element(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Type of
        Element, return a string describing the meaning.

        """
        if eint == 0:
            return "Unsigned Binary"
        elif eint == 1:
            return "Signed Binary"
        elif eint == 2:
            return "Real Number"
        elif eint == 3:
            return "Short Float (IEEE 32-bit definition)"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Unit_Meas_CrossVirt(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for CrossVirtual
        Look Direction, return a string describing the meaning.

        """
        if eint == 0:
            return "angular (radians)"
        elif eint == 1:
            return "distance (metres)"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Use_of_element(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Use of
        element, return a string describing the meaning.

        """
        if eint == 0:
            return "Magnitude Radar Measurement"
        elif eint == 1:
            return "Phase"
        elif eint == 2:
            return "In phase (I)"
        elif eint == 3:
            return "Quadrature (Q)"
        elif eint == 4:
            return "Velocity Magnitude"
        elif eint == 5:
            return "Velocity Direction Angle"
        elif eint == 6:
            return "Radial Velocity (negative if approaching)"
        elif eint == 7:
            return "v_x or v_N"
        elif eint == 8:
            return "v_y or v_E"
        elif eint == 9:
            return "Value"
        elif eint == 16:
            return "(Magnitude)**2"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    def Lookup_Vect_or_Tim_Mod(self, eint):
        """
        Return a string corresponding to the given integer enumeration.

        Given an int derived from the STANAG 7023 enumeration for Vector model
        or for Timing Model, return a string describing the meaning.

        """
        if eint == 0:
            return "Sample by sample"
        elif eint == 1:
            return "Pixel by pixel"
        else:
            return str(eint) + ", " + self.TXT_UNKN_ENUM

    # End of lookup functions
    
    # Now follows a set of conversion functions, whch generally convert a raw value into a more readable form
    ##############################################################################
    
    def Conv_DTG(self, dtg):
        """
        Given a buffer containing the 7023 encoded date-time info, return a
        string with year-month-day hour:min:sec.fsec
        """
        # First check for zeroed-out date:
        if len(dtg) != 8:
            return self.TXT_BAD_DTG
        elif self.Conv_Int_NC(dtg) == 0:
            return self.TXT_NULL
        else:
            #
            f = struct.unpack('>H4BH', dtg[0:8])
            year = f[0]
            month = f[1]
            day = f[2]
            hour = f[3]
            mins = f[4]
            sec = f[5] // 1000
            microsec = (f[5] % 1000) * 1000
            # There may be invalid date values
            if year == 0 or month == 0 or day == 0:
                outstr = " year ({0}) month ({1}) day ({2})".format(year, month,
                                                                    day)
                return self.TXT_BAD_DTG + outstr
            else:
                d = datetime.datetime(year, month, day, hour, mins, sec,
                                      microsec)
                return '{0:%Y-%m-%d, %H:%M:%S.%f}'.format(d)

    def Conv_Coord(self, coords7023):
        """
        Return a lat-lon tuple given 7023 encoded data for lat-lon
        """
        lat_radians = self.Conv_Real(coords7023[:8])
        lon_radians = self.Conv_Real(coords7023[8:])
        lat = self.Conv_Degrees_NC(lat_radians)
        if lat != self.TXT_NULL:
            if lat < -90.0 or lat > 90.0:
                lat = str(lat) + ", " + self.TXT_BAD_ANGLE
        lon = self.Conv_Degrees(lon_radians)
        return (lat, lon)

    def Conv_Real(self, indat):
        """
        Return a 8 byte real number (double) from the 7023 data.
        Returns NULL text if appropriate
        """
        a = struct.unpack('>d', indat)[0]
        if math.isnan(a):
            return self.TXT_NULL
        else:
            return a

    def Conv_Int_NC(self, indat):
        """
        Return an unsigned int based on bytes of 7023 data (doesn't check
        for NULL values).
        This function can deal with any number of bytes, but is not a fast as
        some of the others with fixed lengths
        """
        return int.from_bytes(indat, byteorder='big')

    def Conv_Int(self, indat):
        """
        Return an unsigned int based on the 7023 data, after checking for NULL
        values.
        This function can deal with any number of bytes.

        Strictly there are 4 7023 tables where an all 'F' hex value is valid
        and not NULL. These are:
        - General Admin, field 4
        - Event Marker, field 1
        - Sensor Sample Coordinat description, fields 2, 4, & 6
        - JPEG 2000 Description, field 4
        These fields should not call thus function, and call the NoCheck
        version instead
        """
        a = self.Conv_Hex(indat).lstrip('F')
        if a == "":
            return self.TXT_NULL
        else:
            return self.Conv_Int_NC(indat)

    def Conv_ASCII(self, indat):
        """
        Return ASCII test based on the 7023 data, after checking for NULL
        values. Also checks for non ASCII characters.
        """
        a = indat.rstrip(b'\x00')
        if a == b"":
            return self.TXT_NULL
        else:
            try:
                b = a.decode("ascii", 'strict')
            except UnicodeError:
                outstr = " convertable ascii= " + a.decode("ascii", 'ignore')
                b = self.TXT_BAD_ASCII + outstr
            return b

    def Conv_I2Blist(self, inint, width=32):
        """
        Converts a given integer into a list of binary 0s and 1s with the
        given width (pads with 0s to get width if needed).
        If inint is larger than width binary elements can display, it will
        be truncated to the width Least significant bits.
        """
        l1 = list("{0:0>{wid}b}".format(inint, wid=width))
        if len(l1) > width:
            return l1[-width:]
        else:
            return l1

    def Conv_bin1ind(self, inint, width=32):
        """
        Should give a list of those indices in the binary equivalent of 'inint'
        that are set to 1.
        width defines the size of the binary i.e. width=32 means will pad to
        left with zeros to 32 binary elements.
        If inint is larger than width binary elements can display, it will be
        truncated to the width Least significant bits.
        """
        b = self.Conv_I2Blist(inint, width=width)
        b.reverse()
        c = [x for x, y in enumerate(b) if y == '1']
        return c

    def Conv_nav_full(self, inint, bwidth, ncodes):
        """
        Convert the integer to a binary of width bwidth, group in binary
        pairs, convert to ints and then convert ncodes from LSB end into 7023
        navigational confidence statements and return that list.
        If ncodes is too big for the given bwidth, cap it at its max sensible
        size.
        Typically sensible values for bwidth and ncodes are:
        - 24 & 12 for minimum dynamic table
        - 56 & 27 for comprehensive dynamic table
        Should normally be called from Conv_nav.
        """
        if ncodes * 2 > bwidth:
            ncodes = bwidth // 2
        s1 = "{0:0>{wid}b}".format(inint, wid=bwidth)
        s2 = re.findall('[01]{2}', s1)
        s2.reverse()
        nl = []
        for i in range(ncodes):
            nl.append(int(s2[i], 2))
        navt = list(map(self.Lookup_Nav_Conf, nl))
        return navt

    def Conv_nav(self, inraw):
        """
        Convert input raw data to a list of strings describing the STANAG 7023
        navigational confidence codes.
        """
        z = len(inraw)
        zint = self.Conv_Int_NC(inraw)
        # work out which of the two possible functions have called this code
        # and hence set appropriate variables
        if z == 3:
            # minimum dynamic table
            bwidth = 3 * 8
            ncodes = 12
        else:
            # comprehensive dynamic table
            bwidth = 7 * 8
            ncodes = 27
        return self.Conv_nav_full(zint, bwidth, ncodes)

    def Conv_Hex(self, indat, outcap=0):
        """
        Convert the given data to a hex string and return it.
        cap length of output at 'outcap' bytes - if outcap <=0 then do not cap.
        """
        if outcap > 0:
            s = min(len(indat), outcap)
            indat = indat[0:s]
        return binascii.hexlify(indat).upper().decode("ascii")

    def Conv_Raw(self, indat):
        """
        Do nothing - just keep data in whever format the stream is in.
        If global cap on raw data has been set then cap length of raw data
        at this value.
        """
        if self.S7023_RAW_CAP > 0:
            # if global set cap length of raw data (may break things...)
            s = min(len(indat), self.S7023_RAW_CAP)
            return indat[0:s]
        else:
            return indat

    def Conv_Degrees(self, angle):
        """
        Convert radians to degrees after checking for NULL values and out
        of range angles
        """
        if angle == self.TXT_NULL:
            return self.TXT_NULL
        else:
            a = math.degrees(angle)
            # check for out of range angles
            if angle >= -math.pi and angle < math.pi:
                return a
            else:
                return str(a) + ", " + self.TXT_BAD_ANGLE

    def Conv_Degrees2(self, angle):
        """
        Convert radians to degrees after checking for NULL values as well as
        flagging up values outside of the range 0 - 180 degrees as suspicious.
        (relevant to certain tables/fields)
        """
        if angle == self.TXT_NULL:
            return self.TXT_NULL
        else:
            a = math.degrees(angle)
            # check for out of range angles
            if angle >= 0 and angle <= math.pi:
                return a
            else:
                return str(a) + ", " + self.TXT_SUS_VALUE

    def Conv_Degrees3(self, angle):
        """
        Convert radians to degrees after checking for NULL values as well as
        flagging up values outside of the range -180 to +180 degrees as
        suspicious.
        (relevant to certain tables/fields)
        """
        if angle == self.TXT_NULL:
            return self.TXT_NULL
        else:
            a = math.degrees(angle)
            # check for out of range angles
            if angle >= -math.pi and angle <= math.pi:
                return a
            else:
                return str(a) + ", " + self.TXT_SUS_VALUE

    def Conv_Degrees_NC(self, angle):
        """
        Convert radians to degrees after checking for Null values, but don't
        check for out of range angles
        """
        if angle == self.TXT_NULL:
            return self.TXT_NULL
        else:
            return math.degrees(angle)

    def Conv_JPEG_PqTq(self, inint):
        """
        Given the encoded PqTq data (as an int) return a string
        giving the precision and quantisation table number
        """
        z = (inint >> 4) & 15
        y = inint & 15
        if z == 0:
            t = "8-bit precision"
        else:
            t = "16-bit precision"
        u = "Table " + str(y)
        v = u + ", " + t
        return v

    def Conv_Huff_TcTh(self, inint):
        """
        Given the encoded TcTh data (as an int) return a string
        giving the table type and the table number
        """
        z = (inint >> 4) & 15
        y = inint & 15
        if z == 0:
            t = "DC"
        else:
            t = "AC"
        u = "Table " + str(y)
        v = u + " " + t
        return v

    def Conv_Hufflengths(self, buff):
        """
        Given a buffer containing the 16 raw huffman values, return a 16
        element list with the lengths as integers
        """
        nl = struct.unpack('>16B', buff)
        return list(nl)

    def Conv_notinuse(self, invalue):
        """
        Checks the input value for NULL and if present returns a "Not in Use"
        string, otherwise returns the original value.

        Use for functions where a NULL value should be interpreted as not used.
        """
        if self.TXT_NULL in str(invalue):
            return self.TXT_NOTINUSE
        else:
            return invalue

    ###################################################################################
    # Now follows a set of hardcoded data, much of which is extracted from the standard 
    #
    # Data: the different data types used and the basic functions to be applied
    # to each of them
    S7023_F_Conversions = {
        'a': Conv_ASCII,                # ascii data
        'd': Conv_DTG,                  # 7023 encoded Dtate-Time value
        'c': Conv_Coord,                # lat-lon coord pair
        'r': Conv_Real,                 # real number
        'i': Conv_Int,                  # integer
        'j': Conv_Int_NC,               # integer - but one where the normal
                                        # integer NULL value is a valid value
        'h': Conv_Hex,                  # hex
        'e': Conv_Int_NC,               # should also call a Lookup function
        'b': Conv_Int_NC,               # should also call
                                        # Convert_binary_1_indices
        'q': Conv_Raw,                  # keep as raw data, but expect to call
                                            # function on this raw
        'x': Conv_Raw,                  # keep as raw data
        'z': None                       # no conversion function
    }

    # Data: 7023 Source Address related constants
    # - each allocated a unique integer number
    SA_Format_Description_Data = 1
    SA_Mission_Data = 2
    SA_Target_Data = 3
    SA_Platform_Data = 4
    SA_Segment_Event_Index_Data = 5
    SA_User_Defined_Data = 6
    SA_Sensor_Parametric_Data = 7
    SA_Sensor_Data = 8
    SA_Reserved = 9
    SA_Urecognised = 10
    SA_BAD = 11  # Genric code for a bad value

    # Data: linking source address codes to their textual description
    SA_INFO = collections.defaultdict (lambda: "Unrecognised Source Address", {
        SA_Format_Description_Data: "Format Description",
        SA_Mission_Data: "Mission",
        SA_Target_Data: "Target",
        SA_Platform_Data: "Platform",
        SA_Segment_Event_Index_Data: "Segment/Event Index",
        SA_User_Defined_Data: "User Defined",
        SA_Sensor_Parametric_Data: "Sensor Parametric",
        SA_Sensor_Data: "Sensor",
        SA_Reserved: "Reserved",
        SA_Urecognised: "Unrecognised Source Address",
        SA_BAD: "Unrecognised Source Address"
    })

    # Data: 7023 data tables = each data table allocated a unique integer
    # number
    DT_Format_Time_Tag_DT = 1
    DT_General_Admin_Ref_DT = 2
    DT_Mission_Security_DT = 3
    DT_Air_Tasking_Order_DT = 4
    DT_Collection_Plat_ID_DT = 5
    DT_Requester_DT = 6
    DT_Requester_Remarks_DT = 7
    DT_General_Tgt_Info_DT = 8
    DT_General_Tgt_Loc_DT = 9
    DT_General_Tgt_EEI_DT = 10
    DT_General_Tgt_Remarks_DT = 11
    DT_Min_Dynamic_Plat_DT = 12
    DT_Comp_Dynamic_Plat_DT = 13
    DT_Sensor_Grouping_DT = 14
    DT_End_Record_Marker_DT = 15
    DT_End_Segment_Marker_DT = 16
    DT_Event_Marker_DT = 17
    DT_Segment_Index_DT = 18
    DT_Event_Index_DT = 19
    DT_User_Defined_DT = 20
    DT_Sensor_ID_DT = 21
    DT_PASSIVE_Sensor_Des_DT = 22
    DT_Sensor_Calibration_DT = 23
    DT_Sync_Hier_and_ImBld_DT = 24
    DT_Sensor_Data_Timing_DT = 25
    DT_Sensor_Op_Status_DT = 26
    DT_Sensor_Position_DT = 27
    DT_Min_Sensor_Att_DT = 28
    DT_Comp_Sensor_Att_DT = 29
    DT_Gimbals_Position_DT = 30
    DT_Min_Gimbals_Att_DT = 31
    DT_Comp_Gimbals_Att_DT = 32
    DT_Sensor_Index_DT = 33
    DT_Passive_Sensor_El_DT = 34
    DT_Sensor_Samp_Coord_Des_DT = 35
    DT_Sensor_Samp_Timing_Des_DT = 36
    DT_Sensor_Compression_DT = 37
    DT_JPEG_Sensor_Quant_DT = 38
    DT_JPEG_Sensor_Huffman_DT = 39
    DT_RADAR_Sensor_Des_DT = 40
    DT_RADAR_Collect_Plane_ImGeo_DT = 41
    DT_Reference_Track_DT = 42
    DT_Rectified_ImGeo_DT = 43
    DT_Virtual_Sensor_Def_DT = 44
    DT_RADAR_Parameters_DT = 45
    DT_ISAR_Track_DT = 46
    DT_RADAR_Element_DT = 47
    DT_Sensor_DT = 48
    DT_Sensor_Samp_xCoord_DT = 49
    DT_Sensor_Samp_yCoord_DT = 50
    DT_Sensor_Samp_zCoord_DT = 51
    DT_Sensor_Samp_Timing_DT = 52
    DT_4607_GMTI_DT = 53
    DT_4609_Motion_Imagery_DT = 54
    DT_Range_Finder_DT = 55
    DT_Reserved_DT = 56
    DT_UNRECOGNISED_SA_DT = 57
    DT_UNRECOGNISED_DFA_DT = 58
    DT_JPEG2000_Des_DT = 59
    DT_JPEG2000_Index_DT = 60
    DT_BAD_DT = 61  # Generic Bad table entry

    # Data: tuple containing all 7023 valid tables except the User defined table
    ALL_VALID_TABLES_EXCEPT_USER_DEFINED = (
        DT_Format_Time_Tag_DT, DT_General_Admin_Ref_DT, DT_Mission_Security_DT,
        DT_Air_Tasking_Order_DT, DT_Collection_Plat_ID_DT, DT_Requester_DT,
        DT_Requester_Remarks_DT, DT_General_Tgt_Info_DT, DT_General_Tgt_Loc_DT,
        DT_General_Tgt_EEI_DT, DT_General_Tgt_Remarks_DT,
        DT_Min_Dynamic_Plat_DT, DT_Comp_Dynamic_Plat_DT, DT_Sensor_Grouping_DT,
        DT_End_Record_Marker_DT, DT_End_Segment_Marker_DT, DT_Event_Marker_DT,
        DT_Segment_Index_DT, DT_Event_Index_DT, DT_Sensor_ID_DT,
        DT_PASSIVE_Sensor_Des_DT, DT_Sensor_Calibration_DT,
        DT_Sync_Hier_and_ImBld_DT, DT_Sensor_Data_Timing_DT,
        DT_Sensor_Op_Status_DT, DT_Sensor_Position_DT, DT_Min_Sensor_Att_DT,
        DT_Comp_Sensor_Att_DT, DT_Gimbals_Position_DT, DT_Min_Gimbals_Att_DT,
        DT_Comp_Gimbals_Att_DT, DT_Sensor_Index_DT, DT_Passive_Sensor_El_DT,
        DT_Sensor_Samp_Coord_Des_DT, DT_Sensor_Samp_Timing_Des_DT,
        DT_Sensor_Compression_DT, DT_JPEG_Sensor_Quant_DT,
        DT_JPEG_Sensor_Huffman_DT, DT_RADAR_Sensor_Des_DT,
        DT_RADAR_Collect_Plane_ImGeo_DT, DT_Reference_Track_DT,
        DT_Rectified_ImGeo_DT, DT_Virtual_Sensor_Def_DT, DT_RADAR_Parameters_DT,
        DT_ISAR_Track_DT, DT_RADAR_Element_DT, DT_Sensor_DT,
        DT_Sensor_Samp_xCoord_DT, DT_Sensor_Samp_yCoord_DT,
        DT_Sensor_Samp_zCoord_DT, DT_Sensor_Samp_Timing_DT, DT_4607_GMTI_DT,
        DT_4609_Motion_Imagery_DT, DT_Range_Finder_DT, DT_JPEG2000_Des_DT,
        DT_JPEG2000_Index_DT
    )

    # Data: tuple containing all valid 7023 data tables
    S7023_ALL_VALID_TABLES = (
        ALL_VALID_TABLES_EXCEPT_USER_DEFINED + (DT_User_Defined_DT,)
    )

    # Data: tuple containing all invalid defined tables
    S7023_INVALID_DEFINED_TABLES = (
        DT_Reserved_DT,
        DT_UNRECOGNISED_SA_DT,
        DT_UNRECOGNISED_DFA_DT,
        DT_BAD_DT
    )

    #Data: tuple containing all Defined tables
    S7023_DEFINED_TABLES = (
        S7023_ALL_VALID_TABLES + S7023_INVALID_DEFINED_TABLES
    )

    # Data: tuple containing those tables not in Edition 3
    S7023_NOT_ED3 = (
        DT_4607_GMTI_DT,
        DT_4609_Motion_Imagery_DT,
        DT_Range_Finder_DT,
        DT_JPEG2000_Des_DT,
        DT_JPEG2000_Index_DT
    )

    # Data: Various groups of tables from the standard
    S7023_Requester_Index_Tables = ( DT_Requester_DT, DT_Requester_Remarks_DT)
    S7023_Group_ID_Tables = (DT_Sensor_Grouping_DT, )
    S7023_Event_ID_Tables = (DT_Event_Index_DT, )
    S7023_Segment_ID_Tables = (
        DT_Segment_Index_DT,
        DT_Event_Index_DT,
        DT_Sensor_Index_DT)
    S7023_Location_ID_Tables = (
        DT_General_Tgt_Loc_DT,
        DT_General_Tgt_EEI_DT,
        DT_General_Tgt_Remarks_DT)
    S7023_Target_ID_Tables = (
        DT_General_Tgt_Info_DT,
        DT_General_Tgt_Loc_DT,
        DT_General_Tgt_EEI_DT,
        DT_General_Tgt_Remarks_DT)
    S7023_Gimbal_ID_Tables = (
        DT_Gimbals_Position_DT,
        DT_Min_Gimbals_Att_DT,
        DT_Comp_Gimbals_Att_DT)
    S7023_Sensor_ID_Tables = (
        DT_Sensor_ID_DT, DT_Sensor_Calibration_DT,
        DT_Sync_Hier_and_ImBld_DT, DT_Sensor_Op_Status_DT,
        DT_Sensor_Position_DT, DT_Min_Sensor_Att_DT,
        DT_Comp_Sensor_Att_DT, DT_Gimbals_Position_DT,
        DT_Min_Gimbals_Att_DT, DT_Comp_Gimbals_Att_DT,
        DT_Sensor_Data_Timing_DT, DT_Sensor_Compression_DT,
        DT_JPEG2000_Des_DT, DT_PASSIVE_Sensor_Des_DT,
        DT_RADAR_Sensor_Des_DT, DT_Reference_Track_DT,
        DT_Rectified_ImGeo_DT, DT_Virtual_Sensor_Def_DT,
        DT_RADAR_Parameters_DT, DT_ISAR_Track_DT,
        DT_Range_Finder_DT, DT_Passive_Sensor_El_DT,
        DT_JPEG_Sensor_Quant_DT, DT_JPEG_Sensor_Huffman_DT,
        DT_Sensor_Index_DT, DT_Sensor_DT, DT_4607_GMTI_DT,
        DT_RADAR_Collect_Plane_ImGeo_DT, DT_RADAR_Element_DT,
        DT_4609_Motion_Imagery_DT, DT_Sensor_Samp_zCoord_DT,
        DT_Sensor_Samp_yCoord_DT, DT_Sensor_Samp_xCoord_DT,
        DT_Sensor_Samp_Timing_DT, DT_Sensor_Samp_Coord_Des_DT,
        DT_Sensor_Samp_Timing_Des_DT, DT_JPEG2000_Index_DT)
    S7023_Platform_ID_Tables = (
        DT_Sensor_ID_DT,
        DT_Comp_Dynamic_Plat_DT,
        DT_Min_Dynamic_Plat_DT)
    S7023_Dynamic_Plat_Tables = (
        DT_Min_Dynamic_Plat_DT,
        DT_Comp_Dynamic_Plat_DT)

    # Data: Table names
    S7023_TABLE_NAMES = collections.defaultdict (lambda: "Unrecognised Table", {
        DT_Format_Time_Tag_DT: "Format Time Tag",
        DT_General_Admin_Ref_DT: "General Administrative Reference",
        DT_Mission_Security_DT: "Mission Security",
        DT_Air_Tasking_Order_DT: "Air Tasking Order",
        DT_Collection_Plat_ID_DT: "Collection Platform Identification",
        DT_Requester_DT: "Requester",
        DT_Requester_Remarks_DT: "Requester Remarks",
        DT_General_Tgt_Info_DT: "General Target Information",
        DT_General_Tgt_Loc_DT: "General Target Location",
        DT_General_Tgt_EEI_DT: "General Target EEI",
        DT_General_Tgt_Remarks_DT: "General Target Remarks",
        DT_Min_Dynamic_Plat_DT: "Minimum Dynamic Platform",
        DT_Comp_Dynamic_Plat_DT: "Comprehensive Dynamic Platform",
        DT_Sensor_Grouping_DT: "Sensor Grouping",
        DT_End_Record_Marker_DT: "End of Record Marker",
        DT_End_Segment_Marker_DT: "End of Segment Marker",
        DT_Event_Marker_DT: "Event Marker",
        DT_Segment_Index_DT: "Segment Index",
        DT_Event_Index_DT: "Event Index",
        DT_User_Defined_DT: "User Defined",
        DT_Sensor_ID_DT: "Sensor Identification",
        DT_PASSIVE_Sensor_Des_DT: "Passive Sensor Description",
        DT_Sensor_Calibration_DT: "Sensor Calibration",
        DT_Sync_Hier_and_ImBld_DT: "Sync Hierarchy and Image Build",
        DT_Sensor_Data_Timing_DT: "Sensor Data Timing",
        DT_Sensor_Op_Status_DT: "Sensor Operating Status",
        DT_Sensor_Position_DT: "Sensor Position",
        DT_Min_Sensor_Att_DT: "Minimum Sensor Attitude",
        DT_Comp_Sensor_Att_DT: "Comprehensive Sensor Attitude",
        DT_Gimbals_Position_DT: "Gimbals Position Data Table",
        DT_Min_Gimbals_Att_DT: "Minimum Gimbals Attitude",
        DT_Comp_Gimbals_Att_DT: "Comprehensive Gimbals Attitude",
        DT_Sensor_Index_DT: "Sensor Index",
        DT_Passive_Sensor_El_DT: "Passive Sensor Element",
        DT_Sensor_Samp_Coord_Des_DT: "Sensor Sample Coordinate Description",
        DT_Sensor_Samp_Timing_Des_DT: "Sensor Sample Timing Description",
        DT_Sensor_Compression_DT: "Sensor Compression",
        DT_JPEG_Sensor_Quant_DT: "JPEG Sensor Quantisation",
        DT_JPEG_Sensor_Huffman_DT: "JPEG Sensor Huffman",
        DT_RADAR_Sensor_Des_DT: "RADAR Sensor Description",
        DT_RADAR_Collect_Plane_ImGeo_DT: "RADAR Collection Plane Image Geometry",
        DT_Reference_Track_DT: "Reference Track",
        DT_Rectified_ImGeo_DT: "Rectified Image Geometry",
        DT_Virtual_Sensor_Def_DT: "Virtual Sensor Definition",
        DT_RADAR_Parameters_DT: "RADAR Parameters",
        DT_ISAR_Track_DT: "ISAR Track",
        DT_RADAR_Element_DT: "RADAR Element",
        DT_Sensor_DT: "Sensor",
        DT_Sensor_Samp_xCoord_DT: 'Sensor Sample "x" Coordinate',
        DT_Sensor_Samp_yCoord_DT: 'Sensor Sample "y" Coordinate',
        DT_Sensor_Samp_zCoord_DT: 'Sensor Sample "z" Coordinate',
        DT_Sensor_Samp_Timing_DT: "Sensor Sample Timing",
        DT_4607_GMTI_DT: "4607 GMTI",
        DT_4609_Motion_Imagery_DT: "4609 Motion Imagery",
        DT_Range_Finder_DT: "Range Finder",
        DT_Reserved_DT: "Unrecognised Table",
        DT_UNRECOGNISED_SA_DT: "Unrecognised Table",
        DT_UNRECOGNISED_DFA_DT: "Unrecognised Table",
        DT_JPEG2000_Des_DT: "JPEG 2000 Description",
        DT_JPEG2000_Index_DT: "JPEG 2000 Index",
        DT_BAD_DT: "Unrecognised Table"
    })

    # Data: Table size in bytes - Tuple of min and max
    # ignores sync code and packet header
    S7023_TABLE_SIZES = collections.defaultdict (lambda: (0, 0), {
        DT_Format_Time_Tag_DT: (8, 8),
        DT_General_Admin_Ref_DT: (20, 20),
        DT_Mission_Security_DT: (1156, 1156),
        DT_Air_Tasking_Order_DT: (50, 50),
        DT_Collection_Plat_ID_DT: (37, 37),
        DT_Requester_DT: (849, 849),
        DT_Requester_Remarks_DT: (1024, 1024),
        DT_General_Tgt_Info_DT: (130, 130),
        DT_General_Tgt_Loc_DT: (71, 71),
        DT_General_Tgt_EEI_DT: (40, 40),
        DT_General_Tgt_Remarks_DT: (1024, 1024),
        DT_Min_Dynamic_Plat_DT: (107, 107),
        DT_Comp_Dynamic_Plat_DT: (231, 231),
        DT_Sensor_Grouping_DT: (5, 68),
        DT_End_Record_Marker_DT: (8, 8),
        DT_End_Segment_Marker_DT: (8, 8),
        DT_Event_Marker_DT: (6, 6),
        DT_Segment_Index_DT: (80, 80),
        DT_Event_Index_DT: (78, 78),
        DT_User_Defined_DT: (1, DATA_MAXPKTSIZE),
        DT_Sensor_ID_DT: (35, 35),
        DT_PASSIVE_Sensor_Des_DT: (61, 61),
        DT_Sensor_Calibration_DT: (99, 99),
        DT_Sync_Hier_and_ImBld_DT: (8, 8),
        DT_Sensor_Data_Timing_DT: (32, 32),
        DT_Sensor_Op_Status_DT: (256, 256),
        DT_Sensor_Position_DT: (24, 24),
        DT_Min_Sensor_Att_DT: (24, 24),
        DT_Comp_Sensor_Att_DT: (72, 72),
        DT_Gimbals_Position_DT: (24, 24),
        DT_Min_Gimbals_Att_DT: (24, 24),
        DT_Comp_Gimbals_Att_DT: (72, 72),
        DT_Sensor_Index_DT: (80, 4294967280),
            # from max num of 80 byte chunks that fit in DATA_MAXPKTSIZE
        DT_Passive_Sensor_El_DT: (21, 1344000),
        DT_Sensor_Samp_Coord_Des_DT: (7, 384001),
        DT_Sensor_Samp_Timing_Des_DT: (3, 64002),
        DT_Sensor_Compression_DT: (1, 1),
        DT_JPEG_Sensor_Quant_DT: (69, 520),
        DT_JPEG_Sensor_Huffman_DT: (33, 1108),
        DT_RADAR_Sensor_Des_DT: (29, 29),
        DT_RADAR_Collect_Plane_ImGeo_DT: (33, 33),
        DT_Reference_Track_DT: (72, 72),
        DT_Rectified_ImGeo_DT: (226, 226),
        DT_Virtual_Sensor_Def_DT: (25, 25),
        DT_RADAR_Parameters_DT: (122, 122),
        DT_ISAR_Track_DT: (23, 23),
        DT_RADAR_Element_DT: (83, 5312000),
        DT_Sensor_DT: (1, DATA_MAXPKTSIZE),
        DT_Sensor_Samp_xCoord_DT: (1, DATA_MAXPKTSIZE),
        DT_Sensor_Samp_yCoord_DT: (1, DATA_MAXPKTSIZE),
        DT_Sensor_Samp_zCoord_DT: (1, DATA_MAXPKTSIZE),
        DT_Sensor_Samp_Timing_DT: (1, DATA_MAXPKTSIZE),
        DT_4607_GMTI_DT: (1, DATA_MAXPKTSIZE),
        DT_4609_Motion_Imagery_DT: (1, DATA_MAXPKTSIZE),
        DT_Range_Finder_DT: (8, 8),
        DT_Reserved_DT: (0, 0),
        DT_UNRECOGNISED_SA_DT: (0, 0),
        DT_UNRECOGNISED_DFA_DT: (0, 0),
        DT_JPEG2000_Des_DT: (9, 9),
        DT_JPEG2000_Index_DT: (4, 262140),
            # quality levels * 4 (n quality > n components > n resolution)
        DT_BAD_DT: (0, 0)
    })

    # Data: Field lengths (in bytes) for each given table
    # NB things marked as 8+8 are coordinates
    # A "v" means this list has variable length - code will need to work these
    # out based on the data packet
    S7023_FLD_LENGTHS = collections.defaultdict (lambda: (), {
        DT_Format_Time_Tag_DT: (8, ),
        DT_General_Admin_Ref_DT: (8, 8, 2, 1, 1),
        DT_Mission_Security_DT: (64, 8, 60, 1024),
        DT_Air_Tasking_Order_DT: (7, 20, 10, 8, 3, 2),
        DT_Collection_Plat_ID_DT: (6, 4, 16, 6, 2, 3),
        DT_Requester_DT: (
            1, 16, 16, 8, 6, 1, 512, 1, 48, 48, 48, 48, 48, 48),
        DT_Requester_Remarks_DT: (1024, ),
        DT_General_Tgt_Info_DT: (1, 1, 16, 64, 8, 1, 1, 1, 1, 4, 32),
        DT_General_Tgt_Loc_DT: (8 + 8, 8, 8, 8, 14, 8, 1, 8),
        DT_General_Tgt_EEI_DT: (32, 1, 7),
        DT_General_Tgt_Remarks_DT: (1024, ),
        DT_Min_Dynamic_Plat_DT: (
            8, 8 + 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 3),
        DT_Comp_Dynamic_Plat_DT: (
            8, 8 + 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8,
            8, 8, 8, 8, 8, 8, 7),
        DT_Sensor_Grouping_DT: ('v', 1, 1, 1, 1, 1),
        DT_End_Record_Marker_DT: (8, ),
        DT_End_Segment_Marker_DT: (8, ),
        DT_Event_Marker_DT: (1, 1, 1, 1, 1, 1),
        DT_Segment_Index_DT: (8, 8, 8, 8, 8, 8, 8 + 8, 8 + 8),
        DT_Event_Index_DT: (1, 1, 1, 8, 8, 8 + 8, 1, 1, 1, 8, 32),
        DT_User_Defined_DT: ('v', ),
        DT_Sensor_ID_DT: (1, 16, 16, 1, 1),
        DT_PASSIVE_Sensor_Des_DT: (
            4, 8, 4, 4, 4, 4, 4, 4, 1, 2, 2, 1, 8, 8, 1, 1, 1),
        DT_Sensor_Calibration_DT: (8, 91),
        DT_Sync_Hier_and_ImBld_DT: (1, 1, 1, 1, 1, 1, 1, 1),
        DT_Sensor_Data_Timing_DT: (8, 8, 8, 8),
        DT_Sensor_Op_Status_DT: (256, ),
        DT_Sensor_Position_DT: (8, 8, 8),
        DT_Min_Sensor_Att_DT: (8, 8, 8),
        DT_Comp_Sensor_Att_DT: (8, 8, 8, 8, 8, 8, 8, 8, 8),
        DT_Gimbals_Position_DT: (8, 8, 8),
        DT_Min_Gimbals_Att_DT: (8, 8, 8),
        DT_Comp_Gimbals_Att_DT: (8, 8, 8, 8, 8, 8, 8, 8, 8),
        DT_Sensor_Index_DT: ('v', 8, 8, 8, 8, 8 + 8, 8 + 8, 8, 8),
        DT_Passive_Sensor_El_DT: ('v', 1, 2, 2, 8, 8),
        DT_Sensor_Samp_Coord_Des_DT: ('v', 1, 1, 1, 1, 1, 1, 1),
        DT_Sensor_Samp_Timing_Des_DT: ('v', 1, 1, 1),
        DT_Sensor_Compression_DT: (1, ),
        DT_JPEG_Sensor_Quant_DT: ('v', 2, 2, 1),
        DT_JPEG_Sensor_Huffman_DT: ('v', 2, 2, 1, 16),
        DT_RADAR_Sensor_Des_DT: (4, 4, 4, 4, 4, 1, 1, 1, 2, 2, 1, 1),
        DT_RADAR_Collect_Plane_ImGeo_DT: (8, 8, 8, 8, 1),
        DT_Reference_Track_DT: (8 + 8, 8, 8, 8, 8, 8, 8, 8),
        DT_Rectified_ImGeo_DT: (
            8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8,
            8, 8, 8, 8, 8, 8, 1, 1),
        DT_Virtual_Sensor_Def_DT: (8, 8, 2, 2, 2, 2, 1),
        DT_RADAR_Parameters_DT: (
            8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 2, 2, 2, 2, 1, 1, 1, 1,
            1, 1, 1, 1, 1, 1),
        DT_ISAR_Track_DT: (8, 8, 4, 1, 1, 1),
        DT_RADAR_Element_DT: (
            'v', 1, 2, 2, 1, 2, 8, 8, 8, 8, 8, 8, 8, 8, 8, 1, 1, 1),
        DT_Sensor_DT: ('v', ),
        DT_Sensor_Samp_xCoord_DT: ('v', ),
        DT_Sensor_Samp_yCoord_DT: ('v', ),
        DT_Sensor_Samp_zCoord_DT: ('v', ),
        DT_Sensor_Samp_Timing_DT: ('v', ),
        DT_4607_GMTI_DT: ('v', ),
        DT_4609_Motion_Imagery_DT: ('v', ),
        DT_Range_Finder_DT: (8, ),
        DT_Reserved_DT: (),
        DT_UNRECOGNISED_SA_DT: (),
        DT_UNRECOGNISED_DFA_DT: (),
        DT_JPEG2000_Des_DT: (1, 1, 1, 2, 2, 1, 1),
        DT_JPEG2000_Index_DT: ('v', 4),
        DT_BAD_DT: ()
    })

    # Data: Data Types for each field in a table
    S7023_FLD_TYPES = collections.defaultdict (lambda: (), {
        DT_Format_Time_Tag_DT: ('r',),
        DT_General_Admin_Ref_DT: ('a', 'd', 'a', 'j', 'i'),
        DT_Mission_Security_DT: ('a', 'd', 'a', 'a'),
        DT_Air_Tasking_Order_DT: ('a', 'a', 'a', 'd', 'a', 'i'),
        DT_Collection_Plat_ID_DT: ('a', 'a', 'a', 'a', 'i', 'a'),
        DT_Requester_DT: (
            'e', 'a', 'a', 'd', 'a', 'e', 'a', 'e', 'a', 'a', 'a', 'a',
            'a', 'a'),
        DT_Requester_Remarks_DT: ('a',),
        DT_General_Tgt_Info_DT: (
            'e', 'e', 'a', 'a', 'd', 'e', 'e', 'e', 'i', 'b', 'a'),
        DT_General_Tgt_Loc_DT: ('c', 'r', 'r', 'a', 'a', 'r', 'i', 'd'),
        DT_General_Tgt_EEI_DT: ('a', 'e', 'a'),
        DT_General_Tgt_Remarks_DT: ('a',),
        DT_Min_Dynamic_Plat_DT: ('d', 'c') + ('r',) * 10 + ('q',),
        DT_Comp_Dynamic_Plat_DT: ('d', 'c') + ('r',) * 25 + ('q',),
        DT_Sensor_Grouping_DT: ('e', 'i', 'e', 'e', 'i'),
        DT_End_Record_Marker_DT: ('i',),
        DT_End_Segment_Marker_DT: ('i',),
        DT_Event_Marker_DT: ('j', 'e', 'i', 'i', 'i', 'i'),
        DT_Segment_Index_DT: ('i', 'i', 'd', 'd', 'i', 'i', 'c', 'c'),
        DT_Event_Index_DT: ('e',) + ('i',) * 3 + ('d', 'c') + ('i',) * 4 + ('a',),
        DT_User_Defined_DT: (),
        DT_Sensor_ID_DT: ('e', 'a', 'a', 'e', 'i'),
        DT_PASSIVE_Sensor_Des_DT: (
            'i', 'r', 'i', 'i', 'i', 'i', 'i', 'i', 'e', 'i', 'i', 'e', 'r',
            'r', 'i', 'e', 'e'),
        DT_Sensor_Calibration_DT: ('d', 'a'),
        DT_Sync_Hier_and_ImBld_DT: ('i',) * 6 + ('e', 'e'),
        DT_Sensor_Data_Timing_DT: ('r',) * 4,
        DT_Sensor_Op_Status_DT: ('a',),
        DT_Sensor_Position_DT: ('r',) * 3,
        DT_Min_Sensor_Att_DT: ('r',) * 3,
        DT_Comp_Sensor_Att_DT: ('r',) * 9,
        DT_Gimbals_Position_DT: ('r',) * 3,
        DT_Min_Gimbals_Att_DT: ('r',) * 3,
        DT_Comp_Gimbals_Att_DT: ('r',) * 9,
        DT_Sensor_Index_DT: ('d', 'd', 'i', 'i', 'c', 'c', 'i', 'i'),
        DT_Passive_Sensor_El_DT: ('i', 'i', 'i', 'r', 'r'),
        DT_Sensor_Samp_Coord_Des_DT: ('e', 'j', 'e', 'j', 'e', 'j', 'e'),
        DT_Sensor_Samp_Timing_Des_DT: ('e',) * 3,
        DT_Sensor_Compression_DT: ('e',),
        DT_JPEG_Sensor_Quant_DT: ('h', 'i', 'e', 'x'),
        DT_JPEG_Sensor_Huffman_DT: ('h', 'i', 'e', 'q', 'x'),
        DT_RADAR_Sensor_Des_DT: ('i',) * 5 + ('e',) * 3 + ('i', 'i', 'e', 'e'),
        DT_RADAR_Collect_Plane_ImGeo_DT: ('r', 'r', 'r', 'r', 'e'),
        DT_Reference_Track_DT: ('c',) + ('r',) * 7,
        DT_Rectified_ImGeo_DT: ('r',) * 28 + ('e', 'e'),
        DT_Virtual_Sensor_Def_DT: ('r', 'r', 'i', 'i', 'i', 'i', 'e'),
        DT_RADAR_Parameters_DT: ('r',) * 13 + ('e',) + ('i',) * 4 + ('e',) * 9,
        DT_ISAR_Track_DT: ('r', 'r', 'i', 'e', 'e', 'e'),
        DT_RADAR_Element_DT: ('i',) * 3 + ('e',) * 2 + ('r',) * 9 + ('e',) * 3,
        DT_Sensor_DT: ('x',),
        DT_Sensor_Samp_xCoord_DT: ('x',),
        DT_Sensor_Samp_yCoord_DT: ('x',),
        DT_Sensor_Samp_zCoord_DT: ('x',),
        DT_Sensor_Samp_Timing_DT: ('x',),
        DT_4607_GMTI_DT: ('x',),
        DT_4609_Motion_Imagery_DT: ('x',),
        DT_Range_Finder_DT: ('r',),
        DT_Reserved_DT: (),
        DT_UNRECOGNISED_SA_DT: (),
        DT_UNRECOGNISED_DFA_DT: (),
        DT_JPEG2000_Des_DT: ('e', 'e', 'i', 'j', 'i', 'e', 'e'),
        DT_JPEG2000_Index_DT: ('i',),
        DT_BAD_DT: ()
    })

    # Data: Field Requirements - whether each field is Mandatory, Conditional
    # or Optional
    S7023_FLD_REQS = collections.defaultdict (lambda: (), {
        DT_Format_Time_Tag_DT: ('m',),
        DT_General_Admin_Ref_DT: ('m', 'm', 'o', 'm', 'm'),
        DT_Mission_Security_DT: ('m', 'o', 'o', 'o'),
        DT_Air_Tasking_Order_DT: ('m', 'm', 'o', 'o', 'o', 'o'),
        DT_Collection_Plat_ID_DT: ('o', 'o', 'o', 'o', 'm', 'o'),
        DT_Requester_DT: ('m',) * 8 + ('o',) * 6,
        DT_Requester_Remarks_DT: ('m',),
        DT_General_Tgt_Info_DT: ('m', 'm') + ('o',) * 6 + ('m', 'm', 'o'),
        DT_General_Tgt_Loc_DT: ('m',) + ('o',) * 7,
        DT_General_Tgt_EEI_DT: ('m', 'm', 'o'),
        DT_General_Tgt_Remarks_DT: ('m',),
        DT_Min_Dynamic_Plat_DT: (
            ('m', 'm') + ('c',) * 6 + ('m', 'm', 'm', 'c', 'm')),
        DT_Comp_Dynamic_Plat_DT: (
            ('m', 'm') + ('c',) * 6 + ('m', 'm', 'm', 'c') + ('o',) * 15 +
            ('m',)),
        DT_Sensor_Grouping_DT: ('m',) * 5,
        DT_End_Record_Marker_DT: ('m',),
        DT_End_Segment_Marker_DT: ('m',),
        DT_Event_Marker_DT: ('m', 'm', 'm', 'o', 'o', 'o'),
        DT_Segment_Index_DT: ('m',) * 8,
        DT_Event_Index_DT: (
            'm', 'c', 'c', 'm', 'o', 'o', 'm', 'o', 'o', 'm', 'o'),
        DT_User_Defined_DT: (),
        DT_Sensor_ID_DT: ('m', 'o', 'o', 'm', 'm'),
        DT_PASSIVE_Sensor_Des_DT: ('m',) * 17,
        DT_Sensor_Calibration_DT: ('m', 'm'),
        DT_Sync_Hier_and_ImBld_DT: ('m',) * 6 + ('o', 'o'),
        DT_Sensor_Data_Timing_DT: ('o',) * 4,
        DT_Sensor_Op_Status_DT: ('m',),
        DT_Sensor_Position_DT: ('m',) * 3,
        DT_Min_Sensor_Att_DT: ('m',) * 3,
        DT_Comp_Sensor_Att_DT: ('m',) * 9,
        DT_Gimbals_Position_DT: ('m',) * 3,
        DT_Min_Gimbals_Att_DT: ('m',) * 3,
        DT_Comp_Gimbals_Att_DT: ('m',) * 9,
        DT_Sensor_Index_DT: ('m',) * 8,
        DT_Passive_Sensor_El_DT: ('m',) * 5,
        DT_Sensor_Samp_Coord_Des_DT: ('m',) * 7,
        DT_Sensor_Samp_Timing_Des_DT: ('m',) * 3,
        DT_Sensor_Compression_DT: ('m',),
        DT_JPEG_Sensor_Quant_DT: ('m',) * 4,
        DT_JPEG_Sensor_Huffman_DT: ('m',) * 5,
        DT_RADAR_Sensor_Des_DT: ('m',) * 11 + ('c',),
        DT_RADAR_Collect_Plane_ImGeo_DT: ('m',) * 5,
        DT_Reference_Track_DT: ('m', 'c', 'c', 'c', 'm', 'm', 'm', 'o'),
        DT_Rectified_ImGeo_DT: ('m',) * 6 + ('c',) * 20 + ('m',) * 4,
        DT_Virtual_Sensor_Def_DT: ('m', 'o', 'm', 'm', 'm', 'm', 'm'),
        DT_RADAR_Parameters_DT: ('o',) * 13 + ('m',) + ('o',) * 13,
        DT_ISAR_Track_DT: ('m', 'm', 'o', 'c', 'm', 'm'),
        DT_RADAR_Element_DT: (
            ('m',) * 5 + ('o',) * 5 + ('m',) * 4 + ('o', 'm', 'm')),
        DT_Sensor_DT: ('m',),
        DT_Sensor_Samp_xCoord_DT: ('m',),
        DT_Sensor_Samp_yCoord_DT: ('m',),
        DT_Sensor_Samp_zCoord_DT: ('m',),
        DT_Sensor_Samp_Timing_DT: ('m',),
        DT_4607_GMTI_DT: ('m',),
        DT_4609_Motion_Imagery_DT: ('m',),
        DT_Range_Finder_DT: ('m',),
        DT_Reserved_DT: (),
        DT_UNRECOGNISED_SA_DT: (),
        DT_UNRECOGNISED_DFA_DT: (),
        DT_JPEG2000_Des_DT: ('m', 'm', 'm', 'm', 'm', 'm', 'o'),
        DT_JPEG2000_Index_DT: ('m',),
        DT_BAD_DT: ()
    })

    # Data: Names of the fields in each of the given tables (in order)
    S7023_FLD_NAMES = collections.defaultdict (lambda: (), {
        DT_Format_Time_Tag_DT: ('Tick Value',),
        DT_General_Admin_Ref_DT: (
            'Mission Number', 'Mission Start Time', 'Project Identifier Code',
            'Number of Targets', 'Number of Requesters'),
        DT_Mission_Security_DT: (
            'Mission Security Classification', 'Date', 'Authority',
            'Downgrading Instructions'),
        DT_Air_Tasking_Order_DT: (
            'Air Tasking Order Title', 'Air Tasking Order Originator',
            'Air Tasking Order Serial Number', 'Date Time Group', 'Qualifier',
            'Qualifier Serial Number'),
        DT_Collection_Plat_ID_DT: (
            'Squadron', 'Wing', 'Aircraft Type', 'Aircraft Tail Number',
            'Sortie Number', 'Pilot ID'),
        DT_Requester_DT: (
            'Report Message Type', 'Message Communications Channel',
            'Secondary Imagery Dissemination Channel',
            'Latest Time of Intelligence Value', 'Requester Serial Number',
            'Mission Priority', 'Requester Address', 'Requester Type',
            'Operation Codeword', 'Operation Plan Originator & Number',
            'Operation Option Name - Primary',
            'Operation Option Name - Secondary', 'Exercise Nickname',
            'Message Additional Identifier'),
        DT_Requester_Remarks_DT: ('Remarks',),
        DT_General_Tgt_Info_DT: (
            'Target Type', 'Target Priority',
            'Basic Encyclopaedia (BE) Number',
            'Target Security Classification', 'Required Time on Target',
            'Requested Sensor Type', 'Requested Sensor Response Band',
            'Requested Collection Technique', 'Number of Locations',
            'Requester Address Index', 'Target Name'),
        DT_General_Tgt_Loc_DT: (
            'Start_ Target or Corner Location',
            'Start_ Target or Corner Elevation', 'Target Diameter or Width',
            'Map Series', 'Sheet Number of Target Location',
            'Inverse Map Scale', 'Map Edition Number', 'Map Edition Date'),
        DT_General_Tgt_EEI_DT: (
            'Target Category/Essential Elements of Information',
            'EEI/Target Category Designation Scheme',
            'Weather Over the Target Reporting Code'),
        DT_General_Tgt_Remarks_DT: ('Remarks',),
        DT_Min_Dynamic_Plat_DT: (
            'Platform Time', 'Platform Geo-Location', 'MSL Altitude',
            'AGL Altitude', 'GPS Altitude', 'Platform true airspeed',
            'Platform ground speed', 'Platform true Course',
            'Platform true Heading', 'Platform Pitch', 'Platform Roll',
            'Platform Yaw', 'Navigational Confidence'),
        DT_Comp_Dynamic_Plat_DT: (
            'Platform Time', 'Platform Geo-Location', 'MSL Altitude',
            'AGL Altitude', 'GPS Altitude', 'Platform true airspeed',
            'Platform ground speed', 'Platform true Course',
            'Platform true Heading', 'Platform Pitch', 'Platform Roll',
            'Platform Yaw', 'Platform Velocity North',
            'Platform Velocity East', 'Platform Velocity Down',
            'Platform Acceleration North', 'Platform Acceleration East',
            'Platform Acceleration Down', 'Platform Heading Rate',
            'Platform Pitch Rate', 'Platform Roll Rate', 'Platform Yaw Rate',
            'Platform Heading angular Acceleration',
            'Platform Pitch angular Acceleration',
            'Platform Roll angular Acceleration',
            'Platform Yaw angular Acceleration', 'V/H',
            'Navigational Confidence'),
        DT_Sensor_Grouping_DT: (
            'Group type', 'Number of sensor numbers within the Group',
            'Coverage relationship', 'Timing relationship', 'Sensor number'),
        DT_End_Record_Marker_DT: ('Size of record',),
        DT_End_Segment_Marker_DT: ('Size of segment',),
        DT_Event_Marker_DT: (
            'Event Number', 'Event Type', 'Primary Sensor Number',
            'Secondary Sensor Number', 'Third Sensor Number', 'Target number'),
        DT_Segment_Index_DT: (
            'Start of data segment', 'End of data segment',
            'Start time of recording', 'Stop time of recording',
            'Start of Header Time Tag', 'End of Header Time Tag',
            'Aircraft location at the start of recording of the segment',
            'Aircraft location at the end of recording of the segment'),
        DT_Event_Index_DT: (
            'Event Type', 'Target Number', 'Target Sub-section', 'Time Tag',
            'Event Time', 'Aircraft Geo-Location', 'Primary Sensor Number',
            'Secondary Sensor Number', 'Third Sensor Number',
            'Event position in the record', 'Event Name'),
        DT_User_Defined_DT: (),
        DT_Sensor_ID_DT: (
            'Sensor Type', 'Sensor Serial Number', 'Sensor Model Number',
            'Sensor Modelling Method', 'Number of Gimbals'),
        DT_PASSIVE_Sensor_Des_DT: (
            'Frame or Swath size', 'Active Line time',
            'Line size of active data', 'Packets per Frame or Swath',
            'Size of tile in the high frequency scanning direction',
            'Size of tile in the low frequency scanning direction',
            'Number of tiles across a line', 'Number of swaths per frame',
            'Sensor mode', 'Pixel size', 'Elements per pixel', 'Data Ordering',
            'Line FOV', 'Frame or Swath FOV', 'Number of Fields',
            'High frequency scanning direction',
            'Low frequency scanning direction'),
        DT_Sensor_Calibration_DT: (
            'Calibration date', 'Calibration Agency'),
        DT_Sync_Hier_and_ImBld_DT: (
            'SUPER FRAME hierarchy', 'FRAME hierarchy', 'FIELD hierarchy',
            'SWATH hierarchy', 'TILE hierarchy', 'LINE hierarchy',
            'Build direction of TILE image components',
            'Frame Coverage Relationship'),
        DT_Sensor_Data_Timing_DT: (
            'Frame period', 'Intra Frame Time', 'Line period',
            'Intra Line time'),
        DT_Sensor_Op_Status_DT: ('Status',),
        DT_Sensor_Position_DT: (
            'X vector component', 'Y vector component', 'Z vector component'),
        DT_Min_Sensor_Att_DT: (
            'Rotation about Z-axis', 'Rotation about Y-axis',
            'Rotation about X-axis'),
        DT_Comp_Sensor_Att_DT: (
            'Rotation about Z-axis', 'Rotation about Y-axis',
            'Rotation about X-axis', 'Rotation rate about Z-axis',
            'Rotation rate about Y-axis', 'Rotation rate about X-axis',
            'Rotation acceleration about Z-axis',
            'Rotation acceleration about Y-axis',
            'Rotation acceleration about X-axis'),
        DT_Gimbals_Position_DT: (
            'X vector component', 'Y vector component', 'Z vector component'),
        DT_Min_Gimbals_Att_DT: (
            'Rotation about Z-axis', 'Rotation about Y-axis',
            'Rotation about X-axis'),
        DT_Comp_Gimbals_Att_DT: (
            'Rotation about Z-axis', 'Rotation about Y-axis',
            'Rotation about X-axis', 'Rotation rate about Z-axis',
            'Rotation rate about Y-axis', 'Rotation rate about X-axis',
            'Rotation acceleration about Z-axis',
            'Rotation acceleration about Y-axis',
            'Rotation acceleration about X-axis'),
        DT_Sensor_Index_DT: (
            'Collection Start Time', 'Collection Stop Time',
            'Start Header Time Tag', 'End Header Time Tag',
            'Aircraft location at Collection Start Time',
            'Aircraft location at Collection End Time',
            'Sensor Start Position', 'Sensor End Position'),
        DT_Passive_Sensor_El_DT: (
            'Element size', 'Element Bit offset', 'Sensor Element ID',
            'Minimum wavelength', 'Maximum wavelength'),
        DT_Sensor_Samp_Coord_Des_DT: (
            'Vector model', "Size of 'x' vector component",
            "Type of 'x' vector component", "Size of 'y' vector component",
            "Type of 'y' vector component", "Size of 'z' vector component",
            "Type of 'z' vector component"),
        DT_Sensor_Samp_Timing_Des_DT: (
            'Timing model', 'Timing accuracy', 'Timing method'),
        DT_Sensor_Compression_DT: ('Compression algorithm',),
        DT_JPEG_Sensor_Quant_DT: (
            'DQT Define Quantisation Table Marker', 'Lq Length of parameters',
            'PqTq Quantisation table element precision',
            'Qk Quantisation table elements in zigzag order'),
        DT_JPEG_Sensor_Huffman_DT: (
            'DHT Define Huffman Table marker', 'Lh Length of parameters',
            'TcTh Huffman Table Class and Table Identifier',
            'L1 Number of codes in each length', 'Vij Huffman Code Values'),
        DT_RADAR_Sensor_Des_DT: (
            'Image length', 'Image width', 'Packets per image', 'Tile length',
            'Tile width', 'Physical coordinate system',
            'Coordinate System Orientation', 'Sensor mode', 'Pixel size',
            'Elements per pixel', 'Data ordering', 'vld orientation'),
        DT_RADAR_Collect_Plane_ImGeo_DT: (
            'Alpha', 'Virtual distance to the first pixel in the image',
            'Pixel interval in the Virtual Look Direction',
            'Pixel interval in the Cross Virtual Look Direction',
            'Units of measurement for CrossVirtual Look Direction'),
        DT_Reference_Track_DT: (
            'Sensor Virtual Position geo-location',
            'Sensor Virtual Position MSL altitude',
            'Sensor Virtual Position AGL altitude',
            'Sensor Virtual Position GPS altitude',
            'Reference Track north', 'Reference Track east',
            'Reference Track down', 'Reference Track Speed'),
        DT_Rectified_ImGeo_DT: (
            'Axx', 'Axy', 'Ayx', 'Ayy', 'Cx', 'Cy', 'Data 1', 'Data 2',
            'Data 3', 'Data 4', 'Data 5', 'Data 6', 'Data 7', 'Data 8',
            'Data 9', 'Data 10', 'Data 11', 'Data 12', 'Data 13', 'Data 14',
            'Data 15', 'Data 16', 'Data 17', 'Data 18', 'Data 19', 'Data 20',
            'Near Range Point Depression angle',
            'Far Range Point Depression angle', 'Projection type',
            'Terrain model'),
        DT_Virtual_Sensor_Def_DT: (
            'Transmit phase difference', 'Receive phase difference',
            'Transmit antenna 1 Sensor number',
            'Transmit antenna 2 Sensor number',
            'Receive antenna 1 Sensor number',
            'Receive antenna 2 Sensor number', 'Combination operation'),
        DT_RADAR_Parameters_DT: (
            'Processed resolution in vld', 'Processed resolution in cvld',
            'Wavelength', 'Average power', 'Antenna Gain', 'PRF',
            'Radiometric scale factor', 'Aperture Time',
            'Pulse Compression Ratio', 'Azimuth Beamwidth',
            'Interpulse Transmit Bandwidth',
            'Instantaneous Receiver Bandwidth', 'A/D converter sample rate',
            'RADAR mode', 'Processed number of looks', 'Pre-summing in range',
            'Pre-summing in azimuth', 'Number of A/D converter bits',
            'Interpulse modulation type', 'Pulse-to-pulse modulation type',
            'Range compression processing algorithm',
            'Azimuth compression processing algorithm',
            'Autofocus processing algorithms', 'Range processing weighting',
            'Azimuth processing weighting', 'Antenna azimuth weighting',
            'Antenna elevation weighting'),
        DT_ISAR_Track_DT: (
            'Road curvature', 'Radial speed of vehicle', 'Track ID',
            'Track type', 'Direction of road curvature',
            'Direction of vehicle radial velocity'),
        DT_RADAR_Element_DT: (
            'Element size', 'Element Bit offset', 'Sensor Element ID',
            'Type of Element', 'Physical characteristic',
            'RF Centre frequency', 'RF Bandwidth', 'Mean Doppler Frequency',
            'Look Centre Frequency', 'Look Bandwidth', 'Minimum Element Value',
            'Maximum Element Value', 'Minimum Physical Value',
            'Maximum Physical Value', 'Polarisation', 'Use of element',
            'Transfer Function Type'),
        DT_Sensor_DT: ('Sensor data',),
        DT_Sensor_Samp_xCoord_DT: ('Sample "x" coordinate',),
        DT_Sensor_Samp_yCoord_DT: ('Sample "y" coordinate',),
        DT_Sensor_Samp_zCoord_DT: ('Sample "z" coordinate',),
        DT_Sensor_Samp_Timing_DT: ('Sample Timing',),
        DT_4607_GMTI_DT: ('4607 GMTI Data',),
        DT_4609_Motion_Imagery_DT: ('4609 Motion Imagery Data',),
        DT_Range_Finder_DT: ('Range',),
        DT_Reserved_DT: (),
        DT_UNRECOGNISED_SA_DT: (),
        DT_UNRECOGNISED_DFA_DT: (),
        DT_JPEG2000_Des_DT: (
            'Codestream capability', 'Progression order',
            'Number of decomposition levels', 'Number of layers',
            'Number of components', 'JPEG 2000 Tiling performed', 'IREP'),
        DT_JPEG2000_Index_DT: ('Highest order of progression index',),
        DT_BAD_DT: ()
    })

    # Data : Field 'list' Flags - fields flagged with a '1' may have repeating
    # elements. These will be handled as lists.
    S7023_FLD_LIST_FLAGS = collections.defaultdict (lambda: (), {
        DT_Format_Time_Tag_DT: (0,),
        DT_General_Admin_Ref_DT: (0,) * 5,
        DT_Mission_Security_DT: (0,) * 4,
        DT_Air_Tasking_Order_DT: (0,) * 6,
        DT_Collection_Plat_ID_DT: (0,) * 6,
        DT_Requester_DT: (0,) * 14,
        DT_Requester_Remarks_DT: (0,),
        DT_General_Tgt_Info_DT: (0,) * 11,
        DT_General_Tgt_Loc_DT: (0,) * 8,
        DT_General_Tgt_EEI_DT: (0,) * 3,
        DT_General_Tgt_Remarks_DT: (0,),
        DT_Min_Dynamic_Plat_DT: (0,) * 13,
        DT_Comp_Dynamic_Plat_DT: (0,) * 28,
        DT_Sensor_Grouping_DT: (0, 0, 0, 0, 1),
        DT_End_Record_Marker_DT: (0,),
        DT_End_Segment_Marker_DT: (0,),
        DT_Event_Marker_DT: (0,) * 6,
        DT_Segment_Index_DT: (0,) * 8,
        DT_Event_Index_DT: (0,) * 11,
        DT_User_Defined_DT: (),
        DT_Sensor_ID_DT: (0,) * 5,
        DT_PASSIVE_Sensor_Des_DT: (0,) * 17,
        DT_Sensor_Calibration_DT: (0,) * 2,
        DT_Sync_Hier_and_ImBld_DT: (0,) * 8,
        DT_Sensor_Data_Timing_DT: (0,) * 4,
        DT_Sensor_Op_Status_DT: (0,),
        DT_Sensor_Position_DT: (0,) * 3,
        DT_Min_Sensor_Att_DT: (0,) * 3,
        DT_Comp_Sensor_Att_DT: (0,) * 9,
        DT_Gimbals_Position_DT: (0,) * 3,
        DT_Min_Gimbals_Att_DT: (0,) * 3,
        DT_Comp_Gimbals_Att_DT: (0,) * 9,
        DT_Sensor_Index_DT: (1,) * 8,
        DT_Passive_Sensor_El_DT: (1, 1, 1, 1, 1),
        DT_Sensor_Samp_Coord_Des_DT: (0, 1, 1, 1, 1, 1, 1),
        DT_Sensor_Samp_Timing_Des_DT: (0, 0, 1),
        DT_Sensor_Compression_DT: (0,),
        DT_JPEG_Sensor_Quant_DT: (0, 0, 1, 1),
        DT_JPEG_Sensor_Huffman_DT: (0, 0, 1, 1, 1),
        DT_RADAR_Sensor_Des_DT: (0,) * 12,
        DT_RADAR_Collect_Plane_ImGeo_DT: (0,) * 5,
        DT_Reference_Track_DT: (0,) * 8,
        DT_Rectified_ImGeo_DT: (0,) * 30,
        DT_Virtual_Sensor_Def_DT: (0,) * 7,
        DT_RADAR_Parameters_DT: (0,) * 27,
        DT_ISAR_Track_DT: (0,) * 6,
        DT_RADAR_Element_DT: (1,) * 17,
        DT_Sensor_DT: (0,),
        DT_Sensor_Samp_xCoord_DT: (0,),
        DT_Sensor_Samp_yCoord_DT: (0,),
        DT_Sensor_Samp_zCoord_DT: (0,),
        DT_Sensor_Samp_Timing_DT: (0,),
        DT_4607_GMTI_DT: (0,),
        DT_4609_Motion_Imagery_DT: (0,),
        DT_Range_Finder_DT: (0,),
        DT_Reserved_DT: (),
        DT_UNRECOGNISED_SA_DT: (),
        DT_UNRECOGNISED_DFA_DT: (),
        DT_JPEG2000_Des_DT: (0,) * 7,
        DT_JPEG2000_Index_DT: (1,),
        DT_BAD_DT: ()
    })

    # Data: linking tables to a text string containing the variable name
    # not used by the code, but possibly useful for code refactoring
    _VARIABLE_NAMES = collections.defaultdict (lambda: "Not Applicable", {
        DT_Format_Time_Tag_DT: "DT_Format_Time_Tag_DT",
        DT_General_Admin_Ref_DT: "DT_General_Admin_Ref_DT",
        DT_Mission_Security_DT: "DT_Mission_Security_DT",
        DT_Air_Tasking_Order_DT: "DT_Air_Tasking_Order_DT",
        DT_Collection_Plat_ID_DT: "DT_Collection_Plat_ID_DT",
        DT_Requester_DT: "DT_Requester_DT",
        DT_Requester_Remarks_DT: "DT_Requester_Remarks_DT",
        DT_General_Tgt_Info_DT: "DT_General_Tgt_Info_DT",
        DT_General_Tgt_Loc_DT: "DT_General_Tgt_Loc_DT",
        DT_General_Tgt_EEI_DT: "DT_General_Tgt_EEI_DT",
        DT_General_Tgt_Remarks_DT: "DT_General_Tgt_Remarks_DT",
        DT_Min_Dynamic_Plat_DT: "DT_Min_Dynamic_Plat_DT",
        DT_Comp_Dynamic_Plat_DT: "DT_Comp_Dynamic_Plat_DT",
        DT_Sensor_Grouping_DT: "DT_Sensor_Grouping_DT",
        DT_End_Record_Marker_DT: "DT_End_Record_Marker_DT",
        DT_End_Segment_Marker_DT: "DT_End_Segment_Marker_DT",
        DT_Event_Marker_DT: "DT_Event_Marker_DT",
        DT_Segment_Index_DT: "DT_Segment_Index_DT",
        DT_Event_Index_DT: "DT_Event_Index_DT",
        DT_User_Defined_DT: "DT_User_Defined_DT",
        DT_Sensor_ID_DT: "DT_Sensor_ID_DT",
        DT_PASSIVE_Sensor_Des_DT: "DT_PASSIVE_Sensor_Des_DT",
        DT_Sensor_Calibration_DT: "DT_Sensor_Calibration_DT",
        DT_Sync_Hier_and_ImBld_DT: "DT_Sync_Hier_and_ImBld_DT",
        DT_Sensor_Data_Timing_DT: "DT_Sensor_Data_Timing_DT",
        DT_Sensor_Op_Status_DT: "DT_Sensor_Op_Status_DT",
        DT_Sensor_Position_DT: "DT_Sensor_Position_DT",
        DT_Min_Sensor_Att_DT: "DT_Min_Sensor_Att_DT",
        DT_Comp_Sensor_Att_DT: "DT_Comp_Sensor_Att_DT",
        DT_Gimbals_Position_DT: "DT_Gimbals_Position_DT",
        DT_Min_Gimbals_Att_DT: "DT_Min_Gimbals_Att_DT",
        DT_Comp_Gimbals_Att_DT: "DT_Comp_Gimbals_Att_DT",
        DT_Sensor_Index_DT: "DT_Sensor_Index_DT",
        DT_Passive_Sensor_El_DT: "DT_Passive_Sensor_El_DT",
        DT_Sensor_Samp_Coord_Des_DT: "DT_Sensor_Samp_Coord_Des_DT",
        DT_Sensor_Samp_Timing_Des_DT: "DT_Sensor_Samp_Timing_Des_DT",
        DT_Sensor_Compression_DT: "DT_Sensor_Compression_DT",
        DT_JPEG_Sensor_Quant_DT: "DT_JPEG_Sensor_Quant_DT",
        DT_JPEG_Sensor_Huffman_DT: "DT_JPEG_Sensor_Huffman_DT",
        DT_RADAR_Sensor_Des_DT: "DT_RADAR_Sensor_Des_DT",
        DT_RADAR_Collect_Plane_ImGeo_DT: "DT_RADAR_Collect_Plane_ImGeo_DT",
        DT_Reference_Track_DT: "DT_Reference_Track_DT",
        DT_Rectified_ImGeo_DT: "DT_Rectified_ImGeo_DT",
        DT_Virtual_Sensor_Def_DT: "DT_Virtual_Sensor_Def_DT",
        DT_RADAR_Parameters_DT: "DT_RADAR_Parameters_DT",
        DT_ISAR_Track_DT: "DT_ISAR_Track_DT",
        DT_RADAR_Element_DT: "DT_RADAR_Element_DT",
        DT_Sensor_DT: "DT_Sensor_DT",
        DT_Sensor_Samp_xCoord_DT: "DT_Sensor_Samp_xCoord_DT",
        DT_Sensor_Samp_yCoord_DT: "DT_Sensor_Samp_yCoord_DT",
        DT_Sensor_Samp_zCoord_DT: "DT_Sensor_Samp_zCoord_DT",
        DT_Sensor_Samp_Timing_DT: "DT_Sensor_Samp_Timing_DT",
        DT_4607_GMTI_DT: "DT_4607_GMTI_DT",
        DT_4609_Motion_Imagery_DT: "DT_4609_Motion_Imagery_DT",
        DT_Range_Finder_DT: "DT_Range_Finder_DT",
        DT_Reserved_DT: "DT_Reserved_DT",
        DT_UNRECOGNISED_SA_DT: "DT_UNRECOGNISED_SA_DT",
        DT_UNRECOGNISED_DFA_DT: "DT_UNRECOGNISED_DFA_DT",
        DT_JPEG2000_Des_DT: "DT_JPEG2000_Des_DT",
        DT_JPEG2000_Index_DT: "DT_JPEG2000_Index_DT",
        DT_BAD_DT: "DT_BAD_DT"
    })

    # Data: any additional functions which should be run on the data fields
    # 'None' means no additional functions
    S7023_FLD_FUNCS = collections.defaultdict (lambda: (), {
        DT_Format_Time_Tag_DT: (None,),
        DT_General_Admin_Ref_DT: (None,) * 5,
        DT_Mission_Security_DT: (None,) * 4,
        DT_Air_Tasking_Order_DT: (None,) * 6,
        DT_Collection_Plat_ID_DT: (None,) * 6,
        DT_Requester_DT: (
            Lookup_Report_Message_Type, None, None, None, None,
            Lookup_Mission_Priority_Type, None, Lookup_Requester_Type, None,
            None, None, None, None, None),
        DT_Requester_Remarks_DT: (None,),
        DT_General_Tgt_Info_DT: (
            Lookup_Target_Type, Lookup_Mission_Priority_Type, None, None, None,
            Lookup_Req_Sensor_Type, Lookup_Req_Sensor_Resp_Band,
            Lookup_Req_Collect_Tech, None, Conv_bin1ind, None),
        DT_General_Tgt_Loc_DT: (None,) * 8,
        DT_General_Tgt_EEI_DT: (None, Lookup_Tgt_Cat_Desig_Scheme, None),
        DT_General_Tgt_Remarks_DT: (None,),
        DT_Min_Dynamic_Plat_DT: (
            None, None, None, None, None, None, None, Conv_Degrees,
            Conv_Degrees, Conv_Degrees, Conv_Degrees, Conv_Degrees, Conv_nav),
        DT_Comp_Dynamic_Plat_DT: (
            None, None, None, None, None, None, None, Conv_Degrees,
            Conv_Degrees, Conv_Degrees, Conv_Degrees, Conv_Degrees, None, None,
            None, None, None, None, Conv_Degrees_NC, Conv_Degrees_NC,
            Conv_Degrees_NC, Conv_Degrees_NC, Conv_Degrees_NC, Conv_Degrees_NC,
            Conv_Degrees_NC, Conv_Degrees_NC, None, Conv_nav),
        DT_Sensor_Grouping_DT: (
            Lookup_Group_type, None, Lookup_Coverage_Rel,
            Lookup_Timing_relationship, None),
        DT_End_Record_Marker_DT: (None,),
        DT_End_Segment_Marker_DT: (None,),
        DT_Event_Marker_DT: (None, Lookup_Event_Type, None, None, None, None),
        DT_Segment_Index_DT: (None,) * 8,
        DT_Event_Index_DT: (Lookup_Event_Type,) + (None,) * 10,
        DT_User_Defined_DT: (),
        DT_Sensor_ID_DT: (
            Lookup_Sensor_Coding_Type, None, None, Lookup_Sensor_Mod_Meth,
            None),
        DT_PASSIVE_Sensor_Des_DT: (
            None, None, None, None, None, None, None, None,
            Lookup_PassSens_Mode, None, None, Lookup_PassSens_Ordering,
            Conv_Degrees2, Conv_Degrees2, Lookup_Num_Fields,
            Lookup_PassSens_Scan_Dir, Lookup_PassSens_Scan_Dir),
        DT_Sensor_Calibration_DT: (None,) * 2,
        DT_Sync_Hier_and_ImBld_DT: (
            None, None, None, None, None, None, Lookup_Image_Build_Dir,
            Lookup_Coverage_Rel),
        DT_Sensor_Data_Timing_DT: (None,) * 4,
        DT_Sensor_Op_Status_DT: (None,),
        DT_Sensor_Position_DT: (None,) * 3,
        DT_Min_Sensor_Att_DT: (Conv_Degrees3,) * 3,
        DT_Comp_Sensor_Att_DT: (Conv_Degrees3,) * 3 + (Conv_Degrees_NC,) * 6,
        DT_Gimbals_Position_DT: (None,) * 3,
        DT_Min_Gimbals_Att_DT: (Conv_Degrees3,) * 3,
        DT_Comp_Gimbals_Att_DT: (Conv_Degrees3,) * 3 + (Conv_Degrees_NC,) * 6,
        DT_Sensor_Index_DT: (None,) * 8,
        DT_Passive_Sensor_El_DT: (None,) * 5,
        DT_Sensor_Samp_Coord_Des_DT: (
            Lookup_Vect_or_Tim_Mod, None, Lookup_Type_of_Element, None,
            Lookup_Type_of_Element, None, Lookup_Type_of_Element),
        DT_Sensor_Samp_Timing_Des_DT: (
            Lookup_Vect_or_Tim_Mod, Lookup_Timing_accuracy,
            Lookup_Timing_method),
        DT_Sensor_Compression_DT: (Lookup_Comp_Alg,),
        DT_JPEG_Sensor_Quant_DT: (None, None, Conv_JPEG_PqTq, None),
        DT_JPEG_Sensor_Huffman_DT: (
            None, None, Conv_Huff_TcTh, Conv_Hufflengths, None),
        DT_RADAR_Sensor_Des_DT: (
            None, None, None, None, None, Lookup_RAD_Phys_coord_sys,
            Lookup_RAD_Coord_Sys_Orient, Lookup_RAD_Sensor_mode, None, None,
            Lookup_RAD_Data_order, Lookup_RAD_vld_orientation),
        DT_RADAR_Collect_Plane_ImGeo_DT: (
            Conv_Degrees3, None, None, None, Lookup_Unit_Meas_CrossVirt),
        DT_Reference_Track_DT: (None,) * 8,
        DT_Rectified_ImGeo_DT: (
            (None,) * 26 + (Conv_Degrees2,) * 2 +
            (Lookup_Projection_type, Lookup_Terrain_model)),
        DT_Virtual_Sensor_Def_DT: (
            None, None, Conv_notinuse, Conv_notinuse, Conv_notinuse,
            Conv_notinuse, Lookup_Comb_op),
        DT_RADAR_Parameters_DT: (
            (None,) * 9 + (Conv_Degrees2, None, None, None, Lookup_RAD_mode,
            None, None, None, None, Lookup_Interpulse_mod_type,
            Lookup_Pulse_to_pulse_mod, Lookup_Range_comp_proc_alg,
            Lookup_Azimuth_comp_proc, Lookup_Autofocus_proc_alg,
            Lookup_proc_weight, Lookup_proc_weight, Lookup_Antenna_weight,
            Lookup_Antenna_weight)),
        DT_ISAR_Track_DT: (
            None, None, None, Lookup_Track_type, Lookup_Dir_road_curv,
            Lookup_Dir_vehicle_radvel),
        DT_RADAR_Element_DT: (
            (None, None, None, Lookup_Type_of_Element,
            Lookup_Physical_characteristic) + (None,) * 9 +
            (Lookup_Polarisation, Lookup_Use_of_element,
            Lookup_Trans_Func_Type)),
        DT_Sensor_DT: (None,),
        DT_Sensor_Samp_xCoord_DT: (None,),
        DT_Sensor_Samp_yCoord_DT: (None,),
        DT_Sensor_Samp_zCoord_DT: (None,),
        DT_Sensor_Samp_Timing_DT: (None,),
        DT_4607_GMTI_DT: (None,),
        DT_4609_Motion_Imagery_DT: (None,),
        DT_Range_Finder_DT: (None,),
        DT_Reserved_DT: (),
        DT_UNRECOGNISED_SA_DT: (),
        DT_UNRECOGNISED_DFA_DT: (),
        DT_JPEG2000_Des_DT: (
            Lookup_Codestream_cap, Lookup_Prog_order, None, None, None,
            Lookup_JPEG_2000_Tiling, Lookup_JPEG_2000_IREP),
        DT_JPEG2000_Index_DT: (None,),
        DT_BAD_DT: ()
    })

    # text that is used when printing info from tables with repeated elements
    S7023_REP_ELEMENT_TEXT = collections.defaultdict (
        lambda: "Unexpected Elements in table", {
        DT_Passive_Sensor_El_DT: "Elements in table,",
        DT_Sensor_Index_DT: "Sensor Activations in table,",
        DT_RADAR_Element_DT: "Elements in table,",
        DT_Sensor_Samp_Coord_Des_DT: "Number of Elements in table,",
        DT_Sensor_Samp_Timing_Des_DT: "Number of Elements in table,",
        DT_JPEG2000_Index_DT: "Number of Elements in table,",
        DT_Sensor_Grouping_DT: "Number of Sensors listed in table,",
        DT_JPEG_Sensor_Quant_DT: "Number of Tables (max 4),",
        DT_JPEG_Sensor_Huffman_DT: "Number of Tables (max 8),"
    })
    ###################################################################################

class Tabledata(NPIF):
    """
    Creates a class capable of converting, extracting and manupulating
    individual NPIF tables.
    """

    def __init__(self):
        """
        Creates a NPIF_Header and NPIF_DataContent attributes within the class.
        """
        self.hdr = NPIF_Header()
        self.tdat = NPIF_DataContent()

    def SplitFields(self, buff, flist, crcflag):
        """
        Split the string, buff, into a list of strings with element lengths
        determined by the values in the list, flist. crcflag is needed as NPIF
        tables may optionally have a 2 byte crc at the end, and this flag
        indicates its presence - if present, an additional 2 byte sting will be
        added to the output list.
        Returns an empty list if total of flist elements (plus crc bit if
        appropriate) is greater than length of buff.
        """
        # buff is in binary, flist is in bytes, -
        # check that buff is big enough, adding in crc size if appropriate
        nflist = list(flist)
        if crcflag != 0:
            nflist.append(2)
        a = sum(nflist)
        if len(buff) < a:
            # buffer is not long enough. Return empty list.
            nlist = []
        else:
            # create list of end points in buffer and break out
            elist = []
            nlist = []
            last = 0
            for i in nflist:
                elist.append(last + i)
                last = last + i
            start = 0
            for i in elist:
                nlist.append(buff[start:i])
                start = i
        return nlist

    def crc16(self, s):
        """
        Calculate the crc-16 as specified in the standard. Lookup table (and c
        code) derived from pycrc v0.8.1 with the following parameters:
        width 16, poly 0x8005, reflect-in 0, reflect-out 0, xor-in 0, xor-out 0
        Returns a string with uppercase hex values.
        """
        crcValue = 0x0000
        crc16tab = (
            0x0000, 0x8005, 0x800f, 0x000a, 0x801b, 0x001e, 0x0014, 0x8011,
            0x8033, 0x0036, 0x003c, 0x8039, 0x0028, 0x802d, 0x8027, 0x0022,
            0x8063, 0x0066, 0x006c, 0x8069, 0x0078, 0x807d, 0x8077, 0x0072,
            0x0050, 0x8055, 0x805f, 0x005a, 0x804b, 0x004e, 0x0044, 0x8041,
            0x80c3, 0x00c6, 0x00cc, 0x80c9, 0x00d8, 0x80dd, 0x80d7, 0x00d2,
            0x00f0, 0x80f5, 0x80ff, 0x00fa, 0x80eb, 0x00ee, 0x00e4, 0x80e1,
            0x00a0, 0x80a5, 0x80af, 0x00aa, 0x80bb, 0x00be, 0x00b4, 0x80b1,
            0x8093, 0x0096, 0x009c, 0x8099, 0x0088, 0x808d, 0x8087, 0x0082,
            0x8183, 0x0186, 0x018c, 0x8189, 0x0198, 0x819d, 0x8197, 0x0192,
            0x01b0, 0x81b5, 0x81bf, 0x01ba, 0x81ab, 0x01ae, 0x01a4, 0x81a1,
            0x01e0, 0x81e5, 0x81ef, 0x01ea, 0x81fb, 0x01fe, 0x01f4, 0x81f1,
            0x81d3, 0x01d6, 0x01dc, 0x81d9, 0x01c8, 0x81cd, 0x81c7, 0x01c2,
            0x0140, 0x8145, 0x814f, 0x014a, 0x815b, 0x015e, 0x0154, 0x8151,
            0x8173, 0x0176, 0x017c, 0x8179, 0x0168, 0x816d, 0x8167, 0x0162,
            0x8123, 0x0126, 0x012c, 0x8129, 0x0138, 0x813d, 0x8137, 0x0132,
            0x0110, 0x8115, 0x811f, 0x011a, 0x810b, 0x010e, 0x0104, 0x8101,
            0x8303, 0x0306, 0x030c, 0x8309, 0x0318, 0x831d, 0x8317, 0x0312,
            0x0330, 0x8335, 0x833f, 0x033a, 0x832b, 0x032e, 0x0324, 0x8321,
            0x0360, 0x8365, 0x836f, 0x036a, 0x837b, 0x037e, 0x0374, 0x8371,
            0x8353, 0x0356, 0x035c, 0x8359, 0x0348, 0x834d, 0x8347, 0x0342,
            0x03c0, 0x83c5, 0x83cf, 0x03ca, 0x83db, 0x03de, 0x03d4, 0x83d1,
            0x83f3, 0x03f6, 0x03fc, 0x83f9, 0x03e8, 0x83ed, 0x83e7, 0x03e2,
            0x83a3, 0x03a6, 0x03ac, 0x83a9, 0x03b8, 0x83bd, 0x83b7, 0x03b2,
            0x0390, 0x8395, 0x839f, 0x039a, 0x838b, 0x038e, 0x0384, 0x8381,
            0x0280, 0x8285, 0x828f, 0x028a, 0x829b, 0x029e, 0x0294, 0x8291,
            0x82b3, 0x02b6, 0x02bc, 0x82b9, 0x02a8, 0x82ad, 0x82a7, 0x02a2,
            0x82e3, 0x02e6, 0x02ec, 0x82e9, 0x02f8, 0x82fd, 0x82f7, 0x02f2,
            0x02d0, 0x82d5, 0x82df, 0x02da, 0x82cb, 0x02ce, 0x02c4, 0x82c1,
            0x8243, 0x0246, 0x024c, 0x8249, 0x0258, 0x825d, 0x8257, 0x0252,
            0x0270, 0x8275, 0x827f, 0x027a, 0x826b, 0x026e, 0x0264, 0x8261,
            0x0220, 0x8225, 0x822f, 0x022a, 0x823b, 0x023e, 0x0234, 0x8231,
            0x8213, 0x0216, 0x021c, 0x8219, 0x0208, 0x820d, 0x8207, 0x0202)
        for ch in s:
            tbl_idx = ((crcValue >> 8) ^ ch) & 0xff
            crcValue = (crc16tab[tbl_idx] ^ (crcValue << 8)) & 0xffff
        return '%04X' % crcValue

    def fieldlengths(self):
        """
        Returns a list containing each of the field lengths for all fields in
        the table type stored in the NPIF class.
        """
        # returns a list containing each of the field lengths
        if self.tdat.data_flens is not None:
            return self.tdat.data_flens
        tablecode = self.hdr.tablecode
        datasize = self.nocrcdatasize()
        loclist = self.S7023_FLD_LENGTHS[tablecode]
        # now deal with those tables of variable length
        if len(loclist) == 0:
            # dud cases only can't do anything more here
            return loclist
        #
        if loclist[0] == "v":
            loclist2 = loclist[1:]
            # check for the known cases (17 in total), and fix those we can
            if tablecode in [
                    self.DT_Sensor_Grouping_DT,
                    self.DT_Sensor_Samp_Timing_Des_DT]:
                # may contain additional length 1 fields
                tsize = sum(loclist2)
                if datasize > tsize:
                    loclist2 += (1,) * (datasize - tsize)
                loclist = loclist2
            elif tablecode in [
                    self.DT_Sensor_Index_DT,
                    self.DT_Passive_Sensor_El_DT,
                    self.DT_RADAR_Element_DT,
                    self.DT_JPEG2000_Index_DT]:
                # all fields may get repeated a number of times
                tsize = sum(loclist2)
                if datasize > tsize:
                    loclist3 = loclist2 * (datasize // tsize)
                else:
                    loclist3 = loclist2
                loclist = loclist3
            elif tablecode == self.DT_Sensor_Samp_Coord_Des_DT:
                # may repeat all but the 1st element of the pattern
                tsize = sum(loclist2)
                ssize = tsize - loclist2[0]
                loclist3 = (loclist2[0], )
                pat = loclist2[1:]
                if datasize > tsize:
                    loclist3 += pat * ((datasize - loclist2[0]) // ssize)
                else:
                    loclist3 = loclist2
                loclist = loclist3
            elif tablecode == self.DT_JPEG_Sensor_Quant_DT:
                # need to pick through table itself to get lengths
                last = datasize - 2 - 2 - 1
                # lump everything else into the final field
                loclist2 = (2, 2, 1, last)
                loclist = self._JPEG_quant_flengths(loclist2)
            elif tablecode == self.DT_JPEG_Sensor_Huffman_DT:
                # need to pick through table itself to get lengths
                last = datasize - 2 - 2 - 1 - 16
                loclist2 = (2, 2, 1, 16, last)
                loclist = self._JPEG_huff_flengths(loclist2)
            elif tablecode == self.DT_Sensor_DT:
                # variable sized element repeated multiple times
                # key tables
                # 1. Sensor Description Data Table
                # 2. Sync Hierarchy and Image Build Data Table
                # 3. Sensor Element Data Table
                # 4. Sensor Compression Data Table
                # currently just return the whole lot
                loclist = (datasize,)
            elif tablecode in [
                    self.DT_Sensor_Samp_xCoord_DT,
                    self.DT_Sensor_Samp_yCoord_DT,
                    self.DT_Sensor_Samp_zCoord_DT]:
                # variable sized element repeated multiple times
                # Sensor Sample Coordinate Description Data Table sets sizes
                # currently just return the whole lot
                loclist = (datasize, )
            elif tablecode == self.DT_Sensor_Samp_Timing_DT:
                # field has one of two lengths
                # field may be repeated multiple times
                # Sensor Sample Timing Description Data Table sets sizes
                # currently just return the whole lot
                loclist = (datasize, )
            elif tablecode in [
                    self.DT_4607_GMTI_DT,
                    self.DT_4609_Motion_Imagery_DT,
                    self.DT_User_Defined_DT]:
                # variable, and beyond scope of 7023 - treat as the length of
                # the data
                loclist = (datasize, )
            else:
                # if this code is properly self consistent, we should never end
                # up in here...
                loclist = self.DT_TABLES[self.DT_BAD_DT][1]
        self.tdat.data_flens = loclist
        return loclist

    def _JPEG_quant_flengths(self, fl):
        """
        Helper method for fieldlengths method. Works out some of the field
        lengths for the JPEG Quantisation table - in this case the data needs
        to be picked through and examined.
        """
        # calculate the field lengths by going through the buffer stage by
        # stage and decoding enough info to determine all field lengths
        # fl should be [2,2,1,x] where x is a variable number
        endbit = fl[-1]
        while endbit > 0:
            # loop through and decode the rest
            f = self.SplitFields(self.tdat.dataraw, fl, 0)
            z = self.Conv_Int_NC(f[-2]) >> 4
            # z allows you to determine the size
            if z == 0:
                nextentry = 64
            else:
                nextentry = 128
            # build up the field length array and then loop if still necessary
            endbit = fl[-1] - nextentry
            f2 = fl[0:-1]
            if endbit == 0:
                fl = f2 + (nextentry, )
            else:
                fl = f2 + (nextentry, 1, endbit - 1)
        return fl

    def _JPEG_huff_flengths(self, fl):
        """
        Helper method for fieldlengths method. Works out some of the field
        lengths for the JPEG Huffman table - in this case the data needs
        to be picked through and examined.
        """
        # calculate the field lengths by going through the buffer stage by
        # stage and decoding enough info to determine all field lengths
        # fl should be [2,2,1,16,x] where x is a variable number
        validlengths = (12, 16, 162, 226)
        endbit = fl[-1]
        while endbit > 0:
            # loop through and decode the rest
            f = self.SplitFields(self.tdat.dataraw, fl, 0)
            nextentry = sum(self.Conv_Hufflengths(f[-2]))
            if nextentry in validlengths:
                # build up field length array and then loop if still necessary
                endbit = fl[-1] - nextentry
                f2 = fl[0:-1]
                if endbit == 0:
                    fl = f2 + (nextentry, )
                else:
                    fl = f2 + (nextentry, 1, 16, endbit - 17)
            else:
                # we have bad lengths
                ptext = ("Packet " + str(self.hdr.packetnum) + "(" +
                    self.hdr.tablename + ") - ")
                if fl[-1] in validlengths:
                    # There is a mistake in the lengths array, but we know how
                    # big it is supposed to be
                    self.tdat.errors.adderror(self.tdat.errors.E_JPEGVALS,
                        self.tdat.errors.ELVL_LOW, ptext +
                        "Invalid lengths in JPEG Huffman Table")
                else:
                    self.tdat.errors.adderror(self.tdat.errors.E_JPEGVALS,
                        self.tdat.errors.ELVL_LOW, ptext +
                        "Invalid data in JPEG Huffman Table, cannot determine" +
                        " all field lengths")
                return fl
        return fl

    def Calc_sourcecode(self, sa=None):
        """
        Given an integer Source Address, return a code indicating the source
        type. If Source Address is not given, the value is taken from the host
        NPIF object.
        """
        if sa is None:
            sa = self.hdr.sourceaddress

        if sa == 0:
            return self.SA_Format_Description_Data
        elif sa == 16:
            return self.SA_Mission_Data
        elif sa == 17:
            return self.SA_Target_Data
        elif sa == 32:
            return self.SA_Platform_Data
        elif sa == 48:
            return self.SA_Segment_Event_Index_Data
        elif sa == 63:
            return self.SA_User_Defined_Data
        elif sa >= 64 and sa <= 127:
            return self.SA_Sensor_Parametric_Data
        elif sa >= 128 and sa <= 191:
            return self.SA_Sensor_Data
        elif sa >= 193 and sa <= 255:
            return self.SA_Reserved
        else:
            return self.SA_Urecognised

    def Calc_tablecode(self, sa=None, dfa=None):
        """
        Given an integer Source Address and Data File Address, return a code
        indicating the source type. If either type is not given values are taken
        from the host NPIF object.
        """
        # given the source address and data file address in self,
        # return a code for the corresponding table
        if sa is None:
            sa = self.hdr.sourceaddress

        if dfa is None:
            dfa = self.hdr.datafileaddress

        if sa == 0:
            if dfa == 1:
                return self.DT_Format_Time_Tag_DT
            else:
                return self.DT_UNRECOGNISED_DFA_DT
        elif sa == 16:
            if dfa == 0:
                return self.DT_General_Admin_Ref_DT
            elif dfa == 16:
                return self.DT_Mission_Security_DT
            elif dfa == 32:
                return self.DT_Air_Tasking_Order_DT
            elif dfa == 48:
                return self.DT_Collection_Plat_ID_DT
            elif dfa >= 64 and dfa <= 95:
                return self.DT_Requester_DT
            elif dfa >= 96 and dfa <= 127:
                return self.DT_Requester_Remarks_DT
            else:
                return self.DT_UNRECOGNISED_DFA_DT
        elif sa == 17:
            dfa2 = dfa >> 4
            dfa3 = dfa & 1  # zero everything except the last bit
            if dfa2 >= 0 and dfa2 <= 254 and dfa3 == 0:
                return self.DT_General_Tgt_Info_DT
            elif dfa2 >= 256 and dfa2 <= 510:
                return self.DT_General_Tgt_Loc_DT
            elif dfa2 >= 512 and dfa2 <= 766:
                return self.DT_General_Tgt_EEI_DT
            elif dfa2 >= 768 and dfa2 <= 1022:
                return self.DT_General_Tgt_Remarks_DT
            else:
                return self.DT_UNRECOGNISED_DFA_DT
        elif sa == 32:
            dfa2 = dfa >> 16
            dfa3 = dfa & 65535  # zeros out left half of dfa bits
            if dfa2 >= 0 and dfa2 <= 64 and dfa3 == 0:
                return self.DT_Min_Dynamic_Plat_DT
            elif dfa2 >= 0 and dfa2 <= 64 and dfa3 == 1:
                return self.DT_Comp_Dynamic_Plat_DT
            elif dfa >= 4259840 and dfa <= 4260095:
                return self.DT_Sensor_Grouping_DT
            else:
                return self.DT_UNRECOGNISED_DFA_DT
        elif sa == 48:
            dfa2 = dfa >> 8
            dfa3 = dfa & 255    # zeros out left hand 24 bits
            if dfa == 0:
                return self.DT_End_Record_Marker_DT
            elif dfa == 1:
                return self.DT_End_Segment_Marker_DT
            elif dfa == 2:
                return self.DT_Event_Marker_DT
            elif dfa2 >= 1 and dfa2 <= 255 and dfa3 == 0:
                return self.DT_Segment_Index_DT
            elif dfa2 >= 1 and dfa2 <= 255 and dfa3 != 0:
                return self.DT_Event_Index_DT
            else:
                return self.DT_UNRECOGNISED_DFA_DT
        elif sa == 63:
            if dfa >= 0 and dfa <= 65535:
                return self.DT_User_Defined_DT
            else:
                return self.DT_UNRECOGNISED_DFA_DT
        elif sa >= 64 and sa <= 127:
            dfa2 = dfa >> 16
            dfa3 = dfa & 65535   # zeros out left half of dfa bits
            if dfa2 >= 0 and dfa2 <= 64 and dfa3 == 0:
                return self.DT_Sensor_ID_DT
            elif dfa == 1:
                return self.DT_PASSIVE_Sensor_Des_DT
            elif dfa == 2:
                return self.DT_Sensor_Calibration_DT
            elif dfa == 3:
                return self.DT_Sync_Hier_and_ImBld_DT
            elif dfa == 4:
                return self.DT_Sensor_Data_Timing_DT
            elif dfa == 6:
                return self.DT_Sensor_Op_Status_DT
            elif dfa == 16:
                return self.DT_Sensor_Position_DT
            elif dfa == 32:
                return self.DT_Min_Sensor_Att_DT
            elif dfa == 48:
                return self.DT_Comp_Sensor_Att_DT
            elif dfa >= 80 and dfa <= 95:
                return self.DT_Gimbals_Position_DT
            elif dfa >= 96 and dfa <= 111:
                return self.DT_Min_Gimbals_Att_DT
            elif dfa >= 112 and dfa <= 127:
                return self.DT_Comp_Gimbals_Att_DT
            elif dfa == 256:
                return self.DT_Sensor_Compression_DT
            elif dfa == 257:
                return self.DT_JPEG_Sensor_Quant_DT
            elif dfa == 258:
                return self.DT_JPEG_Sensor_Huffman_DT
            elif dfa == 259:
                return self.DT_JPEG2000_Des_DT
            elif dfa == 260:
                return self.DT_JPEG2000_Index_DT
            elif dfa >= 512 and dfa <= 767:
                return self.DT_Sensor_Index_DT
            elif dfa == 4096:
                return self.DT_Passive_Sensor_El_DT
            elif dfa == 4112:
                return self.DT_Sensor_Samp_Coord_Des_DT
            elif dfa == 4128:
                return self.DT_Sensor_Samp_Timing_Des_DT
            elif dfa == 65537:
                return self.DT_RADAR_Sensor_Des_DT
            elif dfa == 66304:
                return self.DT_RADAR_Collect_Plane_ImGeo_DT
            elif dfa == 66305:
                return self.DT_Reference_Track_DT
            elif dfa == 66306:
                return self.DT_Rectified_ImGeo_DT
            elif dfa == 66307:
                return self.DT_Virtual_Sensor_Def_DT
            elif dfa == 66308:
                return self.DT_RADAR_Parameters_DT
            elif dfa == 66309:
                return self.DT_ISAR_Track_DT
            elif dfa == 69632:
                return self.DT_RADAR_Element_DT
            else:
                return self.DT_UNRECOGNISED_DFA_DT
        elif sa >= 128 and sa <= 191:
            if dfa == 0:
                return self.DT_Sensor_DT
            elif dfa == 16:
                return self.DT_Sensor_Samp_xCoord_DT
            elif dfa == 32:
                return self.DT_Sensor_Samp_yCoord_DT
            elif dfa == 48:
                return self.DT_Sensor_Samp_zCoord_DT
            elif dfa == 80:
                return self.DT_Sensor_Samp_Timing_DT
            elif dfa == 96:
                return self.DT_4607_GMTI_DT
            elif dfa == 112:
                return self.DT_4609_Motion_Imagery_DT
            elif dfa == 128:
                return self.DT_Range_Finder_DT
            else:
                return self.DT_UNRECOGNISED_DFA_DT
        elif sa >= 193 and sa <= 255:
            return self.DT_Reserved_DT
        else:
            return self.DT_UNRECOGNISED_SA_DT

    def _calc_headflags(self, intflags):
        """
        Given the int representation of the set of header flags determine
        what flags are set and then set them in the NPIF object.
        """
        if intflags & 8 == 8:
            self.hdr.ambleflag = 1
        else:
            self.hdr.ambleflag = 0
        if intflags & 4 == 4:
            self.hdr.crcflag = 1
        else:
            self.hdr.crcflag = 0
        if intflags & 2 == 2:
            self.hdr.compressflag = 1
        else:
            self.hdr.compressflag = 0

    def extract_header(self, buff, pnum):
        """
        Given a raw buffer break out the 7023 header information, and header
        related derived values. Assumes sync data is *not present* at the start
        of buff. pnum should be an integer indicating which packet this is in
        the original file (as this is helpful info for error messages).
        Raw table field data will be put into the dararaw field for later
        extraction.
        """
        # given a raw buffer break out the 7023 information
        # NB assumes sync data is not present at the start
        self.hdr.packetnum = pnum
        ptext = "Packet " + str(pnum) + "- "
        a = len(buff)
        self.hdr.totlen = (a + self.SYNC_LEN)
        if a < self.HDR_LEN:
            self.hdr.errors.adderror(self.hdr.errors.E_HEADLEN,
                self.hdr.errors.ELVL_MED, ptext +
                "Input Buffer not long enough for minimum header information")
            self.blockdataextract = True
            return
        #
        f = struct.unpack('>4B3IQB5s2s', buff[0:32])
        self.hdr.edition = f[0]
        self._calc_headflags(f[1])
        self.hdr.segmentnum = f[2]
        self.hdr.sourceaddress = f[3]
        self.hdr.datafileaddress = f[4]
        self.hdr.datafilesize = f[5]
        self.hdr.datafilenum = f[6]
        self.hdr.timetag = f[7]
        self.hdr.synctype = self.Lookup_Sync_Type_Code(f[8])
        self.hdr.reserved = self.Conv_Hex(f[9])
        self.hdr.headcrc = self.Conv_Hex(f[10])

        # start with table code calc as this has info useful to other parts
        self.hdr.tablecode = self.Calc_tablecode()
        if self.hdr.tablecode is self.DT_UNRECOGNISED_DFA_DT:
            self.hdr.errors.adderror(self.hdr.errors.E_DFAADD,
                self.hdr.errors.ELVL_LOW, ptext +
                "Data File Address in Header is unrecognised (hex= " +
                str(f[4]) + ")")
            self.blockdataextract = True

        self.hdr.tablename = self.S7023_TABLE_NAMES[self.hdr.tablecode]

        if self.hdr.tablecode not in self.S7023_ALL_VALID_TABLES:
            self.hdr.errors.adderror(self.hdr.errors.E_UKNPACKET,
                self.hdr.errors.ELVL_LOW, ptext +
                "Unrecognised Data Packet (sa= " + str(f[3]) +
                ", dfa= " + str(f[4]) + ")")
            self.blockdataextract = True
        else:
            ptext = ("Packet " + str(self.hdr.packetnum) + "(" +
                self.hdr.tablename + ") - ")
            lenrange = self.S7023_TABLE_SIZES[self.hdr.tablecode]
            if self.nocrcdatasize() < lenrange[0]:
                self.hdr.errors.adderror(self.hdr.errors.E_DATALEN,
                    self.hdr.errors.ELVL_MED, ptext +
                    "Data Packet length too short (stated length [adjusted for"
                    " crc if appropriate]= " + str(self.nocrcdatasize()) +
                    ", allowable range= " + str(lenrange) + ")")
                self.blockdataextract = True
            elif self.nocrcdatasize() > lenrange[1]:
                self.hdr.errors.adderror(self.hdr.errors.E_DATALEN,
                    self.hdr.errors.ELVL_MED, ptext +
                    "Data Packet length too long (stated length [adjusted for" +
                    " crc if appropriate]= " + str(self.nocrcdatasize()) +
                    ", allowable range= " + str(lenrange) + ")")
        # do initial checks on read in data
        if self.hdr.edition not in self.DATA_VALID_ED:
            # is the edition number outside of the expected values
            self.hdr.errors.adderror(self.hdr.errors.E_EDITION,
                self.hdr.errors.ELVL_LOW, ptext +
                "Claimed Edition (" + str(self.hdr.edition) +
                ") is not a valid edition")
        elif self.hdr.edition <= 3 and self.hdr.tablecode in self.S7023_NOT_ED3:
            # is it reporting Ed3 but using a table that only existed in Ed 4
            self.hdr.errors.adderror(self.hdr.errors.E_EDITION,
                self.hdr.errors.ELVL_LOW, ptext +
                "This table did not exist in Edition 3 or earlier")
        #
        if self.TXT_UNKN_ENUM in str(self.hdr.synctype):
            # is the sync code in the header recognised
            self.hdr.errors.adderror(self.hdr.errors.E_ENUMERATION,
                self.hdr.errors.ELVL_LOW, ptext +
                "Unknown Enumeration in Header Sync Type (int= " +
                str(f[8]) + ")")
        #
        if self.hdr.reserved != "0000000000":
            # is the reserved field populated with anything other than all 0s
            self.hdr.errors.adderror(self.hdr.errors.E_RESERVED,
                self.hdr.errors.ELVL_WARN, ptext +
                "Reserved field in header is not empty (hex= " +
                str(self.hdr.reserved) + ")")
        #
        crccalc = self.crc16(buff[:30])
        if self.hdr.headcrc != crccalc:
            # does the header CRC match our clculated value
            self.hdr.errors.adderror(self.hdr.errors.E_HEADCRC,
                self.hdr.errors.ELVL_LOW, ptext +
                "CRC value in header is not correct (header value= " +
                str(self.hdr.headcrc) + ", calculated value= " + str(crccalc)
                + ")")
        #
        self.hdr.sourcecode = self.Calc_sourcecode()
        if self.hdr.sourcecode is self.SA_Reserved:
            # is the source address using a reserved value?
            self.hdr.errors.adderror(self.hdr.errors.E_SOURCEADD,
                self.hdr.errors.ELVL_LOW, ptext +
                "Source address in Header uses reserved value (int= " +
                str(f[3]) + ")")
            self.blockdataextract = True
        elif self.hdr.sourcecode is self.SA_Urecognised:
            # is the source address using an unrecognised value?
            self.hdr.errors.adderror(self.hdr.errors.E_SOURCEADD,
                self.hdr.errors.ELVL_LOW, ptext +
                "Source address in Header uses unknown value (int= " +
                str(f[3]) + ")")
            self.blockdataextract = True

        if self.hdr.tablecode == self.DT_User_Defined_DT:
            # is a user defined table being used? - warn if it is.
            # don't block this - handle as special case
            self.hdr.errors.adderror(self.hdr.errors.E_USERDEFINED,
                self.hdr.errors.ELVL_WARN, ptext +
                "User Defined Table")

        self.hdr.claimlen = (self.HDR_LEN + self.SYNC_LEN +
            self.hdr.datafilesize)
        #
        # grab any extra bytes, if present
        ldiff = self.hdr.totlen - self.hdr.claimlen
        if ldiff > 0:
            # are there extra bytes between this packet and the next?
            self.hdr.extraraw = buff[-ldiff:]
            self.hdr.errors.adderror(self.hdr.errors.E_EXTRABYTE,
                self.hdr.errors.ELVL_WARN, ptext + str(ldiff) +
                " extra bytes detected after packet (extra= " +
                str(self.Conv_Hex(self.hdr.extraraw)) + ")")
        else:
            self.hdr.extraraw = ""
        #
        # now calculate any additional values derived from sa and dfa
        if self.hdr.tablecode in self.S7023_Requester_Index_Tables:
            self.hdr.Requester_Idx_Num = self.Calc_Requester_ID()
            if self.hdr.Requester_Idx_Num in [-1, -2]:
                # then error extracting number
                self.hdr.errors.adderror(self.hdr.errors.E_ADDRESSEXTRACT,
                    self.hdr.errors.ELVL_LOW, ptext +
                    "Error extracting Requester Index Num from DFA")
        if self.hdr.tablecode in self.S7023_Group_ID_Tables:
            self.hdr.Group_ID_Num = self.Calc_Group_ID()
            if self.hdr.Group_ID_Num in [-1, -2]:
                # then error extracting number
                self.hdr.errors.adderror(self.hdr.errors.E_ADDRESSEXTRACT,
                    self.hdr.errors.ELVL_LOW, ptext +
                    "Error extracting Group ID Num from DFA")
        if self.hdr.tablecode in self.S7023_Event_ID_Tables:
            self.hdr.Event_ID_Num = self.Calc_Event_ID()
            if self.hdr.Event_ID_Num in [-1, -2]:
                # then error extracting number
                self.hdr.errors.adderror(self.hdr.errors.E_ADDRESSEXTRACT,
                    self.hdr.errors.ELVL_LOW, ptext +
                    "Error extracting Event ID Num from DFA")
        if self.hdr.tablecode in self.S7023_Segment_ID_Tables:
            self.hdr.Segment_ID_Num = self.Calc_Segment_ID()
            if self.hdr.Segment_ID_Num in [-1, -2]:
                # then error extracting number
                self.hdr.errors.adderror(self.hdr.errors.E_ADDRESSEXTRACT,
                    self.hdr.errors.ELVL_LOW, ptext +
                    "Error extracting Segment ID Num from DFA")
        if self.hdr.tablecode in self.S7023_Location_ID_Tables:
            self.hdr.Location_ID_Num = self.Calc_Location_ID()
            if self.hdr.Location_ID_Num in [-1, -2]:
                # then error extracting number
                self.hdr.errors.adderror(self.hdr.errors.E_ADDRESSEXTRACT,
                    self.hdr.errors.ELVL_LOW, ptext +
                    "Error extracting Location ID Num from DFA")
        if self.hdr.tablecode in self.S7023_Target_ID_Tables:
            self.hdr.Target_ID_Num = self.Calc_Target_ID()
            if self.hdr.Target_ID_Num in [-1, -2]:
                # then error extracting number
                self.hdr.errors.adderror(self.hdr.errors.E_ADDRESSEXTRACT,
                    self.hdr.errors.ELVL_LOW, ptext +
                    "Error extracting Target ID Num from DFA")
        if self.hdr.tablecode in self.S7023_Gimbal_ID_Tables:
            self.hdr.Gimbal_ID_Num = self.Calc_Gimbal_ID()
            if self.hdr.Gimbal_ID_Num in [-1, -2]:
                # then error extracting number
                self.hdr.errors.adderror(self.hdr.errors.E_ADDRESSEXTRACT,
                    self.hdr.errors.ELVL_LOW, ptext +
                    "Error extracting Gimbal ID Num from DFA")
        if self.hdr.tablecode in self.S7023_Sensor_ID_Tables:
            self.hdr.Sensor_ID_Num = self.Calc_Sensor_ID()
            if self.hdr.Sensor_ID_Num in [-1, -2]:
                # then error extracting number
                self.hdr.errors.adderror(self.hdr.errors.E_ADDRESSEXTRACT,
                    self.hdr.errors.ELVL_LOW, ptext +
                    "Error extracting Sensor ID Num from SA")
        if self.hdr.tablecode in self.S7023_Platform_ID_Tables:
            self.hdr.Platform_ID_Num = self.Calc_Platform_ID()
            if self.hdr.Platform_ID_Num in [-1, -2]:
                # then error extracting number
                self.hdr.errors.adderror(self.hdr.errors.E_ADDRESSEXTRACT,
                    self.hdr.errors.ELVL_LOW, ptext +
                    "Error extracting Platform ID Num from DFA")
        #
        # finally grab data and place in dataraw
        self.tdat.dataraw = (
            buff[self.HDR_LEN:self.HDR_LEN +
            self.hdr.datafilesize])

    def extract_data(self, buff, allerr=True):
        """
        Given a raw buffer containing data table info, break out the data.
        Assumes no header information present in buff. Also carries out a number
        of checks on the correctness of the table data (stored in error elements
        of object).

        allerr controls whether all error checks are run. If set to false, some
        error checks on the buffer are ignored (speeds extraction times if a
        full errors analysis is not important)
        """
        if self.hdr.blockdataextract is True:
            return

        ptext = "Packet " + str(self.hdr.packetnum) + "(" + self.hdr.tablename + ") - "

        if self.hdr.tablecode == self.DT_User_Defined_DT:
            # attempt to extract and check data crc if present
            if self.hdr.crcflag != 0:
                self.tdat.datacrc = self.Conv_Hex(buff[-2:])
                # also check data crc
                calcdcrc = self.crc16(buff[:-2])
                if self.tdat.datacrc != calcdcrc:
                    self.tdat.errors.adderror(self.tdat.errors.E_DATACRC,
                        self.tdat.errors.ELVL_LOW, ptext +
                        "CRC value of data is not correct (file value= " +
                        str(self.tdat.datacrc) + ", calculated value= " +
                        str(calcdcrc) + ")")

        if self.hdr.tablecode not in self.ALL_VALID_TABLES_EXCEPT_USER_DEFINED:
            # cannot extract further data from User Defined or unrecognised tables
            return

        # expects a buffer with the table data in it
        # Extract the table data (i.e. non header data) in the packet
        self.tdat.fieldnames = self.S7023_FLD_NAMES[self.hdr.tablecode]
        self.tdat.fieldtypes = self.S7023_FLD_TYPES[self.hdr.tablecode]
        self.tdat.fieldfuncs = self.S7023_FLD_FUNCS[self.hdr.tablecode]
        self.tdat.fieldlflags = self.S7023_FLD_LIST_FLAGS[self.hdr.tablecode]
        self.tdat.fieldreqs = self.S7023_FLD_REQS[self.hdr.tablecode]

        fnames = self.tdat.fieldnames
        ftypes = self.tdat.fieldtypes
        ffunc = self.tdat.fieldfuncs
        flflag = self.tdat.fieldlflags

        flens = self.fieldlengths()
        lfcount1 = self.tdat.fieldlflags.count(1)
        self.tdat.numfieldsrepeating = lfcount1

        if lfcount1 > 0:
            # we have some data needed to be put into lists
            fentries = len(flens)
            lfcount0 = flflag.count(0)
            numrepeats = (fentries - lfcount0) // lfcount1
            if float(numrepeats) != (fentries - lfcount0) / float(lfcount1):
                self.tdat.errors.adderror(self.tdat.errors.E_DATALEN,
                    self.tdat.errors.ELVL_LOW, ptext +
                    "Table does not have full set of repeated elements")
            # work out which bits repeat and do not repeat in a, n, lf and func
            tup = list(zip(flflag, ftypes, fnames, ffunc))
            norep = [(x, y, z, w) for x, y, z, w in tup if x == 0]
            rep = [(x, y, z, w) for x, y, z, w in tup if x == 1]
            # now build new and full versions of a, n, func & lf
            full = norep + rep * numrepeats
            unfull = list(zip(*full))
            flflag, ftypes, fnames, ffunc = unfull
            self.tdat.numrepeats = numrepeats
        else:
            self.tdat.numrepeats = 0

        f = self.SplitFields(buff, flens, self.hdr.crcflag)
        if f == []:
            # buff was too short
            self.tdat.errors.adderror(self.tdat.errors.E_DATALEN,
                self.tdat.errors.ELVL_LOW, ptext +
                "Buffer not long enough to extract all expected data elements")
            return
        #
        fentries = len(f)
        if self.hdr.crcflag != 0:
            self.tdat.datacrc = self.Conv_Hex(f[-1])
            fentries -= 1
            # also check data crc
            calcdcrc = self.crc16(buff[:-2])
            if self.tdat.datacrc != calcdcrc:
                # Calculated data CRC did not match reported CRC
                self.tdat.errors.adderror(self.tdat.errors.E_DATACRC,
                    self.tdat.errors.ELVL_LOW, ptext +
                    "CRC value of data is not correct (file value= " +
                    str(self.tdat.datacrc) + ", calculated value= " +
                    str(calcdcrc) + ")")
        #
        d = collections.defaultdict(lambda: None)
        if self.tdat.numfieldsrepeating > 0:
            # create blank list entries where necesary
            for b in fnames[-self.tdat.numfieldsrepeating:]:
                d[b] = []
        #
        for i in range(fentries):
            try:
                firstconv = self.S7023_F_Conversions[ftypes[i]](self, f[i])
                if ffunc[i] is None:
                    if flflag[i] == 0:
                        d[fnames[i]] = firstconv
                    else:
                        d[fnames[i]].append(firstconv)
                else:
                    if flflag[i] == 0:
                        d[fnames[i]] = ffunc[i](self, firstconv)
                    else:
                        d[fnames[i]].append(ffunc[i](self, firstconv))
            except:
                if flflag[i] == 0:
                    d[fnames[i]] = self.TXT_UNKN_ERROR
                else:
                    d[fnames[i]].append(self.TXT_UNKN_ERROR)
                self.tdat.errors.adderror(self.tdat.errors.E_UNKNOWN,
                    self.tdat.errors.ELVL_MED, ptext +
                    "Unknown Error extracting '" + str(fnames[i]) + "' field")
        #
        self.tdat.tcontents = d
        if allerr:
            # run checks on packet
            self.Check_DT_Enum_Errors()
            self.Check_DT_DTG_Errors()
            self.Check_DT_ASCII_Errors()
            self.Check_DT_Angle_Errors()
            self.Check_DT_Mand_Fields()
            self.Check_DT_Cond_Fields()
            self.check_dt_specific()
            self.check_dt_suspicious_vals()
        return

    def Check_DT_Enum_Errors(self):
        """
        Check for errors in enumerated values, storing any errors in the table
        data error object.
        """
        ptext = ("Packet " + str(self.hdr.packetnum) + "(" + self.hdr.tablename +
            ") - Invalid Enumeration, field: ")
        for x, y in self.Find_Datatypes_in_Table('e'):
            if isinstance(y, list):
                for i, b in enumerate(y):
                    if self.TXT_UNKN_ENUM in b:
                        self.tdat.errors.adderror(self.tdat.errors.E_ENUMERATION,
                            self.tdat.errors.ELVL_LOW, ptext + str(x) +
                            ", entry: " + str(i))
            else:
                if self.TXT_UNKN_ENUM in y:
                    self.tdat.errors.adderror(self.tdat.errors.E_ENUMERATION,
                        self.tdat.errors.ELVL_LOW, ptext + str(x))
        return

    def Check_DT_DTG_Errors(self):
        """
        Check for errors in DTG values, storing any errors in the table
        data error object.
        """
        ptext = ("Packet " + str(self.hdr.packetnum) + "(" + self.hdr.tablename +
            ") - Invalid DTG value, field: ")
        for x, y in self.Find_Datatypes_in_Table('d'):
            if isinstance(y, list):
                for i, b in enumerate(y):
                    if self.TXT_BAD_DTG in b:
                        self.tdat.errors.adderror(self.tdat.errors.E_DTG,
                            self.tdat.errors.ELVL_LOW, ptext + str(x) +
                            ", entry: " + str(i))
            else:
                if self.TXT_BAD_DTG in y:
                    self.tdat.errors.adderror(self.tdat.errors.E_DTG,
                        self.tdat.errors.ELVL_LOW, ptext + str(x))
        return

    def Check_DT_ASCII_Errors(self):
        """
        Check for invalid ASCII fields, storing any errors in the table
        data error object.
        """
        ptext = ("Packet " + str(self.hdr.packetnum) + "(" + self.hdr.tablename
            + ") - Invalid ASCII, field: ")
        for x, y in self.Find_Datatypes_in_Table('a'):
            if isinstance(y, list):
                for i, b in enumerate(y):
                    if self.TXT_BAD_ASCII in b:
                        self.tdat.errors.adderror(self.tdat.errors.E_ASCII,
                            self.tdat.errors.ELVL_LOW, ptext + str(x) +
                            ", entry: " + str(i))
            else:
                if self.TXT_BAD_ASCII in y:
                    self.tdat.errors.adderror(self.tdat.errors.E_ASCII,
                        self.tdat.errors.ELVL_LOW, ptext + str(x))
        return

    def Check_DT_Angle_Errors(self):
        """
        Check for out-of-range Angles in fields, storing any errors in the table
        data error object.
        """
        ptext = ("Packet " + str(self.hdr.packetnum) + "(" + self.hdr.tablename +
            ") - Out of Range Angle, field: ")
        for x, y in self.Find_Datatypes_in_Table('r'):
            if isinstance(y, list):
                for i, b in enumerate(y):
                    if self.TXT_BAD_ANGLE in str(b):
                        self.tdat.errors.adderror(self.tdat.errors.E_ANGLE,
                            self.tdat.errors.ELVL_LOW, ptext + str(x) +
                            ", entry: " + str(i))
            else:
                if self.TXT_BAD_ANGLE in str(y):
                    self.tdat.errors.adderror(self.tdat.errors.E_ANGLE,
                        self.tdat.errors.ELVL_LOW, ptext + str(x))
        #
        # need to repeat for 'c' data
        for x, y in self.Find_Datatypes_in_Table('c'):
            if isinstance(y, list):
                for i, b in enumerate(y):
                    if self.TXT_BAD_ANGLE in str(b[0]) or self.TXT_BAD_ANGLE in str(b[1]):
                        self.tdat.errors.adderror(self.tdat.errors.E_ANGLE,
                            self.tdat.errors.ELVL_LOW, ptext + str(x) +
                            ", entry: " + str(i))
            else:
                if self.TXT_BAD_ANGLE in str(y[0]) or self.TXT_BAD_ANGLE in str(y[1]):
                    self.tdat.errors.adderror(self.tdat.errors.E_ANGLE,
                        self.tdat.errors.ELVL_LOW, ptext + str(x))
        return

    def Check_DT_Mand_Fields(self):
        """
        Check that mandatory fields are not populated with NULL values, storing
        any errors in the table data error object.
        """
        ptext = ("Packet " + str(self.hdr.packetnum) + "(" +
            self.hdr.tablename + ") - Mandatory Field has NULL value, field: ")
        # in case not populated (e.g. user defined table)
        if self.tdat.fieldtypes is not None:
            for i, t in enumerate(self.tdat.fieldtypes):
                if self.tdat.fieldreqs[i] == 'm':
                    # the list is range of types checked, excluding coords
                    # (done below)
                    if t in ['a', 'r', 'i', 'j', 'd']:
                        n = self.tdat.fieldnames[i]
                        xcont = self.tdat.tcontents[n]
                        if isinstance(xcont, list):
                            for j, b in enumerate(xcont):
                                if self.TXT_NULL in str(b):
                                    self.tdat.errors.adderror(
                                        self.tdat.errors.E_MANDFIELD,
                                        self.tdat.errors.ELVL_LOW, ptext +
                                        str(n) + ", entry: " + str(j))
                        else:
                            if self.TXT_NULL in str(xcont):
                                self.tdat.errors.adderror(
                                    self.tdat.errors.E_MANDFIELD,
                                    self.tdat.errors.ELVL_LOW, ptext +
                                    str(n))
                    elif t == 'c':
                        n = self.tdat.fieldnames[i]
                        xcont = self.tdat.tcontents.get(n,(None,None))
                        if isinstance(xcont, list):
                            for j, b in enumerate(xcont):
                                if self.TXT_NULL in str(b[0]) or self.TXT_NULL in str(b[1]):
                                    self.tdat.errors.adderror(
                                        self.tdat.errors.E_MANDFIELD,
                                        self.tdat.errors.ELVL_LOW, ptext +
                                        str(n) + ", entry: " + str(j))
                        else:
                            if self.TXT_NULL in str(xcont[0]) or self.TXT_NULL in str(xcont[1]):
                                self.tdat.errors.adderror(
                                    self.tdat.errors.E_MANDFIELD,
                                    self.tdat.errors.ELVL_LOW, ptext +
                                    str(n))
                    else:
                        # not a type that can be checked
                        # h (only used twice, accross all tables - jpeg tables)
                        # e (any problems handled under enumeration checks)
                        # b (one use only in gen tgt info table)
                        # q (three uses only - dynam platform tables and jpeg huffman)
                        # x (9 uses, but mostly for payload data)
                        # z (no uses - backup type for errors)
                        pass
        return

    def Check_DT_Cond_Fields(self):
        """
        Check that any conditional fields are populated OK in the given table
        Only 7 tables have conditional fields. Each is handled separately.
        Any errors are stored in the table data error object.
        """
        ptext = ("Packet " + str(self.hdr.packetnum) + "(" + self.hdr.tablename +
            ") - ")

        if self.hdr.tablecode == self.DT_Min_Dynamic_Plat_DT:
            # 3 'sets' of conditionals here
            # 1) at least one of fields 3,4 & 5 be populated
            # 2) at least one of 6 & 7 must be populated
            # 3) at least one of 8 & 12 must be populated
            #
            # Condition 1
            if (self.TXT_NULL in str(self.tdat.tcontents['MSL Altitude']) and
                self.TXT_NULL in str(self.tdat.tcontents['AGL Altitude']) and
                    self.TXT_NULL in str(self.tdat.tcontents['GPS Altitude'])):
                self.tdat.errors.adderror(self.tdat.errors.E_CONDFIELD,
                    self.tdat.errors.ELVL_LOW, ptext +
                    "At Least one of 'MSL Altitude', 'AGL Altitude' & 'GPS " +
                    "Altitude' must be populated")
            # Condition 2
            if (self.TXT_NULL in str(self.tdat.tcontents['Platform true airspeed']) and
                    self.TXT_NULL in str(self.tdat.tcontents['Platform ground speed'])):
                self.tdat.errors.adderror(self.tdat.errors.E_CONDFIELD,
                    self.tdat.errors.ELVL_LOW, ptext +
                    "At Least one of 'Platform true airspeed' & 'Platform " +
                    "ground speed' must be populated")
            # Condition 3
            if (self.TXT_NULL in str(self.tdat.tcontents['Platform true Course']) and
                    self.TXT_NULL in str(self.tdat.tcontents['Platform Yaw'])):
                self.tdat.errors.adderror(self.tdat.errors.E_CONDFIELD,
                    self.tdat.errors.ELVL_LOW, ptext +
                    "At Least one of 'Platform true Course' & 'Platform Yaw'" +
                    " must be populated")
        elif self.hdr.tablecode == self.DT_Comp_Dynamic_Plat_DT:
            # 3 'sets' of conditionals here
            # 1) at least one of fields 3,4 & 5 be populated
            # 2) at least one of 6 & 7 must be populated
            # 3) at least one of 8 & 12 must be populated
            #
            # Condition 1
            if (self.TXT_NULL in str(self.tdat.tcontents['MSL Altitude']) and
                self.TXT_NULL in str(self.tdat.tcontents['AGL Altitude']) and
                    self.TXT_NULL in str(self.tdat.tcontents['GPS Altitude'])):
                self.tdat.errors.adderror(self.tdat.errors.E_CONDFIELD,
                    self.tdat.errors.ELVL_LOW, ptext +
                    "At Least one of 'MSL Altitude', 'AGL Altitude' & " +
                    "'GPS Altitude' must be populated")
            #Condition 2
            if (self.TXT_NULL in str(self.tdat.tcontents['Platform true airspeed']) and
                    self.TXT_NULL in str(self.tdat.tcontents['Platform ground speed'])):
                self.tdat.errors.adderror(self.tdat.errors.E_CONDFIELD,
                    self.tdat.errors.ELVL_LOW, ptext +
                    "At Least one of 'Platform true airspeed' & 'Platform " +
                    "ground speed' must be populated")
            # Condition 3
            if (self.TXT_NULL in str(self.tdat.tcontents['Platform true Course']) and
                    self.TXT_NULL in str(self.tdat.tcontents['Platform Yaw'])):
                self.tdat.errors.adderror(self.tdat.errors.E_CONDFIELD,
                    self.tdat.errors.ELVL_LOW, ptext +
                    "At Least one of 'Platform true Course' & 'Platform Yaw' " +
                    "must be populated")
        elif self.hdr.tablecode == self.DT_Event_Index_DT:
            # two related conditionals here (hope my interpretation is correct)
            # 1) if field 1 enumeration is 0 or 3 field 2 must be non NULL,
            #    otherwise field 2 must be NULL
            # 2) if field 1 enumeration is not 0 or 3, field 3 must be a
            #    number, otherwise it must be 0
            #
            # Condition 1
            if (self.tdat.tcontents['Event Type'] == self.Lookup_Event_Type(0) or
                    self.tdat.tcontents['Event Type'] == self.Lookup_Event_Type(3)):
                if self.tdat.tcontents['Target Number'] == self.TXT_NULL:
                    self.tdat.errors.adderror(self.tdat.errors.E_CONDFIELD,
                        self.tdat.errors.ELVL_LOW, ptext +
                        "With Given Value of 'Event Type', 'Target Number' " +
                        "must be non-NULL")
                if self.tdat.tcontents['Target Sub-section'] != 0:
                    self.tdat.errors.adderror(self.tdat.errors.E_CONDFIELD,
                        self.tdat.errors.ELVL_LOW, ptext +
                        "With Given Value of 'Event Type', 'Target " +
                        "Sub-section' must be '0'")
            # Condition 2
            else:
                if self.tdat.tcontents['Target Number'] != self.TXT_NULL:
                    self.tdat.errors.adderror(self.tdat.errors.E_CONDFIELD,
                        self.tdat.errors.ELVL_LOW, ptext +
                        "With Given Value of 'Event Type', 'Target Number' " +
                        "must be NULL")
                if self.tdat.tcontents['Target Sub-section'] == 0:
                    self.tdat.errors.adderror(self.tdat.errors.E_CONDFIELD,
                        self.tdat.errors.ELVL_LOW, ptext +
                        "With Given Value of 'Event Type', 'Target " +
                        "Sub-section' must not be '0'")
        elif self.hdr.tablecode == self.DT_RADAR_Sensor_Des_DT:
            # 1) if field 7 is enumeration '8', field 12 must be enumeration '0'
            # 2) if field 7 has any other value, field 12 must not be enumeration '0'
            #
            # Condition 1
            if self.tdat.tcontents['Coordinate System Orientation'] == self.Lookup_RAD_Coord_Sys_Orient(8):
                if self.tdat.tcontents['vld orientation'] != self.Lookup_RAD_vld_orientation(0):
                    self.tdat.errors.adderror(self.tdat.errors.E_CONDFIELD,
                        self.tdat.errors.ELVL_LOW, ptext +
                        "With Given Value of 'Coordinate System Orientation', 'vld orientation' must be 'Unused'")
            # Condition 2
            else:
                if self.tdat.tcontents['vld orientation'] == self.Lookup_RAD_vld_orientation(0):
                    self.tdat.errors.adderror(self.tdat.errors.E_CONDFIELD,
                        self.tdat.errors.ELVL_LOW, ptext +
                        "With Given Value of 'Coordinate System Orientation', 'vld orientation' must not be 'Unused'")
        elif self.hdr.tablecode == self.DT_Reference_Track_DT:
            # at least one of fields 2, 3 and 4 must be populated
            if (self.TXT_NULL in str(self.tdat.tcontents['Sensor Virtual Position MSL altitude']) and
                self.TXT_NULL in str(self.tdat.tcontents['Sensor Virtual Position AGL altitude']) and
                    self.TXT_NULL in str(self.tdat.tcontents['Sensor Virtual Position GPS altitude'])):
                    self.tdat.errors.adderror(self.tdat.errors.E_CONDFIELD,
                        self.tdat.errors.ELVL_LOW, ptext +
                        "At Least one of the three Altitude fields must be " +
                        "populated")
        elif self.hdr.tablecode == self.DT_Rectified_ImGeo_DT:
            # 1) if f29 (Projection type) is enum (1) then data 1 to data 6 should
            # be non null
            # 2) if f29 (Projection type) is enum (2) or enum (3) then data 1 to
            # data 5 should be non null
            # 3) if f29 (Projection type) is enum (4) then data 1 to data 7 should
            # be non null
            # all other data values should be null
            x = 0
            z = 0
            if self.tdat.tcontents['Projection type'] != self.Lookup_Projection_type(0):
                # only check when not enum(0) - now generate data for all three conditions
                # for all, data1 to data5 should be non null
                for a in ['Data 1', 'Data 2', 'Data 3', 'Data 4', 'Data 5']:
                    x += 1
                    if self.TXT_NULL in str(self.tdat.tcontents[a]):
                        x -= 1
                    # x records the number of non null in data1 to data5 (hopefully 5)
                for a in ['Data 8', 'Data 9', 'Data 10', 'Data 11', 'Data 12',
                            'Data 13', 'Data 14', 'Data 15', 'Data 16',
                            'Data 17', 'Data 18', 'Data 19', 'Data 20']:
                    z += 1
                    if self.TXT_NULL in str(self.tdat.tcontents[a]):
                        z -= 1
                    # z records the number of non null in data8 to data20 (hopefully 0) 
                # how many non-null in data6
                if self.TXT_NULL in str(self.tdat.tcontents['Data 6']):
                    d6 = 0
                else:
                    d6 = 1
                # how many non-null in data7
                if self.TXT_NULL in str(self.tdat.tcontents['Data 7']):
                    d7 = 0
                else:
                    d7 = 1
                # now check each condition using values calculated above
                # Condition 1
                if self.tdat.tcontents['Projection type'] == self.Lookup_Projection_type(1):
                    if x != 5 or d6 != 1:
                        self.tdat.errors.adderror(
                            self.tdat.errors.E_CONDFIELD,
                            self.tdat.errors.ELVL_LOW, ptext +
                            "For given projection type, there should not be " +
                            "NULL values in fields 'Data 1' to 'Data 6'")
                    if z != 0 or d7 != 0:
                        self.tdat.errors.adderror(self.tdat.errors.E_CONDFIELD,
                            self.tdat.errors.ELVL_LOW, ptext +
                            "For given projection type, there should only be" +
                            " NULL values in fields 'Data 7' to 'Data 20'")
                # Condition 2
                if (self.tdat.tcontents['Projection type'] == self.Lookup_Projection_type(2) or
                        self.tdat.tcontents['Projection type'] == self.Lookup_Projection_type(3)):
                    if x != 5:
                        self.tdat.errors.adderror(self.tdat.errors.E_CONDFIELD,
                            self.tdat.errors.ELVL_LOW, ptext +
                            "For given projection type, there should not be " +
                            "NULL values in fields 'Data 1' to 'Data 5'")
                    if z != 0 or d7 != 0 or d6 != 0:
                        self.tdat.errors.adderror(self.tdat.errors.E_CONDFIELD,
                            self.tdat.errors.ELVL_LOW, ptext +
                            "For given projection type, there should only be" +
                            " NULL values in fields 'Data 6' to 'Data 20'")
                # Condition 3
                if self.tdat.tcontents['Projection type'] == self.Lookup_Projection_type(4):
                    if x != 5 or d6 != 1 or d7 != 1:
                        self.tdat.errors.adderror(self.tdat.errors.E_CONDFIELD,
                            self.tdat.errors.ELVL_LOW, ptext +
                            "For given projection type, there should not be " +
                            "NULL values in fields 'Data 1' to 'Data 7'")
                    if z != 0:
                        self.tdat.errors.adderror(self.tdat.errors.E_CONDFIELD,
                            self.tdat.errors.ELVL_LOW, ptext +
                            "For given projection type, there should only be" +
                            " NULL values in fields 'Data 8' to 'Data 20'")
        elif self.hdr.tablecode == self.DT_ISAR_Track_DT:
            # if field 3 is not NULL, then f4 must not be enumeration 0
            if self.TXT_NULL not in str(self.tdat.tcontents['Track ID']):
                if self.tdat.tcontents['Track type'] == self.Lookup_Track_type(0):
                    self.tdat.errors.adderror(self.tdat.errors.E_CONDFIELD,
                        self.tdat.errors.ELVL_LOW, ptext +
                        "When 'Track ID' is given, 'Track type' cannot " +
                        "be 'Unused'")
        else:
            pass  # do nothing
        return

    def check_dt_specific(self):
        """
        Check some specific fields in certain packets. Currently includes
        certain fields from:
        JPEG_Sensor_Quant
        JPEG_Sensor_Huffman
        Sensor_Grouping
        Event_Index
        """
        ptext = ("Packet " + str(self.hdr.packetnum) + "(" + self.hdr.tablename
            + ") - ")
        if self.hdr.tablecode == self.DT_JPEG_Sensor_Quant_DT:
            # can check the 1st two fields
            key1 = self.S7023_FLD_NAMES[self.DT_JPEG_Sensor_Quant_DT][0]
            key2 = self.S7023_FLD_NAMES[self.DT_JPEG_Sensor_Quant_DT][1]
            val1 = self.tdat.tcontents[key1]
            val2 = self.tdat.tcontents[key2]
            # 1) field one must have a value of FFDB
            if val1 != "FFDB":
                self.tdat.errors.adderror(self.tdat.errors.E_JPEGVALS,
                    self.tdat.errors.ELVL_LOW, ptext +
                    "DQT field must have value of FFDB (contains " + str(val1) +
                     ")")
            # 2) Field 2 should be consistent with datafilesize value
            val2comp = self.hdr.datafilesize - 2
            if val2 != val2comp:
                self.tdat.errors.adderror(self.tdat.errors.E_JPEGVALS,
                    self.tdat.errors.ELVL_LOW, ptext +
                    "Lq field must has inconsistent value (contains " +
                    str(val2) + ", expected " + str(val2comp) + ")")
        elif self.hdr.tablecode == self.DT_JPEG_Sensor_Huffman_DT:
            # can check the 1st two fields
            key1 = self.S7023_FLD_NAMES[self.DT_JPEG_Sensor_Huffman_DT][0]
            key2 = self.S7023_FLD_NAMES[self.DT_JPEG_Sensor_Huffman_DT][1]
            val1 = self.tdat.tcontents[key1]
            val2 = self.tdat.tcontents[key2]
            # 1) Field one must be FFC4
            if val1 != "FFC4":
                self.tdat.errors.adderror(self.tdat.errors.E_JPEGVALS,
                    self.tdat.errors.ELVL_LOW, ptext +
                    "DHT field must have value of FFC4 (contains " + str(val1) +
                     ")")
            # 2) Field 2 should be consistent with datafilesize value
            val2comp = self.hdr.datafilesize - 2
            if val2 != val2comp:
                self.tdat.errors.adderror(self.tdat.errors.E_JPEGVALS,
                    self.tdat.errors.ELVL_LOW, ptext +
                    "Lh field must has inconsistent value (contains " +
                    str(val2) + ", expected " + str(val2comp) + ")")
        elif self.hdr.tablecode == self.DT_Sensor_Grouping_DT:
            # 1) check that field 2 matches the number of sensors listed in the table
            key2 = self.S7023_FLD_NAMES[self.DT_Sensor_Grouping_DT][1]
            val2 = self.tdat.tcontents[key2]
            val2comp = self.hdr.datafilesize - 4
            if val2 != val2comp:
                self.tdat.errors.adderror(self.tdat.errors.E_SENGROUP,
                    self.tdat.errors.ELVL_LOW, ptext +
                    "Number of sensors given for field 2 (" + str(val2) + ")," +
                    " does not match the number of sensors in the table (" +
                    str(val2comp) + ")")
        elif self.hdr.tablecode == self.DT_Event_Index_DT:
            # 1) check if coords in field 6 is made up of one NULL and one OK value
            # NB two NULLs are allowed as field is optional
            # and obviously two non-NULL is OK
            key6 = self.S7023_FLD_NAMES[self.DT_Event_Index_DT][5]
            lat, lon = self.tdat.tcontents.get(key6, ("",""))
            errflag = 0
            if (self.TXT_NULL in str(lat) and
                self.TXT_NULL not in str(lon)):
                errflag = 1
            elif (self.TXT_NULL in str(lon) and
                self.TXT_NULL not in str(lat)):
                errflag = 1
            #
            if errflag == 1:
                #
                self.tdat.errors.adderror(self.tdat.errors.E_OPTCOORD,
                    self.tdat.errors.ELVL_LOW, ptext +
                    "Badly formed Coordinates in field 6 (one of lat or long " +
                    "is NULL)")
        return

    def check_dt_suspicious_vals(self):
        """
        Check for values flagged as suspicious in fields, storing any warnings
        in the table data error object.
        """
        ptext = ("Packet " + str(self.hdr.packetnum) + "(" + self.hdr.tablename +
            ") - Suspicious value, field: ")
        for ntypes in ['r', 'a', 'i', 'd', 'c']:
            for x, y in self.Find_Datatypes_in_Table(ntypes):
                if isinstance(y, list):
                    for i, b in enumerate(y):
                        if self.TXT_SUS_VALUE in str(b):
                            self.tdat.errors.adderror(
                                self.tdat.errors.E_SUSVALUE,
                                self.tdat.errors.ELVL_WARN, ptext + str(x) +
                                ", entry: " + str(i))
                else:
                    if self.TXT_SUS_VALUE in str(y):
                        self.tdat.errors.adderror(self.tdat.errors.E_SUSVALUE,
                            self.tdat.errors.ELVL_WARN, ptext + str(x))
        return

    # now a set of functions calculating values derived from bits of addresses
    #################################################################################

    def Calc_Requester_ID(self, tablecode=None, dfa=None):
        """
        Calculate the Requestor Index Number from the datafile address. Needs
        tablecode to determine calculation to use (if any).
        The calculation is derived from either the given tablecode & address, or
        if not given, it uses the equivalent information stored in the object.
        Returns None if not appropriate to calculate
        Returns -1 if calculated ID is out of range
        Returns -2 if unknown how to calculate (likely due to incomplete
            code update)
        """
        if tablecode is None:
            tablecode = self.hdr.tablecode

        if dfa is None:
            dfa = self.hdr.datafileaddress

        if tablecode not in self.S7023_Requester_Index_Tables or dfa is None:
            # then not appropriate to calculate
            return None

        # calculate requestor index number from dfa.
        # different tables do it in different ways
        if tablecode == self.DT_Requester_DT:
            n = (dfa & 255) - 64
        elif tablecode == self.DT_Requester_Remarks_DT:
            n = (dfa & 255) - 96
        else:
            # table is in list but don't know which method to use to calc
            # most likely means S7023_Requester_Index_Tables has been updated
            # without also updating this function
            return -2

        # check n is in valid range of 0 to 31
        if n < 0 or n > 31:
            return -1
        else:
            return n

    def Calc_Group_ID(self, tablecode=None, dfa=None):
        """
        Calculate the Group ID Number from the datafile address. Needs
        tablecode to determine calculation to use (if any).
        The calculation is derived from either the given tablecode & address, or
        if not given, it uses the equivalent information stored in the object.
        Returns None if not appropriate to calculate
        Returns -1 if calculated ID is out of range
        Returns -2 if unknown how to calculate (likely due to incomplete
            code update)
        """
        if tablecode is None:
            tablecode = self.hdr.tablecode

        if dfa is None:
            dfa = self.hdr.datafileaddress

        if tablecode not in self.S7023_Group_ID_Tables or dfa is None:
            # then not appropriate to calculate
            return None

        # calculate Group ID from dfa.
        n = dfa & 255

        # check n is in valid range of 0 to 255
        if n < 0 or n > 255:
            return -1
        else:
            return n

    def Calc_Event_ID(self, tablecode=None, dfa=None):
        """
        Calculate the Event ID Number from the datafile address. Needs
        tablecode to determine calculation to use (if any).
        The calculation is derived from either the given tablecode & address, or
        if not given, it uses the equivalent information stored in the object.
        Returns None if not appropriate to calculate
        Returns -1 if calculated ID is out of range
        Returns -2 if unknown how to calculate (likely due to incomplete
            code update)
        """
        if tablecode is None:
            tablecode = self.hdr.tablecode

        if dfa is None:
            dfa = self.hdr.datafileaddress

        if tablecode not in self.S7023_Event_ID_Tables or dfa is None:
            # then not appropriate to calculate
            return None

        # calculate Event number from dfa.
        n = dfa & 255

        # check n is in valid range of 1 to 255
        if n < 1 or n > 255:
            return -1
        else:
            return n

    def Calc_Segment_ID(self, tablecode=None, dfa=None):
        """
        Calculate the Segment ID Number from the datafile address. Needs
        tablecode to determine calculation to use (if any).
        The calculation is derived from either the given tablecode & address, or
        if not given, it uses the equivalent information stored in the object.
        Returns None if not appropriate to calculate
        Returns -1 if calculated ID is out of range
        Returns -2 if unknown how to calculate (likely due to incomplete
            code update)
        """
        if tablecode is None:
            tablecode = self.hdr.tablecode

        if dfa is None:
            dfa = self.hdr.datafileaddress

        if tablecode not in self.S7023_Segment_ID_Tables or dfa is None:
            # then not appropriate to calculate
            return None

        # calculate segment ID number from dfa.
        # different tables do it in different ways
        # (and have slightly different valid ranges)
        if tablecode in [self.DT_Segment_Index_DT, self.DT_Event_Index_DT]:
            n = (dfa >> 8) & 255
            if n < 1 or n > 255:
                return -1
        elif tablecode == self.DT_Sensor_Index_DT:
            n = dfa & 255
            if n < 0 or n > 255:
                return -1
        else:
            # table is in list but don't know which method to use to calc
            # most likely means S7023_Segment_ID_Tables has been updated
            # without also updating this function
            return -2

        # range checks already done earlier
        return n

    def Calc_Location_ID(self, tablecode=None, dfa=None):
        """
        Calculate the Location ID Number from the datafile address. Needs
        tablecode to determine calculation to use (if any).
        The calculation is derived from either the given tablecode & address, or
        if not given, it uses the equivalent information stored in the object.
        Returns None if not appropriate to calculate
        Returns -1 if calculated ID is out of range
        Returns -2 if unknown how to calculate (likely due to incomplete
            code update)
        """
        if tablecode is None:
            tablecode = self.hdr.tablecode

        if dfa is None:
            dfa = self.hdr.datafileaddress

        if tablecode not in self.S7023_Location_ID_Tables or dfa is None:
            # then not appropriate to calculate
            return None

        # calculate Location number from dfa.
        n = dfa & 15

        # check n is in valid range of 0 to 15
        if n < 0 or n > 15:
            return -1
        else:
            return n

    def Calc_Target_ID(self, tablecode=None, dfa=None):
        """
        Calculate the Target ID Number from the datafile address. Needs
        tablecode to determine calculation to use (if any).
        The calculation is derived from either the given tablecode & address, or
        if not given, it uses the equivalent information stored in the object.
        Returns None if not appropriate to calculate
        Returns -1 if calculated ID is out of range
        Returns -2 if unknown how to calculate (likely due to incomplete
            code update)
        """
        if tablecode is None:
            tablecode = self.hdr.tablecode

        if dfa is None:
            dfa = self.hdr.datafileaddress

        if tablecode not in self.S7023_Target_ID_Tables or dfa is None:
            # then not appropriate to calculate
            return None

        # calculate Target number from dfa.
        n = (dfa >> 4) & 255

        # check n is in valid range of 0 to 254
        if n < 0 or n > 254:
            return -1
        else:
            return n

    def Calc_Gimbal_ID(self, tablecode=None, dfa=None):
        """
        Calculate the Gimbal ID Number from the datafile address. Needs
        tablecode to determine calculation to use (if any).
        The calculation is derived from either the given tablecode & address, or
        if not given, it uses the equivalent information stored in the object.
        Returns None if not appropriate to calculate
        Returns -1 if calculated ID is out of range
        Returns -2 if unknown how to calculate (likely due to incomplete
            code update)
        """
        if tablecode is None:
            tablecode = self.hdr.tablecode

        if dfa is None:
            dfa = self.hdr.datafileaddress

        if tablecode not in self.S7023_Gimbal_ID_Tables or dfa is None:
            # then not appropriate to calculate
            return None

        # calculate Gimbal number from dfa.
        n = dfa & 15

        # check n is in valid range of 0 to 15
        if n < 0 or n > 15:
            return -1
        else:
            return n

    def Calc_Sensor_ID(self, tablecode=None, sa=None):
        """
        Calculate the Sensor ID Number from the source address. Needs
        tablecode to determine calculation to use (if any).
        The calculation is derived from either the given tablecode & address, or
        if not given, it uses the equivalent information stored in the object.
        Returns None if not appropriate to calculate
        Returns -1 if calculated ID is out of range
        Returns -2 if unknown how to calculate (likely due to incomplete
            code update)
        """
        if tablecode is None:
            tablecode = self.hdr.tablecode

        if sa is None:
            sa = self.hdr.sourceaddress

        if tablecode not in self.S7023_Sensor_ID_Tables or sa is None:
            # then not appropriate to calculate
            return None

        # calculate Sensor number from sa.
        n = sa & 63

        # check n is in valid range of 0 to 15
        if n < 0 or n > 63:
            return -1
        else:
            return n

    def Calc_Platform_ID(self, tablecode=None, dfa=None):
        """
        Calculate the Platform ID Number from the datafile address. Needs
        tablecode to determine calculation to use (if any).
        The calculation is derived from either the given tablecode & address, or
        if not given, it uses the equivalent information stored in the object.
        Returns None if not appropriate to calculate
        Returns -1 if calculated ID is out of range
        Returns -2 if unknown how to calculate (likely due to incomplete
            code update)
        """
        if tablecode is None:
            tablecode = self.hdr.tablecode

        if dfa is None:
            dfa = self.hdr.datafileaddress

        if tablecode not in self.S7023_Platform_ID_Tables or dfa is None:
            # then not appropriate to calculate
            return None

        # calculate Platform number from dfa.
        n = (dfa >> 16) & 255

        # check n is in valid range of 0 to 64
        if n < 0 or n > 64:
            return -1
        else:
            return n

    def Print_Table_Details(self, obuf=sys.stdout, strictcsv=False):
        """
        Print out details of a table. It includes data table fields and values
        derived from header information, but does not include any of the header
        fields themselves.
        """
        # set some format strings
        if strictcsv == False:
            pft_none = " --, {0:<47}\n"
            pft1 = " --, {0:<47} {1}\n"
            pft1n = " --, {0:<47} {1:<30}, {2}\n"
            pft2 = " --, {0:<47} {1:<14}, {2:<14}\n"
            pft2n = " --, {0:<47} {1:<14}, {2:<14}, {3}\n"
            lpft1 = " --, {0:<47} {1:<8} {2}\n"
            lpft2 = " --, {0:<47} {1:<8} {2:<14}, {3:<14}\n"
        else:
            pft_none = " --,{0}\n"
            pft1 = "--,{0}{1}\n"
            pft1n = "--,{0}{1},{2}\n"
            pft2 = "--,{0}{1},{2}\n"
            pft2n = "--,{0}{1},{2},{3}\n"
            lpft1 = "--,{0}{1}{2}\n"
            lpft2 = "--,{0}{1}{2},{3}\n"

        lnames = []
        ltypes = []
        listflags = self.tdat.fieldlflags
        names = self.tdat.fieldnames
        dtypes = self.tdat.fieldtypes

        # print the items derived from sa and dfa first
        if self.hdr.Platform_ID_Num is not None:
            obuf.write(
                pft1.format('Platform ID Number:,', self.hdr.Platform_ID_Num))
        if self.hdr.Sensor_ID_Num is not None:
            obuf.write(
                pft1.format('Sensor ID Number:,', self.hdr.Sensor_ID_Num))
        if self.hdr.Gimbal_ID_Num is not None:
            obuf.write(
                pft1.format('Gimbal ID Number:,', self.hdr.Gimbal_ID_Num))
        if self.hdr.Target_ID_Num is not None:
            obuf.write(
                pft1.format('Target ID Number:,', self.hdr.Target_ID_Num))
        if self.hdr.Location_ID_Num is not None:
            obuf.write(
                pft1.format('Location ID Number:,', self.hdr.Location_ID_Num))
        if self.hdr.Segment_ID_Num is not None:
            obuf.write(
                pft1.format('Segment ID Number:,', self.hdr.Segment_ID_Num))
        if self.hdr.Event_ID_Num is not None:
            obuf.write(
                pft1.format('Event ID Number:,', self.hdr.Event_ID_Num))
        if self.hdr.Group_ID_Num is not None:
            obuf.write(
                pft1.format('Group ID Number:,', self.hdr.Group_ID_Num))
        if self.hdr.Requester_Idx_Num is not None:
            obuf.write(
                pft1.format('Requester Index Number:,', self.hdr.Requester_Idx_Num))

        if self.hdr.tablecode == self.DT_User_Defined_DT:
            obuf.write(
                pft_none.format(
                    'Content of User Defined Table cannot be printed'))
            # print the data CRC if present
            if self.tdat.datacrc is not None:
                obuf.write(pft1.format('Data CRC:,', self.tdat.datacrc))
            # now exit function
            return

        if self.hdr.blockdataextract is True:
            # nothing after this point will have been extracted if this is set
            return

        numnames = len(names)
        j = 0  # used for navcode related data later

        if self.hdr.tablecode in self.S7023_Dynamic_Plat_Tables:
            # nav codes need to be printed on each line rather than at the end
            # as they indicate accuracy of each other entry
            numnames -= 1
            navt = names[-1]
            navtl = self.tdat.tcontents[navt]
            #
            for i in range(numnames):
                k = names[i]
                dat = self.tdat.tcontents[k]
                if dtypes[i] == 'c':  # coord
                    obuf.write(pft2n.format(k + ':,', dat[0], dat[1], navtl[j]))
                    j += 1
                else:
                    obuf.write(pft1n.format(k + ':,', dat, navtl[j]))
                    j += 1
        else:
            # all other tables
            for i in range(numnames):
                k = names[i]
                dat = self.tdat.tcontents[k]
                if listflags[i] == 0:
                    if dtypes[i] == 'c':
                        # coord
                        obuf.write(pft2.format(k + ':,', dat[0], dat[1]))
                    elif dtypes[i] == 'x':
                        # raw data - convert to hex for display
                        zzz = str(self.Conv_Hex(dat, outcap=16))
                        if len(zzz) > 31:
                            ddd = "..."
                        else:
                            ddd = ""
                        obuf.write(pft1.format(k + ':,', zzz + ddd))
                    else:
                        if isinstance(dat, list):
                            zzz = str(dat).replace(',', ';').strip('[]')
                        else:
                            zzz = dat
                        obuf.write(pft1.format(k + ':,', zzz))
                else:
                    # build up names we need to sort later
                    lnames.append(k)
                    ltypes.append(dtypes[i])
        # now handle any remaining list entries
        if self.tdat.numfieldsrepeating != 0:
            obuf.write(pft1.format
                (self.S7023_REP_ELEMENT_TEXT[self.hdr.tablecode],
                self.tdat.numrepeats))
            for i in range(self.tdat.numrepeats):
                for j in range(self.tdat.numfieldsrepeating):
                    k = lnames[j]
                    dat = self.tdat.tcontents[k][i]
                    if ltypes[j] == 'c':
                        obuf.write(
                            lpft2.format(k + ':,', '[' + str(i) + '],', dat[0], dat[1]))
                    elif ltypes[j] == 'x':
                        zzz = str(self.Conv_Hex(dat, outcap=16))
                        if len(zzz) > 31:
                            ddd = "..."
                        else:
                            ddd = ""
                        obuf.write(
                            lpft1.format(k + ':,', '[' + str(i) + '],', zzz + ddd))
                    else:
                        if isinstance(dat, list):
                            zzz = str(dat).replace(',', ';').strip('[]')
                        else:
                            zzz = dat
                        obuf.write(
                            lpft1.format(k + ':,', '[' + str(i) + '],', zzz))
        # print data crc if present
        if self.tdat.datacrc is not None:
            obuf.write(pft1.format('Data CRC:,', self.tdat.datacrc))

    def Print_Table(self, obuf=sys.stdout, detail=False, strictcsv=False, errors=False):
        """
        Print out packet header details in a csv table. If detail is True then
        table contents will also be outputted. If errors is True then
        information on any detected errors will also be printed.
        With strictcsv as False, csv output will have added spaces so that it
        is easy to read in a simple text editor, when True these extra spaces
        are omitted.
        Default output is sys.stdout, but this can be redirected using obuf.
        """
        if strictcsv == False:
            outstring = ("{0:<6}, {1:<19}, {2:<38}, {3:<4}, {4:<5}, {5:>2}, "
                "{6:>2}, {7:>2}, {8:>8}, {9:>8}, {10:>7}, {11:>9}, {12:<16}, "
                "{13:<7}\n")
        else:
            outstring = ("{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},"
                "{12},{13}\n")
        obuf.write("Table Data:\n")
        obuf.write("For flags data (F1; F2; F3) order is: Compression; CRC; "
            "Pre/Postamble ('1' indicates on; '0' indicates off)\n")
        obuf.write("DFA is Data File Address as an integer\n")
        obuf.write(outstring.format("Count", "Source", "Table", "SA", "DFA",
            "F1", "F2", "F3", "Size", "Segment", "Number", "Time Tag",
            "Sync Type", "Edition"))
        obuf.write(outstring.format(self.hdr.packetnum,
            self.SA_INFO[self.hdr.sourcecode], self.hdr.tablename,
            self.hdr.sourceaddress, self.hdr.datafileaddress,
            self.hdr.compressflag, self.hdr.crcflag, self.hdr.ambleflag,
            self.hdr.datafilesize, self.hdr.segmentnum, self.hdr.datafilenum,
            self.hdr.timetag, self.hdr.synctype, self.hdr.edition))
        if detail:
            self.Print_Table_Details(obuf=obuf, strictcsv=strictcsv)
        if errors:
            self.hdr.errors.printerrors(obuf=obuf, strictcsv=strictcsv)
            self.tdat.errors.printerrors(obuf=obuf, strictcsv=strictcsv)

    def Find_Datatypes_in_Table(self, intype):
        """
        Returns list of tuples containing field name & value for table elements
        with type intype, where intype is one of the values recognised by the
        NPIF class (e.g. 'a', 'e', 'x', etc.)
        """
        a = []
        # in case not pupulated (e.g. user defined table)
        if self.tdat.fieldtypes is not None:
            if intype in self.tdat.fieldtypes:
                # grab names and values in list of tuples
                for i, y in enumerate(self.tdat.fieldtypes):
                    if y == intype:
                        x = self.tdat.fieldnames[i]
                        a.append((x, self.tdat.tcontents[x]))
        return a


class Tablelist (NPIF):
    """
    Creates a class capable of converting, extracting and manupulating
    sets of NPIF tables. (e.g. as loaded from a file)

    Individual tables are stored as a list of Tabledata objects within this
    class.
    """
    def __init__(self):
        """
        Define a set of attributes to efficiently handle NPIF files.
        """
        self.packets = []           # list of Tabledata instances in read in order, with extracted table data
        self.packetstarts = []      # list of file byte offsets, indicating start of each 7023 packet
        self.numpackets = 0         # number of 7023 packets in file
        self.frontbytes = None      # if there is some data ahead of 1st sync code it will be stored here (string - hex values)
        self.frontbytelen = 0       # if there is some data ahead of 1st sync code its size in bytes will be here
        self.filename = ""          # filename of loaded file
        self.segmentlist = None     # list of unique segment numbers in file
        self.dataseglist = None     # list of what data segments (i.e. excludes 0 as preamble) are 'ended' in the 
                                    # file (in file order as extracted from End_Segment_Marker tables)
        self.filesize = None        # size in bytes of the loaded file
        self.errors = NPIF_Error()  # NPIF_Error object
        self.packetdict = None      # dict with keys of tablecode and values which are lists of those indices of self.packets 
                                    # with that tablecode
        self.postamblestyle = None  # integer to indicate postable style: 0= none, 1= end of each segment, 2= attached to preamble
        self.sensoridlist = []      # list of unique sensor IDs in file

    def Check_Is_7023_File(self, fname):
        """
        Given a filename, check that that file can be opened and that it looks
        like it is a 7023 file - does this by searching for an instance of the
        sync code in the first 50000 bytes of the file.
        Returns -1 if file cannot be opened
        Returns -2 if files is opened but does not look like 7023 file
        Returns 1 if able to open file and looks like 7023
        """
        try:
            mp = open(fname, 'rb')
        except IOError:
            return -1
        mstr = mp.read(50000)
        mp.close()
        fdata = mstr
        # check there is at least one occurance of the sync flag
        first = fdata.find(self.SYNC_FIELD)
        if first == -1:
            return -2
        else:
            return 1

    def Open_7023_File(self, fname, allerr=True):
        """
        Opens given filename, reads in file, breaks out the header info and
        table data on every packet.

        If allerr is False, some error checks are skipped for speed.
        """
        fcheck = self.Check_Is_7023_File(fname)

        if fcheck == -1:
            self.errors.adderror(self.errors.E_FILEOPEN,
                self.errors.ELVL_HIGH,
                "File, " + str(fname) + ", cannot be opened")
            return
        elif fcheck == -2:
            self.errors.adderror(self.errors.E_FILENOTNPIF,
                self.errors.ELVL_HIGH,
                "File, " + str(fname) + ", does not look like a 7023 file")
            return

        self.filename = os.path.abspath(fname)
        self.filesize = os.stat(fname).st_size
        mp = open(fname, 'rb')
        mstr = mp.read()
        mp.close()
        fdata = mstr
        ldata = fdata.split(self.SYNC_FIELD)
        # get position of 1st sync code
        nextstart = fdata.find(self.SYNC_FIELD)
        if nextstart != 0:
            self.frontbytes = self.Conv_Hex(ldata[0])
            self.frontbytelen = len(ldata[0])
            self.errors.adderror(self.errors.E_FRONTFILLER,
                self.errors.ELVL_WARN, str(self.frontbytelen) +
                " extra filler bytes detected at front of file (extra= " +
                str(self.frontbytes) + ")")
        # split method returns a blank list entry even if sep is at start of
        # buffer so we must discard 1st list entry whether or not sep is at
        # the start
        ldata = ldata[1:]
        count = 0
        seglist = []
        for a in ldata:
            b = Tabledata()
            b.extract_header(a, count)
            b.extract_data(b.tdat.dataraw, allerr=allerr)
            self.packetstarts.append(nextstart)
            nextstart += b.hdr.totlen
            if b.hdr.segmentnum not in seglist:
                seglist.append(b.hdr.segmentnum)
            self.packets.append(b)
            count += 1
        self.numpackets = count
        # sort segment list, just in case of odd (i.e. broken) file
        seglist.sort()
        self.segmentlist = seglist
        # 
        # Create packetdict info. This is a dict with keys of tablecode (i.e. what data table is 
        # present) and values which are lists of those packets in the file with that tablecode.
        # e.g. packetdict[self.DT_End_Segment_Marker_DT] might return [45, 176, 2068] which are
        # the indices of self.packets which contain that table type.
        # Very useful for finding particular tables
        tdict = collections.defaultdict(list)
        for p in self.packets:
            tdict[p.hdr.tablecode].append(p.hdr.packetnum)
        self.packetdict = tdict
        #
        # identify the postamble style
        self.identifypostamblestyle()
        #
        # calculate data segment list
        segp = self.packetdict[self.DT_End_Segment_Marker_DT]
        segl = []
        for p in segp:
            if self.packets[p].hdr.segmentnum != 0:
                segl.append(self.packets[p].hdr.segmentnum)
        self.dataseglist = segl
        #
        # generate list of used sensor IDs in file
        senlist = []
        for p in self.packets:
            if p.hdr.Sensor_ID_Num != None:
                if p.hdr.Sensor_ID_Num not in senlist:
                    senlist.append(p.hdr.Sensor_ID_Num)
        self.sensoridlist = senlist

    def Print_All_Tables(self, obuf=sys.stdout, detail=False, strictcsv=False, errors=False):
        """
        Print out all packet header details in a csv table. If detail is True
        then table contents for each packet will also be outputted. If errors is
        True then information on any detected errors in a particular packet will
        also be printed. This will not print any errors associated with sets of
        packets.
        With strictcsv as False, csv output will have added spaces so that it
        is easy to read in a simple text editor, when True these extra spaces
        are omitted.
        Default output is sys.stdout, but this can be redirected using obuf.
        """
        if strictcsv == False:
            outstring = ("{0:<6}, {1:<19}, {2:<38}, {3:<4}, {4:<5}, {5:>2}, "
                "{6:>2}, {7:>2}, {8:>8}, {9:>8}, {10:>7}, {11:>9}, {12:<16}, "
                "{13:<7}\n")
        else:
            outstring = ("{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},"
                "{12},{13}\n")
        obuf.write("Overview of all tables:\n")
        obuf.write("For flags data (F1; F2; F3) order is: Compression; CRC; "
            "Pre/Postamble ('1' indicates on; '0' indicates off)\n")
        obuf.write("DFA is Data File Address as an integer\n")
        obuf.write(outstring.format("Count", "Source", "Table", "SA", "DFA",
            "F1", "F2", "F3", "Size", "Segment", "Number", "Time Tag",
            "Sync Type", "Edition"))
        for t in self.packets:
            obuf.write(outstring.format(t.hdr.packetnum,
                t.SA_INFO[t.hdr.sourcecode], t.hdr.tablename,
                t.hdr.sourceaddress, t.hdr.datafileaddress,
                t.hdr.compressflag, t.hdr.crcflag, t.hdr.ambleflag,
                t.hdr.datafilesize, t.hdr.segmentnum, t.hdr.datafilenum,
                t.hdr.timetag, t.hdr.synctype, t.hdr.edition))
            if detail:
                t.Print_Table_Details(obuf=obuf, strictcsv=strictcsv)
            if errors:
                t.hdr.errors.printerrors(obuf=obuf, strictcsv=strictcsv)
                t.tdat.errors.printerrors(obuf=obuf, strictcsv=strictcsv)
        obuf.write("\n")

    def Table_Summary(self, seg=None):
        """
        Returns a dictionary with keys corresponding to tablecodes present in
        the file, and values corresponding to the number of instances of each
        table in the file.
        If seg is given, only tables with segment number = seg will be counted.
        If nothing matches, an empty dict is returned.
        """
        tdict = collections.defaultdict(lambda: 0)
        if seg is None:
            for t in self.packets:
                tdict[t.hdr.tablecode] += 1
        else:
            for t in self.packets:
                if t.hdr.segmentnum == seg:
                    tdict[t.hdr.tablecode] += 1
        return tdict

    def Print_Table_Summary(self, tdict=None, obuf=sys.stdout):
        """
        Prints the output of the Table_Summary method, passed in via tdict.
        If tdict is not given, a summary will be generated for the whole file.
        Default output is sys.stdout, but this can be redirected using obuf.
        """
        if tdict is None:
            tdict = self.Table_Summary()
        fstring = "{0:>10}, {1:<38}\n"
        obuf.write(fstring.format("Occurances", "Table Name"))
        for keys in tdict:
            obuf.write(
                fstring.format(tdict[keys], self.S7023_TABLE_NAMES[keys]))

    def Print_Basic_File_Data(self, obuf=sys.stdout):
        """
        Prints a brief summary of the contents of the NPIF file.
        Default output is sys.stdout, but this can be redirected using obuf.
        """
        obuf.write("File : {0}\n".format(self.filename))
        obuf.write(
            "File looks like it is Edition:, {0} (from 1st packet)\n".format(
            self.packets[0].hdr.edition))
        useg = self.segmentlist
        obuf.write("{0}, Segments in the File\n".format(len(useg)))
        obuf.write(
            "Segments are numbered:, {0}\n".format(str(useg).strip("[]")))
        obuf.write("The File contains, {0}, Packets\n".format(self.numpackets))
        if self.postamblestyle == 0 :
            obuf.write("Postambles do not appear to be used.\n")
        elif self.postamblestyle == 1 :
            obuf.write("Postambles appear to follow each data segment.\n")
        elif self.postamblestyle == 2 :
            obuf.write("Postamble appears to be appended to preamble.\n")
        else:
            obuf.write("Unknown Postamble usage.\n")
        obuf.write("The File contains data on {0} sensors:\n".format(
            len(self.sensoridlist)))
        obuf.write("\nThe Tables in the file are (not in order):\n")
        self.Print_Table_Summary(obuf=obuf)
        obuf.write("\nThe Tables in each segment are (not in order):\n")
        for i in useg:
            tsum = self.Table_Summary(seg=i)
            obuf.write("\nSegment, {0}\n".format(i))
            self.Print_Table_Summary(tdict=tsum, obuf=obuf)

    def file_error_checks(self):
        """
        Run a full set of file error checks on the extracted data.
        """
        self.check_total_segments()
        self.check_segment_order()
        self.check_end_seg_marks()
        self.check_end_record_mark()
        self.check_end_segment_sizes()
        self.check_compression_flag()
        self.check_datafilenumbering()
        self.check_preambleflag()
        self.check_postambleflags()
        self.check_postambletables1()
        self.check_postsegindex()
        self.check_postsenindex()
        self.check_posteventindex()
        self.check_fileeditions()
        self.check_segmentindextables()
        self.check_eventindextables()
        self.check_sensornumbersintables()
        self.check_timetagtableexists()
        self.check_sensoridtablesexist()
        self.check_dynamicplatformtables()
        self.check_sensorattitudetables()
        self.check_gimbalattitudetables()
        #
        return

    def printallerrorssorted(self, obuf=sys.stdout):
        """
        Go through all errors type-by-type through all locations and write
        them to obuf (default to sys.stdout).
        """
        for et in self.errors.ETYPES:
            breaktxt = "######################################################"
            checktxt = self.errors.ETYPES_TXT[et]
            obuf.write(breaktxt)
            obuf.write("\n")
            obuf.write(checktxt)
            obuf.write("\n")
            wcount = 0
            ecount = 0
            for n in self.packets:
                if n.hdr.errors.errorcount:
                    a, b = n.hdr.errors.printerrorsoftype(et, obuf=obuf)
                    wcount += a
                    ecount += b
                if n.tdat.errors.errorcount:
                    c, d = n.tdat.errors.printerrorsoftype(et, obuf=obuf)
                    wcount += c
                    ecount += d
            if self.errors.errorcount:
                e, f = self.errors.printerrorsoftype(et, obuf=obuf)
                wcount += e
                ecount += f
            if wcount == 0 and ecount == 0:
                obuf.write(" ... All OK.\n")
            else:
                obuf.write(str(ecount) + " Errors and " + str(wcount) +
                    " Warnings noted.\n")
        return

    def check_total_segments(self):
        """
        Checks the total number of segments in a file and populates error
        data if too many are found. Also checks that at least one end of
        segment marker exists.
        """
        # grab lists of packets that should indicate segment ends
        a = self.packetdict[self.DT_End_Segment_Marker_DT]
        b = self.packetdict[self.DT_End_Record_Marker_DT]
        c = a + b

        if len(a) == 0:
            self.errors.adderror(self.errors.E_NUMSEGMENTS,
                self.errors.ELVL_MED,
                "No End of Segment Markers detected in file")

        if len(c) > 256:
            if (len(a) == 256 and len(b) == 1 and
                self.packets[b[0]].hdr.segmentnum == 255 and
                self.packets[a[-1]].hdr.segmentnum == 255):
                # this is ok
                pass
            else:
                # otherwise there are too many segments in the file
                self.errors.adderror(self.errors.E_NUMSEGMENTS,
                    self.errors.ELVL_MED,
                    "Too many (" + str(len(c)) + ") Segments detected in file")
        # check that an end of segment table appears for each segment number
        seglist = []
        for segps in c:
            seglist.append(self.packets[segps].hdr.segmentnum)
        seglist = set(seglist)
        seglist2 = set(self.segmentlist)
        missing = list(seglist2 - seglist)
        if missing:
            self.errors.adderror(self.errors.E_NUMSEGMENTS,
                self.errors.ELVL_MED,"There are segments (numbers= " +
                str(missing) + ") without any corresponding End of " +
                "Segment/Record markers")
        return

    def check_segment_order(self):
        """
        Check that segment numbering incrementally increases through the
        file. If it drops or increases by more than 1 between adjacent packets
        it is an error
        """
        currseg = self.packets[0].hdr.segmentnum
        for d in self.packets:
            if d.hdr.segmentnum == currseg:
                pass
            else:
                if d.hdr.segmentnum == currseg + 1:
                    currseg += 1
                else:
                    self.errors.adderror(self.errors.E_SEGORDER,
                        self.errors.ELVL_LOW, "At packet, " +
                        str(d.hdr.packetnum) +
                        ", Segement number changes from, " + str(currseg) +
                        ", to, " + str(d.hdr.segmentnum))
                    # reset currseg
                    currseg = d.hdr.segmentnum
        # check also for duplicate end of segment tables
        a = self.packetdict[self.DT_End_Segment_Marker_DT]
        b = [x for x, y in collections.Counter(a).items() if y > 1]
        if b:
            self.errors.adderror(self.errors.E_SEGORDER,
                self.errors.ELVL_LOW, "Segments " + str(b) +
                ", have multiple end of Segment Markers")
        return

    def check_end_seg_marks(self):
        """
        Check that end of segment makers exist at every change of segment
        number.
        """
        currseg = self.packets[0].hdr.segmentnum
        tcode = self.packets[0].hdr.tablecode
        for d in self.packets:
            if d.hdr.segmentnum != currseg:
                # segment has changed - check if tcode is an end of segment
                # marker
                if tcode != self.DT_End_Segment_Marker_DT:
                    self.errors.adderror(self.errors.E_ENDSEGMARK,
                        self.errors.ELVL_LOW, "At packet, " +
                        str(d.hdr.packetnum) +
                        ", Segement number changes from, " + str(currseg) +
                        ", to, " + str(d.hdr.segmentnum) +
                        " and previous packet was not an End of Segment Marker")
                currseg = d.hdr.segmentnum
            tcode = d.hdr.tablecode
        return

    def check_end_record_mark(self):
        """
        Checks that End of Record Marker exists at end of file, that only one
        such table exists in file, that the segment numbering increases
        correctly relative to the penultimate packet and that the reported size
        is correct.
        """
        d = self.packets[-1]
        #
        if d.hdr.tablecode != self.DT_End_Record_Marker_DT:
            # no end of record table at end
            self.errors.adderror(self.errors.E_ENDRECMARK,
                self.errors.ELVL_LOW, "Last packet is, " +
                d.hdr.tablename + "and not an End of Record Marker")
        #
        rlist = self.packetdict[self.DT_End_Record_Marker_DT]
        if len(rlist) > 1:
            # too many end of record tables
            self.errors.adderror(self.errors.E_ENDRECMARK,
                self.errors.ELVL_LOW, "Too many End of Record Tables in \
                File. Instances found at positions: " + str(rlist))
        elif len(rlist) == 0:
            # no end of record tables
            self.errors.adderror(self.errors.E_ENDRECMARK,
                self.errors.ELVL_LOW, "No End of Record Tables in File.")
        #
        if d.hdr.tablecode == self.DT_End_Record_Marker_DT:
            p = self.packets[-2]
            if d.hdr.segmentnum != p.hdr.segmentnum + 1:
                if d.hdr.segmentnum == 255 and p.hdr.segmentnum == 255:
                    # ok - segment number 255 is a special case (max value possible)
                    pass
                else:
                    # segment numbering not correct for end of record table
                    self.errors.adderror(self.errors.E_ENDRECMARK,
                        self.errors.ELVL_LOW,
                        "End of Record table has segment number " +
                        str(d.hdr.segmentnum) +
                        ", and previous packet is numbered " +
                        str(p.hdr.segmentnum))
        # check the reported file size
        calcsize = 0
        if len(rlist) > 0:
            # only do check if such a table exists
            for p in self.packets:
                calcsize += p.hdr.claimlen # don't use totlen as it may include data outside of 7023 packets
            keyname = self.packets[rlist[-1]].tdat.fieldnames[0]
            claimsize = self.packets[rlist[-1]].tdat.tcontents[keyname]
            if claimsize != calcsize:
                # claimed and calculated size do not match
                self.errors.adderror(self.errors.E_ENDRECMARK,
                    self.errors.ELVL_LOW,
                    "End of Record Table claimed size (" + str(claimsize) +
                    " bytes) does not match measured size (" + str(calcsize) +
                    " bytes)")
        return

    def check_end_segment_sizes(self):
        """
        Checks the claimed segment sizes in the end of segment tables match
        the contents of the file. Two different size calculations are used.
        The first sums all segment packet sizes across the packet. The second
        sums all segment packet sizes up to the end of segment table. The two
        methods will have different values if the file (incorrectly) has
        additional segment packets past the end of segment table.
        """
        eseg = self.packetdict[self.DT_End_Segment_Marker_DT]
        segmarks = []
        claimsize = []
        keyname = self.S7023_FLD_NAMES[self.DT_End_Segment_Marker_DT][0]
        for p in eseg:
            segmarks.append(self.packets[p].hdr.segmentnum)
            claimsize.append(self.packets[p].tdat.tcontents[keyname])
        # now calculate sizes by passing through whole packet adding sizes of
        # matching segements. Also calculate sizes by passing through whole
        # packet and adding sizes of matching segments *if* they are also to
        # 'left' of end of segment marker
        # need to do both as some sample data does weird (and generally wrong) stuff..
        psmarks = zip(segmarks, eseg)
        sizes1 = []
        sizes2 = []
        for seg, pack in psmarks:
            sum2 = 0
            sum1 = 0
            for p in self.packets:
                if p.hdr.segmentnum == seg:
                    sum1 += p.hdr.claimlen
                    if p.hdr.packetnum <= pack:
                        sum2 += p.hdr.claimlen
            sizes1.append(sum1)
            sizes2.append(sum2)
        # now compare all
        allsiz = zip(segmarks, claimsize, sizes1, sizes2)
        for s, c, m1, m2 in allsiz:
            etxt = ("End of Segment Table for segment " + str(s) +
                    " claimed size (" + str(c) + " bytes)")
            if m1 == m2 and m1 != c:
                # reported size does not match calculated sizes
                self.errors.adderror(self.errors.E_SEGSIZES,
                    self.errors.ELVL_LOW, etxt +
                    " does not match measured size (" + str(m1) + " bytes)")
            elif c == m2 and c != m1:
                # reported size matches up to point of table but futher segment
                # packets present
                self.errors.adderror(self.errors.E_SEGSIZES,
                    self.errors.ELVL_LOW, etxt + " matches total to point" +
                    " it appears, but further Segment tables appear later " +
                    "(total size of all, " + str(m1) + " bytes)")
            elif c == m1 and c != m2:
                # reported size matches total segment tables in file, but some
                # of these are past End of Segment marker
                self.errors.adderror(self.errors.E_SEGSIZES,
                    self.errors.ELVL_LOW, etxt + " matches total in the " +
                    "file, but not the running total (" + str(m2) + " bytes)" +
                    " at the point it appears")
            elif c != m1 and c != m2 and m2 != m1:
                # claimed size does not match either measurement
                self.errors.adderror(self.errors.E_SEGSIZES,
                    self.errors.ELVL_LOW, etxt + " neither matches the " +
                    "running total at that point (" + str(m2) + " bytes), " +
                    "nor the total in the file (" + str(m1) + " bytes)")
        return

    def check_compression_flag(self):
        """
        Checks if compression flag has been set on compressed sensor data.
        """
        # look for instances of the compression table and get sensor numbers
        # from them
        sensornums = []
        comptypes = []
        keyname = self.S7023_FLD_NAMES[self.DT_Sensor_Compression_DT][0]
        #
        sclist = self.packetdict[self.DT_Sensor_Compression_DT]
        sdlist = self.packetdict[self.DT_Sensor_DT]
        for p in sclist:
            t = self.packets[p]
            if t.hdr.Sensor_ID_Num not in sensornums:
                sensornums.append(t.hdr.Sensor_ID_Num)
                comptypes.append(t.tdat.tcontents[keyname])
        # now find sensor data tables with those sensor numbers and check flag
        for p in sdlist:
            t = self.packets[p]
            if t.hdr.Sensor_ID_Num in sensornums:
                if t.hdr.compressflag != 1:
                    m = comptypes[sensornums.index(t.hdr.Sensor_ID_Num)]
                    etxt = ("Sensor Data in packet " + str(t.hdr.packetnum)
                        + " expected to be compressed (" + str(m) +
                        "), but compression flag not set")
                    self.errors.adderror(self.errors.E_COMPFLAG,
                        self.errors.ELVL_LOW, etxt)
        return

    def check_datafilenumbering(self):
        """
        Checks that data file numbering behaves as expected.
        """
        # within each segment numbering should start at zero and for each source
        # address should incrementally increase.
        # numbers can be out of order, as they represent generation rather than
        # transmission order
        # within a segment and source address, numbers can be repeated providing
        # the time tag and packet contents are identical
        # data file numbering can loop round in a segment, but this will be
        # ignored here as the minimum file sizes needed to see this happening
        # are > 150GB, and this code will not work on files that large anyway
        segsadict = {}
        for s in self.segmentlist:
            segsadict[s] = {}
        #
        for p in self.packets:
            seg = p.hdr.segmentnum
            sa = p.hdr.sourceaddress
            dfn = p.hdr.datafilenum
            pnum = p.hdr.packetnum
            if sa not in segsadict[seg]:
                segsadict[seg][sa] = []
            segsadict[seg][sa].append((dfn, pnum))
        # now have segsadict which is a dictionary with keys corresponding to
        # segment numbers. Each value itself is another dictionary, with keys
        # of sa, with values a list of dfn,pnum tuples
        # Those lists are what needs to be checked
        for s in segsadict:
            for sa in segsadict[s]:
                ll = segsadict[s][sa]
                ll.sort()
                dl, pl = zip(*ll)
                # check stuff
                etxt = ("Segment " + str(s) + ", Source Address " + str(sa) +
                    ", ")
                # check 1st one is zero
                if dl[0] != 0:
                    self.errors.adderror(self.errors.E_DFNUM,
                        self.errors.ELVL_LOW, etxt + "Data File "
                        "numbers begin at " + str(dl[0]) + " rather than 0")
                # check they increase with jumps of no more than 1
                cur = dl[0]
                for i, n in enumerate(dl):
                    if n == cur + 1:
                        cur += 1
                    elif n > cur + 1:
                        # grab a chunk of the range round the warning
                        ilow = max(0, i - 8)
                        dllen = len(dl)
                        ihigh = min(dllen, i + 8)
                        eseq = dl[ilow:ihigh]
                        self.errors.adderror(self.errors.E_DFNUM,
                            self.errors.ELVL_LOW, etxt + "Data File "
                            "number sequence has gaps e.g. subset of " +
                            str(dllen) + " elements= " + str(eseq))
                        break
                # now seek for files with identical DFNs but non identical
                # packets
                ldfn = dl[0] - 1
                lpac = pl[0]
                for d, p in ll:
                    if d == ldfn:
                        # dfn is the same so compare packets
                        p1 = self.packets[lpac]
                        p2 = self.packets[p]
                        checkcount = 0
                        if p1.hdr.timetag != p2.hdr.timetag :
                            checkcount = 1
                        elif p1.hdr.datafileaddress != p2.hdr.datafileaddress:
                            checkcount = 1
                        elif p1.hdr.datafilesize != p2.hdr.datafilesize:
                            checkcount = 1
                        elif p1.hdr.tablecode != p2.hdr.tablecode:
                            checkcount = 1
                        elif p1.tdat.fieldnames != p2.tdat.fieldnames:
                            checkcount = 1
                        elif p1.tdat.tcontents != p2.tdat.tcontents:
                            checkcount = 1
                        #
                        if checkcount:
                            self.errors.adderror(self.errors.E_DFNUM,
                                self.errors.ELVL_LOW, etxt + "Packet " +
                                str(p) + "(" + str(p2.hdr.tablename) +
                                ") has same data file number (" + str(d) +
                                ") as packet " + str(lpac) + "(" +
                                str(p1.hdr.tablename) +
                                "), but is not identical")
                    else:
                        ldfn = d
                        lpac = p
        return

    def check_preambleflag(self):
        """
        Checks that everything in Segment 0 is flagged as pre/postamble (Apart
        from EOS marker). Also checks whether preamble tables get repeated
        through the preamble, and for presence of tables not allowed in a
        preamble.
        """
        # get list of segment 0 packets
        seg0 = []
        for p in self.packets:
            if p.hdr.segmentnum == 0:
                seg0.append(p)
        #
        for p in seg0:
            if p.hdr.tablecode == self.DT_End_Segment_Marker_DT:
                if p.hdr.ambleflag == 1:
                    self.errors.adderror(self.errors.E_SEG0AMBLE,
                        self.errors.ELVL_LOW, "Packet " +
                        str(p.hdr.packetnum) + "(" + str(p.hdr.tablename) +
                        ") End of Segment Tables should not be part of the " +
                        "Preamble")
            elif p.hdr.ambleflag != 1:
                self.errors.adderror(self.errors.E_SEG0AMBLE,
                    self.errors.ELVL_LOW, "Packet " +
                    str(p.hdr.packetnum) + "(" + str(p.hdr.tablename) +
                    ") is in segment 0, but is not flagged as " +
                    "pre/postamble")
        # check there are no repeats of preamble data tables
        rptlist = []
        rptdict = {}
        for p in seg0:
            newl = (p.hdr.sourceaddress, p.hdr.datafileaddress)
            if newl not in rptlist:
                rptlist.append(newl)
            else:
                if newl in rptdict:
                    rptdict[newl][1] += 1
                else:
                    rptdict[newl] = [p.hdr.tablename, 1]
        for a in rptdict:
            s, d = a
            n = rptdict[a][0]
            c = rptdict[a][1]
            self.errors.adderror(self.errors.E_SEG0AMBLE,
                self.errors.ELVL_WARN, str(n) + "(SA=" + str(s) + " DFA=" +
                str(d) + ") packets are repeated " + str(c) + " times in " +
                "preamble. Check carefully as this is likely to be error.")
        # check that are no sensor data packets in preamble.
        for p in seg0:
            if p.hdr.sourcecode == self.SA_Platform_Data:
                # this should not be in preamble
                etxt = ("Packet " + str(p.hdr.packetnum) + " (" +
                    str(p.hdr.tablename) + ") is sensor data and should not " +
                    "be in Segment 0")
                self.errors.adderror(self.errors.E_SEG0AMBLE,
                    self.errors.ELVL_LOW, etxt)
        return

    def identifypostamblestyle(self):
        """
        Inspect index files to see what style of postamble is used (if any).
        Should be called from the file extraction routines.
        Also checks that the index tables look like they are in the correct
        places.
        """
        # postable style: 0= no postamble present, 1= end of each segment, 2= attached to preamble
        # 3 types of index files
        indseg = self.packetdict[self.DT_Segment_Index_DT]
        indsen = self.packetdict[self.DT_Sensor_Index_DT]
        indeve = self.packetdict[self.DT_Event_Index_DT]
        # also look at where postamble flagged packets are
        postsegs = []
        for p in self.packets:
            # ignore segment 0
            if p.hdr.segmentnum != 0 and p.hdr.ambleflag == 1:
                if p.hdr.segmentnum not in postsegs:
                    postsegs.append(p.hdr.segmentnum)
        #
        if len(indeve) == 0 and len(indseg) == 0 and len(indsen) == 0:
            if len(postsegs) == 0:
                # no postamble used
                self.postamblestyle = 0
                return
            else:
                # we have postambles outside segment 0 with no index tables
                self.errors.adderror(self.errors.E_INDEXAMBLE,
                    self.errors.ELVL_LOW, "Postambles " +
                    " do not contain any index tables")
                self.postamblestyle = 1
        allindex = indseg + indsen + indeve
        # check if all index files in segment 0
        seglist = []
        noflag = []
        for p in allindex:
            if self.packets[p].hdr.ambleflag == 1:
                seglist.append(self.packets[p].hdr.segmentnum)
            else:
                noflag.append(self.packets[p].hdr.segmentnum)
        #
        if len(noflag) != 0:
            # warn of presence of index tables with no flag set
            # as it might be valid...
            self.errors.adderror(self.errors.E_INDEXAMBLE,
                self.errors.ELVL_LOW, "Packets " +
                str(noflag) + " are index tables which do not have a " +
                "postamble flag set")
        if set(seglist) == set([0]) and len(postsegs) == 0 :
            # all index tables are in segment 0, and nothing flagged as
            # amble outside segment 0
            self.postamblestyle = 2
        elif set(seglist) == set([0]) and len(postsegs) != 0 :
            # have index tables in seg 0 suggesting style 2, but amble flagged
            # packets in other segments suggesting style 1
            # raise error and assume style 1
            self.postamblestyle = 1
            self.errors.adderror(self.errors.E_INDEXAMBLE,
                self.errors.ELVL_LOW, "Index tables present in Segment 0 " +
                ", implying a single postamble in Segment 0. However postamble"
                + "flagged packets are present in other Segments, implying" +
                " Postambles at end of each data Segment (assuming latter)")
        else:
            self.postamblestyle = 1
        #
        # if postable style 2, check that index tables appear at the end of
        # segment 0
        if self.postamblestyle == 2:
            allindexa = []
            for p in allindex:
                if self.packets[p].hdr.ambleflag == 1:
                    allindexa.append(p)
            seg0index = allindexa
            segp = self.packetdict[self.DT_End_Segment_Marker_DT]
            if segp[0] not in seg0index:
                seg0index.append(segp[0])
            seg0index.sort()
            minp = seg0index[0]
            maxp = seg0index[-1]
            forcast = range(minp, maxp + 1)
            delta = list(set(forcast) - set(seg0index))
            if len(delta) != 0:
                # then there are intervening packets which are non index
                etxt = ("Index tables were not all at end of Segment 0, " +
                    "intervening tables were:" + str(delta))
                self.errors.adderror(self.errors.E_INDEXAMBLE,
                    self.errors.ELVL_LOW, etxt)
        return

    def check_postambleflags(self):
        """
        Checks that the amble flag is set correctly on tables outside of
        segment 0.
        """
        # create dict with key corresponding to packets containing ambleflag=1
        # values of the segment number
        adict = {}
        for p in self.packets:
            if p.hdr.ambleflag == 1:
                adict[p.hdr.packetnum] = p.hdr.segmentnum

        if self.postamblestyle in [0, 2]:
            # check that amble flag is not set on any table outside of
            # segment zero
            plist = []
            for p, s in adict.items():
                if s != 0:
                    plist.append(p)
            if len(plist) != 0:
                self.errors.adderror(self.errors.E_POSTAMBLE,
                    self.errors.ELVL_LOW, "Packets " +
                    str(plist) + " do not appear to be in valid " +
                    "postambles (i.e. valid postambles should have index " +
                    "tables), but are flagged as postamble")
        if self.postamblestyle == 1:
            # check continuous sequence of amble flagged packets before each
            # end of segment marker
            segp = self.packetdict[self.DT_End_Segment_Marker_DT]
            segl = []
            for p in segp:
                if self.packets[p].hdr.segmentnum != 0:
                    segl.append((p,self.packets[p].hdr.segmentnum))
            for seg, pac in segl:
                seg_adict = [p for p, s in adict.items() if s == seg]
                # add the EoS packet if not flagged as postamble already
                if pac not in seg_adict:
                    seg_adict += [pac]
                seg_adict.sort()  # should already be in order, but this ensures
                minp = seg_adict[0]
                maxp = seg_adict[-1]
                seq = range(minp, maxp + 1)  # creates packet list to compare
                delta = list(set(seq) - set(seg_adict))
                if len(delta) != 0:
                    # then there are intevening packets not flagged as postamble
                    self.errors.adderror(self.errors.E_POSTAMBLE,
                        self.errors.ELVL_LOW, "Segment " + str(seg) +
                        " postamble runs from packet " + str(minp) +
                        " to packet " + str(maxp) + " but intervening packets ("
                        + str(delta) + ") are not flagged as postamble")
        return

    def check_postambletables1(self):
        """
        Checks that style 1 postambles contain the correct packets. i.e. that
        all postamble tables are either an index table, or a repeat of a
        preamble table.
        This does not check the correct index tables are present.
        """
        if self.postamblestyle == 0 or self.postamblestyle == 2:
            # no need to do any of these checks
            return
        #
        # set up data we will need
        pamble = collections.defaultdict(list)
        for p in self.packets:
            if p.hdr.ambleflag == 1:
                pamble[p.hdr.segmentnum].append(p.hdr.packetnum)
        # pamble now contains segment keys listing all amble packets
        seg0 = pamble[0]
        indexcodes = [self.DT_Segment_Index_DT, self.DT_Sensor_Index_DT,
            self.DT_Event_Index_DT]
        for skeys in pamble:
            if skeys == 0:
                continue
            for p in pamble[skeys]:
                if self.packets[p].hdr.tablecode in indexcodes:
                    continue
                else:
                    # check if it is a duplicate of something in seg 0
                    same = 0
                    for c in seg0:
                        pp = self.packets[p]
                        cc = self.packets[c]
                        if (pp.hdr.datafileaddress == cc.hdr.datafileaddress
                            and pp.hdr.sourceaddress == cc.hdr.sourceaddress
                            and pp.tdat.tcontents == cc.tdat.tcontents):
                            # is the same
                            same = 1
                            break
                    if same == 0:
                        # it is non index and not same as anything in preamble
                        # report error
                        self.errors.adderror(self.errors.E_POSTAMBLE,
                            self.errors.ELVL_LOW, "Postamble for Segment " +
                            str(skeys) + " contains packet (num= " + str(p) +
                            ", " + str(pp.hdr.tablename) + ") which is " +
                            "neither an index table nor a repeat of a " +
                            "preamble table")
        return

    def check_postsegindex(self):
        """
        Check that the correct combination of segment index files exist in each
        postamble.
        """
        if self.postamblestyle == 0:
            # nothing to do here
            return
        #
        # set up data we will need
        indseg = self.packetdict[self.DT_Segment_Index_DT]
        pamble = collections.defaultdict(list)
        for pp in indseg:
            p = self.packets[pp]
            if p.hdr.ambleflag == 1:
                s = p.hdr.segmentnum
                pamble[s].append(p.hdr.Segment_ID_Num)
        # pamble now contains segment keys listing all segment ID numbers of
        # segment index amble packets
        #
        # now forecast expected segment index tables data
        fcast = collections.defaultdict(list)
        if self.postamblestyle == 1:
            for s in self.dataseglist:
                fcast[s] = range(1,s+1)
        elif self.postamblestyle == 2:
            fcast[0] = list(self.dataseglist).sort()
        #
        # fcast contains what a correct answer should be for style 1 or 2
        for keys in fcast:
            loclist = list(pamble[keys])   # list ensures a copy
            for s in fcast[keys]:
                if s in loclist:
                    loclist.remove(s)
                else:
                    etxt = ("Missing segment " + str(s) + " index table" +
                    " within Postamble for Segment " + str(keys))
                    self.errors.adderror(self.errors.E_POSTAMBLE,
                        self.errors.ELVL_LOW, etxt)
            # check if loclist is now empty
            for s in loclist:
                # then either duplicate index tables or tables for non existent
                # segments
                if s in fcast[keys]:
                    etxt = ("Multiple segment " + str(s) + " index tables " +
                    "within Postamble for Segment " + str(keys))
                else:
                    etxt = ("Postamble for Segment " + str(keys) +
                        " includes egment index table for (non existent) " +
                        "segment, " + str(s))
                self.errors.adderror(self.errors.E_POSTAMBLE,
                    self.errors.ELVL_LOW, etxt)
        return

    def check_postsenindex(self):
        """
        Check that the correct combination of sensor index files exist in each
        postamble.
        """
        if self.postamblestyle == 0:
            # nothing to do here
            return
        #
        # set up data we will need
        indsen = self.packetdict[self.DT_Sensor_Index_DT]
        pamble = collections.defaultdict(list)
        for pp in indsen:
            p = self.packets[pp]
            if p.hdr.ambleflag == 1:
                s = p.hdr.segmentnum
                e = (p.hdr.Segment_ID_Num, p.hdr.Sensor_ID_Num)
                pamble[s].append(e)
        # pamble now contains segment keys listing all segment ID numbers and
        # sensor numbers of segment index amble packets
        #
        # work out what is supposed to be there
        sslist = []
        sencodes = [self.SA_Sensor_Data, self.SA_Sensor_Parametric_Data]
        for p in self.packets:
            if p.hdr.ambleflag == 0 and p.hdr.sourcecode in sencodes:
                cand = (p.hdr.segmentnum, p.hdr.Sensor_ID_Num)
                if cand not in sslist:
                    sslist.append(cand)
        # go through sslist and forecast
        fcast = collections.defaultdict(list)
        if self.postamblestyle == 2:
            fcast[0] = list(cand)
        elif self.postamblestyle == 1:
            for s in self.dataseglist:
                for x, y in sslist:
                    if s >= x:
                        fcast[s].append((x, y))
        #
        # fcast contains what a correct answer should be for style 1 or 2
        for keys in fcast:
            loclist = list(pamble[keys])  # list ensures a copy
            for s in fcast[keys]:
                seg, sen = s
                if s in loclist:
                    loclist.remove(s)
                else:
                    etxt = ("Missing sensor index table (for seg=" + str(seg) +
                    " sen=" + str(sen) + ") within Postamble for Segment "
                    + str(keys))
                    self.errors.adderror(self.errors.E_POSTAMBLE,
                        self.errors.ELVL_LOW, etxt)
            # check if loclist is now empty
            for s in loclist:
                # then either duplicate index tables or tables for non existent
                # segments/sensor combos
                seg, sen = s
                if s in fcast[keys]:
                    etxt = ("Multiple sensor index tables (for seg=" + str(seg)
                    + " sen=" + str(sen) + ") within Postamble for Segment "
                    + str(keys))
                else:
                    etxt = ("Postamble for Segment " + str(keys) +
                        " includes sensor index table for (non existent) " +
                        "segment-sensor combination (seg=" + str(seg) +
                        " sen=" + str(sen) + ")")
                self.errors.adderror(self.errors.E_POSTAMBLE,
                    self.errors.ELVL_LOW, etxt)
        return

    def check_posteventindex(self):
        """
        Check that the correct combination of event index files exist in each
        postamble.
        """
        if self.postamblestyle == 0:
            # nothing to do here
            return
        # set up data we will need
        indeve = self.packetdict[self.DT_Event_Index_DT]
        pamble = collections.defaultdict(list)
        for pp in indeve:
            p = self.packets[pp]
            if p.hdr.ambleflag == 1:
                s = p.hdr.segmentnum
                e = (p.hdr.Segment_ID_Num, p.hdr.Event_ID_Num)
                pamble[s].append(e)
        # pamble now contains segment keys listing all segment ID numbers and
        # event numbers of event index amble packets
        #
        # work out what events are in data
        eventps = self.packetdict[self.DT_Event_Marker_DT]
        key = self.S7023_FLD_NAMES[self.DT_Event_Marker_DT][0]
        elist = []
        for p in eventps:
            s = self.packets[p].hdr.segmentnum
            e = self.packets[p].tdat.tcontents[key]
            elist.append((s, e))
        # now forecast
        fcast = collections.defaultdict(list)
        if self.postamblestyle == 2:
            fcast[0] = list(elist)
        elif self.postamblestyle == 1:
            for s in self.dataseglist:
                for x, y in elist:
                    if s >= x:
                        fcast[s].append((x, y))
        #
        # fcast contains what a correct answer should be for style 1 or 2
        for keys in fcast:
            loclist = list(pamble[keys])   # list ensures a copy
            for s in fcast[keys]:
                seg, eve = s
                if s in loclist:
                    loclist.remove(s)
                else:
                    etxt = ("Missing event index table (for seg=" + str(seg) +
                    " event=" + str(eve) + ") within Postamble for Segment "
                    + str(keys))
                    self.errors.adderror(self.errors.E_POSTAMBLE,
                        self.errors.ELVL_LOW, etxt)
            # check if loclist is now empty
            for s in loclist:
                # then either duplicate index tables or tables for non existent
                # segments/sensor combos
                seg, eve = s
                if s in fcast[keys]:
                    etxt = ("Multiple event index tables (for seg=" + str(seg)
                    + " event=" + str(eve) + ") within Postamble for Segment "
                    + str(keys))
                else:
                    etxt = ("Postamble for Segment " + str(keys) +
                        " includes event index table for (non existent) " +
                        "segment-event combination (seg=" + str(seg) +
                        " event=" + str(eve) + ")")
                self.errors.adderror(self.errors.E_POSTAMBLE,
                    self.errors.ELVL_LOW, etxt)
        return

    def check_fileeditions(self):
        """
        Checks that a consistent Edition number is used through the file.
        """
        edarray = []
        for p in self.packets:
            if p.hdr.edition not in edarray:
                edarray.append(p.hdr.edition)
        if len(edarray) > 1:
            # give warning
            etxt = "Mix of claimed Edition numbers in file: " + str(edarray)
            self.errors.adderror(self.errors.E_EDITION,
                self.errors.ELVL_WARN, etxt)

    def check_segmentindextables(self):
        """
        Check the contents of any segment index tables as far as possible.
        """
        segindextabs = self.packetdict[self.DT_Segment_Index_DT]
        key1 = self.S7023_FLD_NAMES[self.DT_Segment_Index_DT][0]
        key2 = self.S7023_FLD_NAMES[self.DT_Segment_Index_DT][1]
        key5 = self.S7023_FLD_NAMES[self.DT_Segment_Index_DT][4]
        key6 = self.S7023_FLD_NAMES[self.DT_Segment_Index_DT][5]

        for si in segindextabs:
            pp = self.packets[si]
            ptext = ("Packet " + str(pp.hdr.packetnum) + "(" +
                pp.hdr.tablename + ") - ")
            # read in table values from segment index table
            val1 = pp.tdat.tcontents[key1] # start offset
            val2 = pp.tdat.tcontents[key2] # end offset
            val5 = pp.tdat.tcontents[key5] # start timetag
            val6 = pp.tdat.tcontents[key6] # end timetag
            seg = pp.hdr.Segment_ID_Num
            # find first header in segment and extract time tag and file offset
            for p in self.packets:
                if p.hdr.segmentnum == seg:
                    first = p.hdr.packetnum
                    tt = p.hdr.timetag
                    break
            startoff = self.packetstarts[first] - self.frontbytelen
            # compare extracted values with declared values in segment index table
            if startoff != val1:
                # declared value does not match file content for start offset
                etxt = ("Field 1, Start of data segment value (" + str(val1)
                    + ") does not match calculated value (" + str(startoff) +
                    ")")
                self.errors.adderror(self.errors.E_SEGINDEX,
                    self.errors.ELVL_LOW, ptext + etxt)
            if tt != val5:
                # declared value does not match file content for start timetag
                etxt = ("Field 5, Start Header Time Tag (" + str(val5)
                    + ") does not match calculated value (" + str(tt) + ")")
                self.errors.adderror(self.errors.E_SEGINDEX,
                    self.errors.ELVL_LOW, ptext + etxt)
            # find last header in seg
            for p in reversed(self.packets):
                # need to ignore postable and End of Segment tables in this calculation
                if p.hdr.segmentnum == seg and p.hdr.ambleflag == 0:
                    if p.hdr.tablecode != self.DT_End_Segment_Marker_DT:
                        last = p.hdr.packetnum
                        tt = p.hdr.timetag
                        plen = p.hdr.claimlen
                        break
            endoff = self.packetstarts[last] - self.frontbytelen + plen
            if endoff != val2:
                # declared value does not match file content for end offset
                etxt = ("Field 2, End of data segment value (" + str(val2)
                    + ") does not match calculated value (" + str(endoff) +
                    ")")
                self.errors.adderror(self.errors.E_SEGINDEX,
                    self.errors.ELVL_LOW, ptext + etxt)
            if tt != val6:
                # declared value does not match file content for end timetag
                etxt = ("Field 6, End Header Time Tag (" + str(val6)
                    + ") does not match calculated value (" + str(tt) + ")")
                self.errors.adderror(self.errors.E_SEGINDEX,
                    self.errors.ELVL_LOW, ptext + etxt)
            # unsure how to calculate any other values for comparison
        return

    def check_eventindextables(self):
        """
        Check the contents of any event index tables as far as possible.
        """
        # get indices of relevant tables
        eveindextabs = self.packetdict[self.DT_Event_Index_DT]
        emarkertabs = self.packetdict[self.DT_Event_Marker_DT]
        # get relevant keys for index
        key1 = self.S7023_FLD_NAMES[self.DT_Event_Index_DT][0] # event type
        key2 = self.S7023_FLD_NAMES[self.DT_Event_Index_DT][1] # target number
        key4 = self.S7023_FLD_NAMES[self.DT_Event_Index_DT][3] # timetag
        key7 = self.S7023_FLD_NAMES[self.DT_Event_Index_DT][6] # primary sensor number
        key8 = self.S7023_FLD_NAMES[self.DT_Event_Index_DT][7] # secondary sensor number
        key9 = self.S7023_FLD_NAMES[self.DT_Event_Index_DT][8] # tertiary sensor number
        key10 = self.S7023_FLD_NAMES[self.DT_Event_Index_DT][9] # event file offset
        # get keys for marker
        mkey1 = self.S7023_FLD_NAMES[self.DT_Event_Marker_DT][0] # event number
        mkey2 = self.S7023_FLD_NAMES[self.DT_Event_Marker_DT][1] # event type
        mkey3 = self.S7023_FLD_NAMES[self.DT_Event_Marker_DT][2] # primary sensor number
        mkey4 = self.S7023_FLD_NAMES[self.DT_Event_Marker_DT][3] # secondary sensor number
        mkey5 = self.S7023_FLD_NAMES[self.DT_Event_Marker_DT][4] # tertiary sensor number
        mkey6 = self.S7023_FLD_NAMES[self.DT_Event_Marker_DT][5] # target number
        #
        # for each event index table extract info and run through event markers to find matching info
        # report any discrepencies
        for si in eveindextabs:
            pp = self.packets[si]
            ptext = ("Packet " + str(pp.hdr.packetnum) + "(" +
                pp.hdr.tablename + ") - ")
            # read in index table values
            val1 = pp.tdat.tcontents[key1]
            val2 = pp.tdat.tcontents[key2]
            val4 = pp.tdat.tcontents[key4]
            val7 = pp.tdat.tcontents[key7]
            val8 = pp.tdat.tcontents[key8]
            val9 = pp.tdat.tcontents[key9]
            val10 = pp.tdat.tcontents[key10]
            sn = pp.hdr.Segment_ID_Num
            en = pp.hdr.Event_ID_Num
            # find appropriate event in marker tables
            for p in emarkertabs:
                qq = self.packets[p]
                mval1 = qq.tdat.tcontents[mkey1]
                if qq.hdr.segmentnum == sn and mval1 == en:
                    # this should be the correct event, extact values and compare
                    mval2 = qq.tdat.tcontents[mkey2]
                    mval3 = qq.tdat.tcontents[mkey3]
                    mval4 = qq.tdat.tcontents[mkey4]
                    mval5 = qq.tdat.tcontents[mkey5]
                    mval6 = qq.tdat.tcontents[mkey6]
                    tt = qq.hdr.timetag
                    epos = self.packetstarts[p] - self.frontbytelen
                    if val1 != mval2:
                        etxt = ("Field 1, Event type (" + str(val1)
                            + ") does not match corresponding value in Event " +
                            "marker table (" + str(mval2) + ")")
                        self.errors.adderror(self.errors.E_EVENTINDEX,
                            self.errors.ELVL_LOW, ptext + etxt)
                    if val2 != mval6:
                        etxt = ("Field 2, Target Number (" + str(val2)
                            + ") does not match corresponding value in Event " +
                            "marker table (" + str(mval6) + ")")
                        self.errors.adderror(self.errors.E_EVENTINDEX,
                            self.errors.ELVL_LOW, ptext + etxt)
                    if val7 != mval3:
                        etxt = ("Field 7, Primary Sensor Number (" + str(val7)
                            + ") does not match corresponding value in Event " +
                            "marker table (" + str(mval3) + ")")
                        self.errors.adderror(self.errors.E_EVENTINDEX,
                            self.errors.ELVL_LOW, ptext + etxt)
                    if val8 != mval4:
                        etxt = ("Field 8, Secondary Sensor Number (" + str(val8)
                            + ") does not match corresponding value in Event " +
                            "marker table (" + str(mval4) + ")")
                        self.errors.adderror(self.errors.E_EVENTINDEX,
                            self.errors.ELVL_LOW, ptext + etxt)
                    if val9 != mval5:
                        etxt = ("Field 9, Third Sensor Number (" + str(val9)
                            + ") does not match corresponding value in Event " +
                            "marker table (" + str(mval5) + ")")
                        self.errors.adderror(self.errors.E_EVENTINDEX,
                            self.errors.ELVL_LOW, ptext + etxt)
                    if val4 != tt:
                        etxt = ("Field 4, Time Tag (" + str(val4)
                            + ") does not match calculated value (" +
                            str(tt) + ")")
                        self.errors.adderror(self.errors.E_EVENTINDEX,
                            self.errors.ELVL_LOW, ptext + etxt)
                    if val10 != epos:
                        etxt = ("Field 10, Event Position (" + str(val10)
                            + ") does not match calculated value (" +
                            str(epos) + ")")
                        self.errors.adderror(self.errors.E_EVENTINDEX,
                            self.errors.ELVL_LOW, ptext + etxt)
        return

    def check_sensornumbersintables(self):
        """
        For those tables which have fields referring to sensor numbers, checks
        that those given numbers correspond to sensors that exist in the file.
        Includes checks on the following tables:
        Sensor Grouping
        Event Marker
        Event Index
        Virtual Sensor Definition
        """
        sengrptabs = self.packetdict[self.DT_Sensor_Grouping_DT]
        evemrktabs = self.packetdict[self.DT_Event_Marker_DT]
        eveindtabs = self.packetdict[self.DT_Event_Index_DT]
        virtsentabs = self.packetdict[self.DT_Virtual_Sensor_Def_DT]

        for p in sengrptabs:
            # is a list with multiple items
            key = self.S7023_FLD_NAMES[self.DT_Sensor_Grouping_DT][4]
            vals = self.packets[p].tdat.tcontents[key]
            qq = self.packets[p]
            ptext = ("Packet " + str(qq.hdr.packetnum) + "(" +
                qq.hdr.tablename + ") - ")
            for i, s in enumerate(vals):
                if s not in self.sensoridlist:
                    etxt = ("Field " + str(i+5) + ", Sensor Number, " + str(s)
                        + ", is not a valid sensor number for this record")
                    self.errors.adderror(self.errors.E_SENSORNUM,
                        self.errors.ELVL_LOW, ptext + etxt)
        #
        for p in evemrktabs:
            # 3 number in table
            key3 = self.S7023_FLD_NAMES[self.DT_Event_Marker_DT][2]
            key4 = self.S7023_FLD_NAMES[self.DT_Event_Marker_DT][3]
            key5 = self.S7023_FLD_NAMES[self.DT_Event_Marker_DT][4]
            qq = self.packets[p]
            val3 = qq.tdat.tcontents[key3]
            val4 = qq.tdat.tcontents[key4]
            val5 = qq.tdat.tcontents[key5]
            vals = [val3, val4, val5]
            ptext = ("Packet " + str(qq.hdr.packetnum) + "(" +
                qq.hdr.tablename + ") - ")
            for i, s in enumerate(vals):
                if s not in self.sensoridlist:
                    etxt = ("Field " + str(i+3) + ", Sensor Number, " + str(s)
                        + ", is not a valid sensor number for this record")
                    self.errors.adderror(self.errors.E_SENSORNUM,
                        self.errors.ELVL_LOW, ptext + etxt)
        #
        for p in eveindtabs:
            # 3 numbers in table
            key7 = self.S7023_FLD_NAMES[self.DT_Event_Index_DT][6]
            key8 = self.S7023_FLD_NAMES[self.DT_Event_Index_DT][7]
            key9 = self.S7023_FLD_NAMES[self.DT_Event_Index_DT][8]
            qq = self.packets[p]
            val7 = qq.tdat.tcontents[key7]
            val8 = qq.tdat.tcontents[key8]
            val9 = qq.tdat.tcontents[key9]
            vals = [val7, val8, val9]
            ptext = ("Packet " + str(qq.hdr.packetnum) + "(" +
                qq.hdr.tablename + ") - ")
            for i, s in enumerate(vals):
                if s not in self.sensoridlist:
                    etxt = ("Field " + str(i+7) + ", Sensor Number, " + str(s)
                        + ", is not a valid sensor number for this record")
                    self.errors.adderror(self.errors.E_SENSORNUM,
                        self.errors.ELVL_LOW, ptext + etxt)
        #
        for p in virtsentabs:
            # 4 numbers in table - 65535 is possible entry meaning not in use
            key3 = self.S7023_FLD_NAMES[self.DT_Virtual_Sensor_Def_DT][2]
            key4 = self.S7023_FLD_NAMES[self.DT_Virtual_Sensor_Def_DT][3]
            key5 = self.S7023_FLD_NAMES[self.DT_Virtual_Sensor_Def_DT][4]
            key6 = self.S7023_FLD_NAMES[self.DT_Virtual_Sensor_Def_DT][5]
            qq = self.packets[p]
            val3 = qq.tdat.tcontents[key3]
            val4 = qq.tdat.tcontents[key4]
            val5 = qq.tdat.tcontents[key5]
            val6 = qq.tdat.tcontents[key6]
            vals = [val3, val4, val5, val6]
            ptext = ("Packet " + str(qq.hdr.packetnum) + "(" +
                qq.hdr.tablename + ") - ")
            for i, s in enumerate(vals):
                if s not in self.sensoridlist and s != self.TXT_NOTINUSE:
                    etxt = ("Field " + str(i+3) + ", Sensor Number, " + str(s)
                        + ", is not a valid sensor number for this record")
                    self.errors.adderror(self.errors.E_SENSORNUM,
                        self.errors.ELVL_LOW, ptext + etxt)
        #
        return

    def check_timetagtableexists(self):
        """
        Checks whether a Format Time Tag Data Table exists in the preamble
        and warns if it does not.

        Later headers cannot be fully understood if this table does not exist,
        though its existence is not mandatory within the standard.
        """
        tttabs = self.packetdict[self.DT_Format_Time_Tag_DT]
        if len(tttabs) == 0:
            # none exist in file
            etxt = ("No Format Time Tag Tables exist in the Record")
            self.errors.adderror(self.errors.E_TIMETAG,
                self.errors.ELVL_WARN, etxt)
            return
        ambleexist = 0
        for p in tttabs:
            if self.packets[p].hdr.segmentnum == 0:
                if self.packets[p].hdr.ambleflag == 1:
                    ambleexist = 1
                    break
        if not ambleexist:
            etxt = ("No Format Time Tag Tables exist in the Preamble")
            self.errors.adderror(self.errors.E_TIMETAG,
                self.errors.ELVL_WARN, etxt)
        return

    def check_sensoridtablesexist(self):
        """
        Checks if sensor ID tables exist for each sensor ID number identified
        in record.
        """
        idtabs = self.packetdict[self.DT_Sensor_ID_DT]
        senlist = list(self.sensoridlist)
        senlist0 = list(self.sensoridlist)
        for p in idtabs:
            qq = self.packets[p]
            if qq.hdr.Sensor_ID_Num in senlist:
                senlist.remove(qq.hdr.Sensor_ID_Num)
                if qq.hdr.segmentnum == 0:
                    senlist0.remove(qq.hdr.Sensor_ID_Num)
        if len(senlist0):
            etxt = ("Sensor IDs" + str(senlist0) + "do not have a Sensor " +
                "Identification table in the preamble")
            self.errors.adderror(self.errors.E_SENSORNUM,
                self.errors.ELVL_WARN, etxt)
        if len(senlist):
            etxt = ("Sensor IDs" + str(senlist0) + "do not have a Sensor " +
                "Identification table in the record")
            self.errors.adderror(self.errors.E_SENSORNUM,
                self.errors.ELVL_WARN, etxt)
        return

    def check_dynamicplatformtables(self):
        """
        Checks that, for a given platform ID, only one of the comprehensive or
        minimum dynamic platform tables are used.

        Also will warn if neither are used
        """
        comptabs = self.packetdict[self.DT_Comp_Dynamic_Plat_DT]
        mintabs = self.packetdict[self.DT_Min_Dynamic_Plat_DT]
        if len(comptabs) == 0 and len(mintabs) == 0:
            etxt = ("There are no Dynamic Platform tables in the record")
            self.errors.adderror(self.errors.E_DYNAMICTABS,
                self.errors.ELVL_WARN, etxt)
            return
        # calculate dicts with platform IDs as keys
        mindict = collections.defaultdict(list)
        compdict = collections.defaultdict(list)
        for p in mindict:
            pidn = self.packets[p].hdr.Platform_ID_Num
            mindict[pidn].append(p)
        for p in compdict:
            pidn = self.packets[p].hdr.Platform_ID_Num
            compdict[pidn].append(p)
        #
        commonids = set(mindict) & set(compdict)
        for i in commonids:
            etxt = ("Platform ID, " + str(i) + " Uses both Comprehensive and" +
                " Minimum Dynamic Platform Tables")
            self.errors.adderror(self.errors.E_DYNAMICTABS,
                self.errors.ELVL_LOW, etxt)
        return

    def check_sensorattitudetables(self):
        """
        Checks that, for a given sensor ID, only one of the comprehensive or
        minimum sensor attitude tables are used.

        Also will warn if neither are used.
        """
        comptabs = self.packetdict[self.DT_Comp_Sensor_Att_DT]
        mintabs = self.packetdict[self.DT_Min_Sensor_Att_DT]
        if len(comptabs) == 0 and len(mintabs) == 0:
            etxt = ("There are no Sensor Attitude tables in the record")
            self.errors.adderror(self.errors.E_SENATTTABS,
                self.errors.ELVL_WARN, etxt)
            return
        # calculate dicts with sensor IDs as keys
        mindict = collections.defaultdict(list)
        compdict = collections.defaultdict(list)
        for p in mindict:
            pidn = self.packets[p].hdr.Sensor_ID_Num
            mindict[pidn].append(p)
        for p in compdict:
            pidn = self.packets[p].hdr.Sensor_ID_Num
            compdict[pidn].append(p)
        #
        commonids = set(mindict) & set(compdict)
        for i in commonids:
            etxt = ("Sensor ID, " + str(i) + " uses both Comprehensive and" +
                " Minimum Sensor Attitude Tables")
            self.errors.adderror(self.errors.E_SENATTTABS,
                self.errors.ELVL_LOW, etxt)
        return

    def check_gimbalattitudetables(self):
        """
        Checks that, for a given sensor ID, only one of the comprehensive or
        minimum Gimbal attitude tables are used.
        """
        # unlike with the dymanic platform and sensor attitude tables
        # do not warn about no use of either - it is possible to describe
        # sensor views without useage of gimbals tables
        #
        # calculate dicts with sensor IDs as keys, but also need gimbal ID
        mindict = collections.defaultdict(list)
        compdict = collections.defaultdict(list)
        for p in mindict:
            sidn = self.packets[p].hdr.Sensor_ID_Num
            gidn = self.packets[p].hdr.Gimbal_ID_Num
            mindict[sidn].append(gidn)
        for p in compdict:
            sidn = self.packets[p].hdr.Sensor_ID_Num
            gidn = self.packets[p].hdr.Gimbal_ID_Num
            compdict[sidn].append(gidn)
        #
        commonids = set(mindict) & set(compdict)
        for i in commonids:
            # also unpick by Gimbal ID
            ming = mindict[i]
            compg = compdict[i]
            commongimb = set(ming) & set(compg)
            for j in commongimb:
                etxt = ("Sensor ID, " + str(i) + ", Gimbal ID, " + str(j) +
                     " uses both Comprehensive and Minimum Gimbal Attitude" +
                     " Tables")
                self.errors.adderror(self.errors.E_GIMBALTABS,
                    self.errors.ELVL_LOW, etxt)
        return

def Do_7023_Full(fname):
    """
    Runs a standard set of functions on an input file name string.

    Mostly used in testing/development, but also gives an idea of how to string
    code together.
    """
    # Create Tablelist Object
    a = Tablelist()
    # get filename with no extension on the end
    noext = os.path.splitext(fname)[0]
    # make names for output files
    summaryout = noext + '_summary.txt'
    tablesout = noext + '_tables.csv'
    testsout = noext + '_tests.txt'
    #
    # open output files for writing
    sout = open(summaryout, 'w')
    tabout = open(tablesout, 'w')
    tstout = open(testsout, 'w')
    #
    # read in the file
    a.Open_7023_File(fname)
    # add contents to 1st output file (summary)
    a.Print_Basic_File_Data(obuf=sout)
    sout.close()
    # add contents to 2nd output file (csv detail)
    a.Print_All_Tables(obuf=tabout, detail=True, strictcsv=True)
    #a.Print_All_Tables(obuf=tabout, detail=False, strictcsv=True)
    tabout.close()
    # add contents to 3rd output file (simple analysis)
    a.file_error_checks()
    a.printallerrorssorted(obuf=tstout)
    tstout.close()
    #
