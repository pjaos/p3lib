#!/usr/bin/env python3

from    time import sleep
from    p3lib.json_networking import JSONServer, JsonServerHandler, JSONClient
import  threading

class ServerSessionHandler(JsonServerHandler):
    #handler that sends data back to src
    def handle(self):
        try:
            while True:
                rxDict = self.rx()
                self.tx(self.request, rxDict)

        except:
            pass

class TestClass:
    """@brief Test the json_networking class byt setting up a server sending data to is and checking the data we get back
              what we sent."""
    HOST        = "localhost"
    PORT        = 9999
    APASSWORD   = "300fkslaa"
    MIN_ID      = 0
    MAX_ID      = 100
    ID_STR      = "ID"

    @classmethod
    def setup_class(cls):
        server = JSONServer((TestClass.HOST, TestClass.PORT), ServerSessionHandler)
        serverThread = threading.Thread(target=server.serve_forever)
        serverThread.setDaemon(True)
        serverThread.start()

    def test_connect(self):
        client = JSONClient(TestClass.HOST, TestClass.PORT)

    def test_tx(self):
        client = JSONClient(TestClass.HOST, TestClass.PORT)
        txDict = {"password": "apassword"}
        client.tx(txDict)

    def test_rx(self):
        client = JSONClient(TestClass.HOST, TestClass.PORT)

        txDict = {"password": TestClass.APASSWORD}
        client.tx(txDict)

        rxDict = client.rx()
        assert( "password" in rxDict)
        value = rxDict["password"]
        assert( value == TestClass.APASSWORD )

    def txThread(self, client):
        for id in range(TestClass.MIN_ID, TestClass.MAX_ID):
            txDict = {TestClass.ID_STR: id}
            client.tx(txDict)

    def test_tx_multiple(self):
        client = JSONClient(TestClass.HOST, TestClass.PORT)
        txThread = threading.Thread(target=self.txThread, args=(client,) )
        txThread.start()
        for id in range(TestClass.MIN_ID, TestClass.MAX_ID):
            txDict = {TestClass.ID_STR: id}
            client.tx(txDict)

    def test_rx_multiple(self):
        client = JSONClient(TestClass.HOST, TestClass.PORT)
        txThread = threading.Thread(target=self.txThread, args=(client,) )
        txThread.start()

        expectedID=TestClass.MIN_ID
        while True:
            rxDict = client.rx()
            assert(TestClass.ID_STR in rxDict)
            id = rxDict[TestClass.ID_STR]
            assert( id  == expectedID )
            expectedID=expectedID+1
            if expectedID == TestClass.MAX_ID:
                break

        client.close()

    def test_rx_multiple_non_blocking(self):
        client = JSONClient(TestClass.HOST, TestClass.PORT)
        txThread = threading.Thread(target=self.txThread, args=(client,))
        txThread.start()

        expectedID = TestClass.MIN_ID
        while True:
            rxDict = client.rx(blocking=False)
            if rxDict:
                assert (TestClass.ID_STR in rxDict)
                id = rxDict[TestClass.ID_STR]
                assert (id == expectedID)
                expectedID = expectedID + 1
                if expectedID == TestClass.MAX_ID:
                    break

        client.close()
