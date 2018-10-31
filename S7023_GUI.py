#-------------------------------------------------------------------------------
# Name:         S7023_GUI
# Purpose:      functions to support GUI use with 7023 code
#
# Author:      sfhelsdon-dstl
# Originally Created:     02/07/2013
# 
#############################################################################
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
"""
Simple GUI functions to support NPIF code.
"""

import tkinter
import tkinter.filedialog
import tkinter.messagebox

def Get7023_Filename () :
    """
    Trivial function to use a file dialog to get and return a file name.
    """
    tkinter.Tk().withdraw()
    filename = tkinter.filedialog.askopenfilename()
    return filename

def Do7023_ErrorBox (txt) :
    """
    Trivial function to give an error message in a window.
    """
    tkinter.Tk().withdraw()
    tkinter.messagebox.showerror("Error",txt)

def main():
    pass

if __name__ == '__main__':
    main()
