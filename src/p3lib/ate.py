from time import time

# Responsible for providing functionality useful when implementing ATE solutions
# including Engineering hardware test and MFG test.

class TestCase(object):
    """@brief Responsible for holding the details of a single test case."""
    
    def __init__(self, testCaseNumber, testCaseDescription, testMethod):
        """@brief Constructor for a single test case
           @param testCaseNumber The number of the test case. This must be an integer value.
           @param slTestCaseDescription The test case description as a single line of text.
           @param testMethod The method to call to perform the test case."""
        if not isinstance(testCaseNumber, int):
            raise Exception(f"{testCaseNumber} (test case number) must be an integer value.")
        
        elems = testCaseDescription.split("\n")
        if len(elems) > 1:
            raise Exception(f"The test case description must be a single line of text. slTestCaseDescription = {testCaseDescription}")
        
        if testMethod is None:
            raise Exception(f"No test method defined for test {testCaseNumber}")
        
        self._testCaseNumber = testCaseNumber
        self._testCaseDescription = testCaseDescription
        self._testMethod=testMethod
        
        self._preConditionMethod = None     
        self._postConditionMethod = None   
        
    def getNumber(self):
        """@brief Get method for test case number."""
        return self._testCaseNumber
    
    def getDescription(self):
        """@brief Get method for test case description."""
        return self._testCaseDescription
    
    def getMethod(self):
        """@brief Get method for test case method."""
        return self._testMethod
    
    def setPreConditionMethod(self, preConditionMethod):
        """@brief Set the pre condition method to be called before the test method.
           @param preConditionMethod The method to be called."""
        self._preConditionMethod = preConditionMethod

    def getPreConditionMethod(self):
        """@brief Get the pre condition method to be called before the test method."""
        return self._preConditionMethod
    
    def setPostConditionMethod(self, postConditionMethod):
        """@brief Set the post condition method to be called after the test method.
           @param postConditionMethod The method to be called."""
        self._postConditionMethod = postConditionMethod

    def getPostConditionMethod(self):
        """@brief Get the post condition method to be called before the test method."""
        return self._postConditionMethod
    
    def showBanner(self, uio):
        """@brief Show the test case banner message to the user."""
        table = []
        table.append(("Test Case", "Description"))
        table.append((f"{self._testCaseNumber}", f"{self._testCaseDescription}"))
        uio.showTable(table)

class TestCaseBase(object):
    """@brief a base class that provides a simple interface to execute a sequence of test cases."""
    
    def __init__(self, uio):
        """@brief Constructor.
           @param uio A UIO instance for getting input from and sending info to the user."""
        self._uio = uio
        self._testCaseList = []
        
    def addTestCase(self, testCaseNumber, testCaseDescription, testMethod):
        """@brief Add a test case to the list of available test cases."""
        # Check we don't have a duplicaste test case number
        for testCase in self._testCaseList:
            if testCase.getNumber() == testCaseNumber:
                raise Exception("Test case number {testCaseNumber} is already used.")
            # We don't check for duplicate test case descriptions or methods because 
            # the caller may wish to perform a test case multiple times during testing.
        testCase = TestCase(testCaseNumber, testCaseDescription, testMethod)
        self._testCaseList.append(testCase)
            
    def executeTestCases(self):
        """@brief Call all test cases in the test sequence."""
        startTime = time()
        try:
            for testCase in self._testCaseList:
                testCase.showBanner(self._uio)
                preMethod = testCase.getPreConditionMethod()
                if preMethod:
                    preMethod()
                
                testCaseMethod = testCase.getMethod()
                testCaseMethod()
                
                postMethod = testCase.getPostConditionMethod()
                if postMethod:
                    postMethod()
        finally:
            # Report the test time even in the event of a test failure.
            testSecs = time()-startTime
            self._uio.info(f"Took {testSecs:.1f} seconds to test.")

