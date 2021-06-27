#!/usr/bin/env python3

import unittest

import  sys
from    p3lib.conduit import Conduit

class ConduitTester(unittest.TestCase):
    """@brief Test cases for the Conduit class"""

    def setUp(self):
        self.conduit = Conduit()

    def tearDown(self):
        pass

    def test1_AToB(self):
        msg = "test1_AToB_Message"
        self.conduit.putA(msg)

        self.assertTrue( self.conduit.bReadAvailable() )
        
        rxMsg = self.conduit.getB()
        self.assertTrue( msg == rxMsg)

    def test1_BToA(self):
        msg = "test1_BToA_Message"
        self.conduit.putB(msg)

        self.assertTrue( self.conduit.aReadAvailable() )
        
        rxMsg = self.conduit.getA()
        self.assertTrue( msg == rxMsg)
        
def main():
    """@brief Unit tests for the UIO class"""
    suite = unittest.TestLoader().loadTestsFromTestCase(ConduitTester)
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    main()
