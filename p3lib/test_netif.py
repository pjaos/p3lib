#!/usr/bin/env python3

from    time import sleep
from    netif import NetIF

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
        #This requires the machine has an interface on the 192.168.0.0/24 network
        ifName = netif.getIFName("192.168.0.100")
        assert( ifName == "enp0s31f6")
        
        ifName = netif.getIFName("172.40.34.10")
        assert( ifName == None )
        
    def test_getIFNetmask(self):
        netif = NetIF()
        #This requires the machine has an interface named enp0s31f6
        nm = netif.getIFNetmask("enp0s31f6")
        assert( nm == "255.255.255.0" )
        
    def test_getIFIPAddress(self):
        netif = NetIF()
        #This requires the machine has an interface named enp0s31f6 with the
        #IP addrress 192.168.0.248
        ipAddr = netif.getIFIPAddress("enp0s31f6")
        assert( ipAddr == "192.168.0.248" )
        
