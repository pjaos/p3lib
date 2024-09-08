#!/usr/bin/env python3

import unittest
from    time import sleep

# Supress the following warning
# CryptographyDeprecationWarning: TripleDES has been moved to cryptography.hazmat.decrepit.ciphers.algorithms.TripleDES and will be removed from this module in 48.0.0.
import warnings
from cryptography.utils import CryptographyDeprecationWarning
with warnings.catch_warnings(action="ignore", category=CryptographyDeprecationWarning):
    import paramiko

from    p3lib.uio import UIO
from    p3lib.ssh import SSH, SSHTunnelManager

#An ssh login on an ssh server must be available for these test to run.
USERNAME="pja"
SERVER="localhost"

class SSHTester(unittest.TestCase):
    """@brief Unit tests for the UIO class"""

    def setUp(self):
        """@brief To test correctly the ssh key should be removed from the server
               The user will be asked to enter a password and the connect will succeed.
               The next time the user should be able to login without a password."""
        self._uio = UIO()
        uio = UIO()
        self.ssh = SSH(SERVER, USERNAME, uio=uio)

    def tearDown(self):
        self.ssh.close()

    def test1_connect(self):
        self.ssh.connect()

    def test2_put(self):
        localFile = "/tmp/pushFile.txt"
        remoteFile = "/tmp/pushedFile.txt"
        fd = open(localFile, 'w')
        fd.write("1234\n")
        fd.close()

        self.ssh.connect(connectSFTPSession=True)
        self.ssh.putFile(localFile, remoteFile)

    def test3_get(self):
        localFile = "/tmp/pulledFile.txt"
        remoteFile = "/tmp/pushedFile.txt"
        fd = open(localFile, 'w')
        fd.write("1234\n")
        fd.close()

        self.ssh.connect(connectSFTPSession=True)
        self.ssh.getFile(remoteFile, localFile)

    def test4_fwdTunnel(self):
        self.ssh.connect()
        sshTunnelManager = SSHTunnelManager(self._uio, self.ssh, True)
        sshTunnelManager.startFwdSSHTunnel(30000, SERVER, 22)

    def test5_revTunnel(self):
        self.ssh.connect()
        sshTunnelManager = SSHTunnelManager(self._uio, self.ssh, True)
        sshTunnelManager.startRevSSHTunnel(30000, SERVER, 22)

def main():
    """@brief Unit tests for the UIO class"""
    suite = unittest.TestLoader().loadTestsFromTestCase(SSHTester)
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    main()
