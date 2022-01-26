#!/usr/bin/env python3

from    time import sleep
from    p3lib.netif import NetIF

#These must be changed to use an interface on the local machine.
NET_IF = "enp0s31f6"
IP_ADDRESS = "192.168.0.51"
NETMASK = "255.255.255.0"

class TestClass:
    """@brief Test the NEtIF class."""

    def test_ip_in_network(self):
        assert( NetIF.IsAddressInNetwork("192.168.1.123", "192.168.1.0/24") )

    def test_ip_not_in_network(self):
        assert( not NetIF.IsAddressInNetwork("192.168.1.123", "192.168.2.0/24") )

    def test_IPStr2int_0(self):
        intValue = NetIF.IPStr2int("0.0.0.0")
        assert( intValue == 0 )

    def test_IPStr2int_f(self):
        intValue = NetIF.IPStr2int("255.255.255.255")
        assert( intValue == 0xffffffff )

    def test_IPStr2int_v(self):
        intValue = NetIF.IPStr2int("192.168.1.1")
        assert( intValue == 0xc0a80101 )

    def test_Int2IPStr_0(self):
        strValue = NetIF.Int2IPStr(0)
        assert( strValue == "0.0.0.0" )

    def test_Int2IPStr_f(self):
        strValue = NetIF.Int2IPStr(0xffffffff)
        assert( strValue == "255.255.255.255" )

    def test_Int2IPStr_v(self):
        strValue = NetIF.Int2IPStr(0xc0a80101)
        assert( strValue == "192.168.1.1" )

    def test_NetmaskToBitCount(self):
        assert( NetIF.NetmaskToBitCount("255.255.255.0") == 24 )

    def test_getIFDict(self):
        netif = NetIF()
        ifDict = netif.getIFDict()

    def test_checkSupportedOS(self):
        netif = NetIF()
        netif._checkSupportedOS()

    def test_getIFName(self):
        netif = NetIF()
        #This requires the machine has an interface on the IP_ADDRESS/24 network
        ifName = netif.getIFName(IP_ADDRESS)
        assert( ifName == NET_IF)

        ifName = netif.getIFName("1.1.1.1")
        assert( ifName == None )

    def test_getIFNetmask(self):
        netif = NetIF()
        #This requires the machine has an interface named MACHINE_NET_IF
        nm = netif.getIFNetmask(NET_IF)
        assert( nm == NETMASK )

    def test_getIFIPAddress(self):
        netif = NetIF()
        ipAddr = netif.getIFIPAddress(NET_IF)
        assert( ipAddr == IP_ADDRESS )
        
    def test_getLocalNetworkAddress(self):
        netif = NetIF()
        ipAddr = netif.getLocalNetworkAddress()
        assert( ipAddr == IP_ADDRESS )
        
