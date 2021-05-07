#!/usr/bin/env python3

import unittest

from    uio import UIO
from    ssh import SSH, SSHTunnelManager
from    time import sleep

class SSHTester(unittest.TestCase):
    """@brief Unit tests for the UIO class"""

    def setUp(self):
        """@brief To test correctly the ssh key should be removed from the server
               The user will be asked to enter a password and the connect will succeed.
               The next time the user should be able to login without a password."""
        self._uio = UIO()
        host="localhost"
        username="pja"
        uio = UIO()
        self.ssh = SSH("localhost", username, uio=uio)

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
        sshTunnelManager.startFwdSSHTunnel(10000, "192.168.0.8", 22)
        #sleep(30)

    def test4_revTunnel(self):
        self.ssh.connect()
        sshTunnelManager = SSHTunnelManager(self._uio, self.ssh, True)
        sshTunnelManager.startRevSSHTunnel(10000, "localhost", 22)
        sleep(30)

def main():
    """@brief Unit tests for the UIO class"""
    suite = unittest.TestLoader().loadTestsFromTestCase(SSHTester)
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    main()
