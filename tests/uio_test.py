#!/usr/bin/env python3

import unittest

import  sys
from    p3lib.uio import UIO

SYSLOG_SERVER = "192.168.0.8"

class UIOTester(unittest.TestCase):
    """@brief Unit tests for the UIO class"""

    #!!! This is not thread safe. Only one instance on a single machine.
    TMP_FILE = "/tmp/redirect.txt"

    @staticmethod
    def GetStdoutLines():
        fd = open(UIOTester.TMP_FILE, 'r')
        lines = fd.readlines()
        fd.close()
        return lines

    def setUp(self):
        self._uio = UIO(colour=False)
        if SYSLOG_SERVER:
            self._uio.enableSyslog(True, host=SYSLOG_SERVER)
        self._orgStdout = None

    def tearDown(self):
        pass

    def _grabStdOut(self):
        self._orgStdout = sys.stdout
        sys.stdout = open(UIOTester.TMP_FILE, 'w')

    def _restoreStdout(self):
        sys.stdout.close()
        sys.stdout = self._orgStdout

    def _grabStdIn(self):
        self._orgStdin = sys.stdin
        sys.stdin = open(UIOTester.TMP_FILE, 'r')

    def _setTmpText(self, text):
        fd = open(UIOTester.TMP_FILE, 'w')
        fd.write(text)
        fd.close()

    def _restoreStdin(self):
        sys.stdin.close()
        sys.stdin = self._orgStdin

    def test0_info(self):
        self._uio = UIO(debug=True, colour=True)
        self._uio.info("An info level message")
        self._uio.warn("An warn level message")
        self._uio.error("An error level message")
        self._uio.debug("An debug level message")

    def test1_info(self):
        self._grabStdOut()
        self._uio.info("An info level message")
        self._restoreStdout()

        lines = UIOTester.GetStdoutLines()
        self.assertTrue(len(lines) == 1)
        self.assertTrue( lines[0] == "INFO:  An info level message\n")

    def test2_warn(self):
        self._grabStdOut()
        self._uio.warn("An warn level message")
        self._restoreStdout()

        lines = UIOTester.GetStdoutLines()
        self.assertTrue(len(lines) == 1)
        self.assertTrue( lines[0] == "WARN:  An warn level message\n")

    def test3_error(self):
        self._grabStdOut()
        self._uio.error("An error level message")
        self._restoreStdout()

        lines = UIOTester.GetStdoutLines()
        self.assertTrue(len(lines) == 1)
        self.assertTrue( lines[0] == "ERROR: An error level message\n")

    def test4_debugOff(self):
        self._grabStdOut()
        self._uio.enableDebug(False)
        self._uio.debug("An debug level message")
        self._restoreStdout()

        lines = UIOTester.GetStdoutLines()
        self.assertTrue(len(lines) == 0)

    def test5_debugOn(self):
        self._grabStdOut()
        self._uio.enableDebug(True)
        self._uio.debug("A debug level message")
        self._restoreStdout()

        lines = UIOTester.GetStdoutLines()
        self.assertTrue(len(lines) == 1)
        self.assertTrue(lines[0] == "DEBUG: A debug level message\n")

    def test6_getInput(self):
        self._setTmpText("0123456789\n")

        self._grabStdIn()
        self._uio.getInput("Enter a string")
        self._restoreStdin()

        lines = UIOTester.GetStdoutLines()
        self.assertTrue(len(lines) == 1)
        self.assertTrue(lines[0] == "0123456789\n")

    def test7_getBoolInput_y(self):
        self._setTmpText("y\n")

        self._grabStdIn()
        response = self._uio.getBoolInput("Enter y/n")
        self._restoreStdin()

        self.assertTrue( response )

    def test7_getBoolInput_n(self):
        self._setTmpText("n\n")

        self._grabStdIn()
        response = self._uio.getBoolInput("Enter y/n")
        self._restoreStdin()

        self.assertTrue( not response )

    def test8_getBoolInput_q(self, allowQuit=True):
        self._setTmpText("q\n")

        try:
            self._grabStdIn()
            self._uio.getBoolInput("Enter y/n or q")
            raise Exception("SystemExit not raised")

        except SystemExit:
            self._restoreStdin()

    def test9_errorException(self):
        self._uio.enableDebug(True)
        self._grabStdOut()

        try:
            raise Exception("An error occurred")

        except Exception:
            self._uio.errorException()
            self._restoreStdout()
            lines = UIOTester.GetStdoutLines()
            self.assertTrue(len(lines) == 5)

            self.assertTrue(lines[0] == "ERROR: Traceback (most recent call last):\n")
            #Not checking for exact text here as line numbers may change in uio.py as it's updated over time.
            self.assertTrue( lines[1].find("uio_test.py") != -1 and lines[1].endswith(", in test9_errorException\n") )
            self.assertTrue(lines[2] == "ERROR:     raise Exception(\"An error occurred\")\n")
            self.assertTrue(lines[3] == "ERROR: Exception: An error occurred\n")
            self.assertTrue(lines[4] == "ERROR: \n")
            
    def test10_table(self):
        print("\n")
        table = []
        table.append(["Col 1", "Col 2"])
        table.append(["awfdasdfgsd", "afesdgfsdgfsdfgsdf"])
        table.append(["1", "2"])
        table.append(["AAA", "BBB"])
        self._uio.showTable(table, rowSeparatorChar="~", colSeparatorChar="!")
        
        table = []
        table.append(["Col 1", "Col 2", "Col 3"])
        table.append(["awfdasdfgsd", "afesdgfsdgfsdfgsdf", "sdf9we908r23m4r2398"])
        table.append(["1", "2", "3"])
        table.append(["AAA", "BBB", "CCC"])
        self._uio.showTable(table)
        
    #!!! getPassword() not tested as redirect does not work.

def main():
    """@brief Unit tests for the UIO class"""
    suite = unittest.TestLoader().loadTestsFromTestCase(UIOTester)
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    main()
