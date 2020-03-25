#!/usr/bin/env python3

################################################################################
#
# Copyright (c) 2016, Paul Austen. All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301  USA
#
################################################################################

import os

class Helper(object):
    """@brief Responsible for providing static helper methods that other
              classes can subclass to make available to all subclasses."""

    @staticmethod
    def GetHomePath():
        """Get the user home path as this will be used to store config files"""
        if "HOME" in os.environ:
            return os.environ["HOME"]

        elif "HOMEDRIVE" in os.environ and "HOMEPATH" in os.environ:
            return os.environ["HOMEDRIVE"] + os.environ["HOMEPATH"]

        elif "USERPROFILE" in os.environ:
            return os.environ["USERPROFILE"]

        return None

    @staticmethod
    def GetAddrPort(host, defaultPort=22):
        """@brief The host address may be entered in the format <address>:<port>
           @param host The host address. May be in the form address:port.
           @param defaultPort The default port to use if no port is defined in the host string (= 22)
           @return a tuple with host and port"""

        port = defaultPort
        elems = host.split(":")

        if len(elems) > 1:
            host = elems[0]
            port = int(elems[1])

        return [host, port]