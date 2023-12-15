#!/usr/bin/env python3
import os
import unittest

from    p3lib.bokeh_auth import CredentialsHasher


class CredentialsHasherTester(unittest.TestCase):
    """@brief Unit tests for the UIO class"""

    #!!! This is not thread safe. Only one instance on a single machine.
    HASH_FILE = "/tmp/credentials.json"

    USERNAME1 = "ausername"
    PASSWORD1 = "apassword"

    USERNAME2 = "ausername1"
    PASSWORD2 = "apassword1"

    USERNAME3 = "ausername2"
    PASSWORD3 = "apassword2"

    def setUp(self):
        if os.path.isfile(CredentialsHasherTester.HASH_FILE):
            os.remove(CredentialsHasherTester.HASH_FILE)
        self._credentialsHasher = CredentialsHasher(CredentialsHasherTester.HASH_FILE)

    def test0_add_hash(self):
        self._credentialsHasher.add(CredentialsHasherTester.USERNAME1, CredentialsHasherTester.PASSWORD1)

    def test1_hash_valid(self):
        self._credentialsHasher.add(CredentialsHasherTester.USERNAME1, CredentialsHasherTester.PASSWORD1)
        assert self._credentialsHasher.verify(CredentialsHasherTester.USERNAME1, CredentialsHasherTester.PASSWORD1) is True

    def test2_hash_invalid(self):
        self._credentialsHasher.add(CredentialsHasherTester.USERNAME1, CredentialsHasherTester.PASSWORD1)
        assert self._credentialsHasher.verify(CredentialsHasherTester.USERNAME1, CredentialsHasherTester.PASSWORD1+"X") is False
        
    def test3_hashes_valid(self):
        self._credentialsHasher.add(CredentialsHasherTester.USERNAME1, CredentialsHasherTester.PASSWORD1)
        self._credentialsHasher.add(CredentialsHasherTester.USERNAME2, CredentialsHasherTester.PASSWORD2)
        self._credentialsHasher.add(CredentialsHasherTester.USERNAME3, CredentialsHasherTester.PASSWORD3)
        assert self._credentialsHasher.verify(CredentialsHasherTester.USERNAME1, CredentialsHasherTester.PASSWORD1) is True
        assert self._credentialsHasher.verify(CredentialsHasherTester.USERNAME2, CredentialsHasherTester.PASSWORD2) is True
        assert self._credentialsHasher.verify(CredentialsHasherTester.USERNAME3, CredentialsHasherTester.PASSWORD3) is True

    def test4_hash_valid(self):
        self._credentialsHasher.add(CredentialsHasherTester.USERNAME1, CredentialsHasherTester.PASSWORD1)
        self._credentialsHasher.add(CredentialsHasherTester.USERNAME2, CredentialsHasherTester.PASSWORD2)
        self._credentialsHasher.add(CredentialsHasherTester.USERNAME3, CredentialsHasherTester.PASSWORD3)
        assert self._credentialsHasher.verify(CredentialsHasherTester.USERNAME2, CredentialsHasherTester.PASSWORD2) is True

    def test5_remove_hash(self):
        self._credentialsHasher.add(CredentialsHasherTester.USERNAME1, CredentialsHasherTester.PASSWORD1)
        self._credentialsHasher.add(CredentialsHasherTester.USERNAME2, CredentialsHasherTester.PASSWORD2)
        self._credentialsHasher.add(CredentialsHasherTester.USERNAME3, CredentialsHasherTester.PASSWORD3)
        assert self._credentialsHasher.verify(CredentialsHasherTester.USERNAME1, CredentialsHasherTester.PASSWORD1) is True
        assert self._credentialsHasher.verify(CredentialsHasherTester.USERNAME2, CredentialsHasherTester.PASSWORD2) is True
        assert self._credentialsHasher.verify(CredentialsHasherTester.USERNAME3, CredentialsHasherTester.PASSWORD3) is True
        self._credentialsHasher.remove(CredentialsHasherTester.USERNAME2)
        assert self._credentialsHasher.verify(CredentialsHasherTester.USERNAME2, CredentialsHasherTester.PASSWORD2) is False

    def test6_hash_count(self):
        self._credentialsHasher.add(CredentialsHasherTester.USERNAME1, CredentialsHasherTester.PASSWORD1)
        self._credentialsHasher.add(CredentialsHasherTester.USERNAME2, CredentialsHasherTester.PASSWORD2)
        self._credentialsHasher.add(CredentialsHasherTester.USERNAME3, CredentialsHasherTester.PASSWORD3)
        assert self._credentialsHasher.getCredentialCount() == 3

    def test7_hash_count2(self):
        self._credentialsHasher.add(CredentialsHasherTester.USERNAME1, CredentialsHasherTester.PASSWORD1)
        self._credentialsHasher.add(CredentialsHasherTester.USERNAME2, CredentialsHasherTester.PASSWORD2)
        self._credentialsHasher.add(CredentialsHasherTester.USERNAME3, CredentialsHasherTester.PASSWORD3)
        assert self._credentialsHasher.getCredentialCount() == 3
        self._credentialsHasher.remove(CredentialsHasherTester.USERNAME1)
        assert self._credentialsHasher.getCredentialCount() == 2
        self._credentialsHasher.remove(CredentialsHasherTester.USERNAME2)
        assert self._credentialsHasher.getCredentialCount() == 1
        self._credentialsHasher.remove(CredentialsHasherTester.USERNAME3)
        assert self._credentialsHasher.getCredentialCount() == 0
        
def main():
    """@brief Unit tests for the UIO class"""
    suite = unittest.TestLoader().loadTestsFromTestCase(CredentialsHasherTester)
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    main()