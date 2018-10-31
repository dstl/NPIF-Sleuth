This folder contains some test code and some data to help test.

The NPIF Testdata.py file can generate the test datasets in this folder, if needed. 
It relies on the 7023 "Golden Files" which are have to be distributed separately by the owner of the standard.

The NPIF Test.py has the actual tests. Some of these also rely on the 7023 "Golden 
Files" (all the test methods in the final class).

quick summary of the other files:
test.7023 - contains single instance of each 7023 table. Values are certainly not 
			self consistent or always sensible, but should have sensible structure
test2.7023 - basically a dud file with no actual 7023 data in it
test3.7023 - just has a few repeated table sets.
testPrint* - this set has sample of formatted output based on test.7023

 