#!/bin/sh/env python3d

from os.path import join, isfile, expanduser, getmtime, basename, isdir
from helper import getDict, saveDict
from shutil import copyfile
import datetime
import sys

class ConfigManager(object):
    """@brief Responsible for storing and loading configuration.
              Also responsible for providing methods that allow users to enter
              configuration."""

    UNSET_VALUE                 = "UNSET"
    DECIMAL_INT_NUMBER_TYPE     = 0
    HEXADECIMAL_INT_NUMBER_TYPE = 1
    FLOAT_NUMBER_TYPE           = 2


    @staticmethod
    def GetString(uio, prompt, previousValue, allowEmpty=True):
      """@brief              Get a string from the the user.
         @param uio          A UIO (User Inpu Output) instance.
         @param prompt       The prompt presented to the user in order to enter
                             the float value.
         @param previousValue The previous value of the string.
         @param allowEmpty   If True then allow the string to be empty."""
      _prompt = prompt
      try:
          prompt = "%s (%s)" % (prompt, previousValue)
      except ValueError:
          prompt = "%s" % (prompt)

      while True:

        response = uio.getInput("%s" % (prompt))

        if len(response) == 0:

            if allowEmpty:

                if len(previousValue) > 0:
                    booleanResponse = uio.getInput("Do you wish to enter the previous value '%s' y/n: " % (previousValue) )
                    booleanResponse=booleanResponse.lower()
                    if booleanResponse == 'y':
                        response = previousValue
                        break

                booleanResponse = uio.getInput("Do you wish to clear '%s' y/n: " % (_prompt) )
                booleanResponse=booleanResponse.lower()
                if booleanResponse == 'y':
                    break
                else:
                    uio.info("A value is required. Please enter a value.")

            else:

                booleanResponse = uio.getInput("Do you wish to enter the previous value of %s y/n: " % (previousValue) )
                booleanResponse=booleanResponse.lower()
                if booleanResponse == 'y':
                    response = previousValue
                    break
        else:
            break

      return response

    @staticmethod
    def IsValidDate(date):
        """@brief determine if the string is a valid date.
           @param date in the form DAY/MONTH/YEAR (02:01:2018)"""
        validDate = False
        if len(date) >= 8:
            elems = date.split("/")
            try:
                day = int(elems[0])
                month = int(elems[1])
                year = int(elems[2])
                datetime.date(year, month, day)
                validDate = True
            except ValueError:
                pass
        return validDate

    @staticmethod
    def GetDate(uio, prompt, previousValue, allowEmpty=True):
        """@brief Input a date in the format DAY:MONTH:YEAR"""
        if not ConfigManager.IsValidDate(previousValue):
            today =  datetime.date.today()
            previousValue = today.strftime("%d/%m/%Y")
        while True:
            newValue = ConfigManager.GetString(uio, prompt, previousValue, allowEmpty=allowEmpty)
            if ConfigManager.IsValidDate(newValue):
                return newValue

    @staticmethod
    def IsValidTime(theTime):
        """@brief determine if the string is a valid time.
           @param theTime in the form HOUR:MINUTE:SECOND (12:56:01)"""
        validTime = False
        if len(theTime) >= 5:
            elems = theTime.split(":")
            try:
                hour = int(elems[0])
                minute = int(elems[1])
                second = int(elems[2])
                datetime.time(hour, minute, second)
                validTime = True
            except ValueError:
                pass
        return validTime

    @staticmethod
    def GetTime(uio, prompt, previousValue, allowEmpty=True):
        """@brief Input a time in the format HOUR:MINUTE:SECOND"""
        if not ConfigManager.IsValidTime(previousValue):
            today =  datetime.datetime.now()
            previousValue = today.strftime("%H:%M:%S")
        while True:
            newValue = ConfigManager.GetString(uio, prompt, previousValue, allowEmpty=allowEmpty)
            if ConfigManager.IsValidTime(newValue):
                return newValue

    @staticmethod
    def _GetNumber(uio, prompt, previousValue=UNSET_VALUE, minValue=UNSET_VALUE, maxValue=UNSET_VALUE, numberType=FLOAT_NUMBER_TYPE, radix=10):
      """@brief              Get float repsonse from user.
         @param uio          A UIO (User Inpu Output) instance.
         @param prompt       The prompt presented to the user in order to enter
                             the float value.
         @param previousValue The previous number value.
         @param minValue     The minimum acceptable value.
         @param maxValue     The maximum acceptable value.
         @param numberType   The type of number."""

      if numberType == ConfigManager.DECIMAL_INT_NUMBER_TYPE:

          radix=10

      elif numberType == ConfigManager.HEXADECIMAL_INT_NUMBER_TYPE:

          radix = 16

      while True:

        response = ConfigManager.GetString(uio, prompt, previousValue, allowEmpty=False)

        try:

            if numberType == ConfigManager.FLOAT_NUMBER_TYPE:

                value = float(response)

            else:

                value = int(str(response), radix)

            if minValue != ConfigManager.UNSET_VALUE and value < minValue:

                if radix == 16:
                    minValueStr = "0x%x" % (minValue)
                else:
                    minValueStr = "%d" % (minValue)

                uio.info("%s is less than the min value of %s." % (response, minValueStr) )
                continue

            if maxValue != ConfigManager.UNSET_VALUE and value > maxValue:

                if radix == 16:
                    maxValueStr = "0x%x" % (maxValue)
                else:
                    maxValueStr = "%d" % (maxValue)

                uio.info("%s is greater than the max value of %s." % (response, maxValueStr) )
                continue

            return value

        except ValueError:

            if numberType == ConfigManager.FLOAT_NUMBER_TYPE:

                uio.info("%s is not a valid number." % (response) )

            elif numberType == ConfigManager.DECIMAL_INT_NUMBER_TYPE:

                uio.info("%s is not a valid integer value." % (response) )

            elif numberType == ConfigManager.HEXADECIMAL_INT_NUMBER_TYPE:

                uio.info("%s is not a valid hexadecimal value." % (response) )

    @staticmethod
    def GetDecInt(uio, prompt, previousValue=UNSET_VALUE, minValue=UNSET_VALUE, maxValue=UNSET_VALUE):
      """@brief              Get a decimal integer number from the user.
         @param uio          A UIO (User Inpu Output) instance.
         @param prompt       The prompt presented to the user in order to enter
                             the float value.
         @param previousValue The previous number value.
         @param minValue     The minimum acceptable value.
         @param maxValue     The maximum acceptable value."""

      return ConfigManager._GetNumber(uio, prompt, previousValue=previousValue, minValue=minValue, maxValue=maxValue, numberType=ConfigManager.DECIMAL_INT_NUMBER_TYPE)

    @staticmethod
    def GetHexInt(uio, prompt, previousValue=UNSET_VALUE, minValue=UNSET_VALUE, maxValue=UNSET_VALUE):
      """@brief              Get a decimal integer number from the user.
         @param uio          A UIO (User Inpu Output) instance.
         @param prompt       The prompt presented to the user in order to enter
                             the float value.
         @param previousValue The previous number value.
         @param minValue     The minimum acceptable value.
         @param maxValue     The maximum acceptable value."""

      return ConfigManager._GetNumber(uio, prompt, previousValue=previousValue, minValue=minValue, maxValue=maxValue, numberType=ConfigManager.HEXADECIMAL_INT_NUMBER_TYPE)

    @staticmethod
    def GetFloat(uio, prompt, previousValue=UNSET_VALUE, minValue=UNSET_VALUE, maxValue=UNSET_VALUE):
      """@brief              Get a float number from the user.
         @param uio          A UIO (User Inpu Output) instance.
         @param prompt       The prompt presented to the user in order to enter
                             the float value.
         @param previousValue The previous number value.
         @param minValue     The minimum acceptable value.
         @param maxValue     The maximum acceptable value."""

      return ConfigManager._GetNumber(uio, prompt, previousValue, minValue=minValue, maxValue=maxValue, numberType=ConfigManager.FLOAT_NUMBER_TYPE)

    def __init__(self, uio, cfgFilename, defaultConfig):
        """@brief Constructor
           @param uio A UIO (User Inpu Output) instance.
           @param cfgFilename   The name of the config file.
           @param defaultConfig A default config instance containg all the default key-value pairs."""
        self._uio           = uio
        self._cfgFilename   = cfgFilename
        self._defaultConfig = defaultConfig
        self._configDict    = {}

        self._cfgFile = self._getConfigFile()
        self._modifiedTime = self._getModifiedTime()

    def _getConfigFile(self):
        """@brief Get the calibration file."""
        if not self._cfgFilename.startswith("."):

            cfgFilename=".%s" % (self._cfgFilename)

        else:

            cfgFilename=self._cfgFilename

        userPath = expanduser("~")
        userPath = userPath.strip()
        #If no user is known then default to root user.
        #This occurs on Omega2 startup apps.
        if len(userPath) == 0 or userPath == '/':
            userPath="/root"

        return join( userPath, cfgFilename )

    def addAttr(self, key, value):
        """@brief Add an attribute value to the config.
           @param key The key to store the value against.
           @param value The value to be stored."""
        self._configDict[key]=value

    def getAttrList(self):
        """@return A list of attribute names that are stored."""
        return self._configDict.keys()

    def getAttr(self, key, allowModify=True):
        """@brief Get an attribute value.
           @param key The key for the value we're after.
           @param allowModify If True and the configuration has been modified
                  since the last read by the caller then the config will be reloaded."""

        #If the config file has been modified then read the config to get the updated state.
        if allowModify and self.isModified():
            self.load(showLoadedMsg=False)
            self.updateModifiedTime()

        return self._configDict[key]

    def store(self, copyToRoot=False):
        """@brief Store the config to the config file.
           @param copyToRoot If True copy the config to the root user (Linux only)
                             if not running with root user config path. If True
                             on non Linux system config will only be saved in
                             the users home path. Default = False."""
        saveDict(self._configDict, self._cfgFile, jsonFmt=True)
        if self._uio:
            self._uio.info("Saved config to %s." % (self._cfgFile) )
        self.updateModifiedTime()

        if copyToRoot and not self._cfgFile.startswith("/root/") and isdir("/root"):
            fileN = basename(self._cfgFile)
            rootCfgFile = join("/root", fileN)
            copyfile(self._cfgFile, rootCfgFile)
            if self._uio:
                self._uio.info("Also updated service list in %s" % (rootCfgFile))

    def load(self, showLoadedMsg=True):
        """@brief Load the config."""
        missingKey= False

        if not isfile(self._cfgFile):

            self._configDict = self._defaultConfig
            self.store()

        else:

            self._configDict = getDict(self._cfgFile, jsonFmt=True)

            #If the expected keys have changed use the default
            expectedKeys = self._defaultConfig.keys()
            for expectedKey in expectedKeys:
                if not expectedKey in self._configDict:
                    missingKey=True
                    break

            if missingKey:
                self._configDict = self._defaultConfig
                self.store()
                if self._uio:
                    self._uio.warn("Failed to load config. Using default configuration.")

        if showLoadedMsg and not missingKey and self._uio:
            self._uio.info("Loaded config from %s" % (self._cfgFile) )

    def inputFloat(self, key, prompt, minValue=UNSET_VALUE, maxValue=UNSET_VALUE):
        """@brief Input a float value into the config.
           @key The key to store this value in the config.
           @param prompt       The prompt presented to the user in order to enter
                             the float value.
           @param minValue     The minimum acceptable value.
           @param maxValue     The maximum acceptable value."""
        value = ConfigManager.GetFloat(self._uio, prompt, previousValue=self._getValue(key), minValue=minValue, maxValue=maxValue)
        self.addAttr(key, value)

    def inputDecInt(self, key, prompt, minValue=UNSET_VALUE, maxValue=UNSET_VALUE):
        """@brief Input a decimal integer value into the config.
           @key The key to store this value in the config.
           @param prompt       The prompt presented to the user in order to enter
                             the float value.
           @param minValue     The minimum acceptable value.
           @param maxValue     The maximum acceptable value."""
        value = ConfigManager.GetDecInt(self._uio, prompt, previousValue=self._getValue(key), minValue=minValue, maxValue=maxValue)
        self.addAttr(key, value)

    def inputHexInt(self, key, prompt, minValue=UNSET_VALUE, maxValue=UNSET_VALUE):
        """@brief Input a hexadecimal integer value into the config.
           @key The key to store this value in the config.
           @param prompt       The prompt presented to the user in order to enter
                             the float value.
           @param minValue     The minimum acceptable value.
           @param maxValue     The maximum acceptable value."""
        value = ConfigManager.GetHexInt(self._uio, prompt, previousValue=self._getValue(key), minValue=minValue, maxValue=maxValue)
        self.addAttr(key, value)

    def _getValue(self, key):
        """@brief Get the current value of the key.
           @param key The key of the value we're after.
           @return The value of the key or and empty string if key not found."""
        value=""

        if key in self._configDict:
            value = self.getAttr(key)

        return value

    def inputStr(self, key, prompt, allowEmpty):
        """@brief Input a string value into the config.
           @param key The key to store this value in the config.
           @param prompt The prompt presented to the user in order to enter
                         the float value.
           @param allowEmpty   If True then allow the string to be empty."""
        value = ConfigManager.GetString(self._uio, prompt, previousValue=self._getValue(key), allowEmpty=allowEmpty )
        self.addAttr(key, value)

    def inputDate(self, key, prompt, allowEmpty):
        """@brief Input a date into the config.
           @param key The key to store this value in the config.
           @param prompt The prompt presented to the user in order to enter
                         the float value.
           @param allowEmpty   If True then allow the string to be empty."""
        value = ConfigManager.GetDate(self._uio, prompt, previousValue=self._getValue(key), allowEmpty=allowEmpty )
        self.addAttr(key, value)

    def inputTime(self, key, prompt, allowEmpty):
        """@brief Input a date into the config.
           @param key The key to store this value in the config.
           @param prompt The prompt presented to the user in order to enter
                         the float value.
           @param allowEmpty   If True then allow the string to be empty."""
        value = ConfigManager.GetTime(self._uio, prompt, previousValue=self._getValue(key), allowEmpty=allowEmpty )
        self.addAttr(key, value)

    def inputBool(self, key, prompt):
        """@brief Input a boolean value.
           @param key The key to store this value in the config.
           @param prompt The prompt presented to the user in order to enter
                         the boolean (Yes/No) value."""
        previousValue=self._getValue(key)
        yes = self.getYesNo(prompt, previousValue=previousValue)
        if yes:
            value=1
        else:
            value=0
        self.addAttr(key, value)

    def getYesNo(self, prompt, previousValue=0):
        """@brief Input yes no response.
           @param prompt The prompt presented to the user in order to enter
                         the float value.
           @param allowEmpty   If True then allow the string to be empty.
           @return True if Yes, False if No."""

        _prompt = "%s y/n" % (prompt)

        if previousValue:
            prevValue='y'
        else:
            prevValue='n'

        while True:
            value = ConfigManager.GetString(self._uio, _prompt, prevValue)
            value=value.lower()
            if value == 'n':
                return False
            elif value == 'y':
                return True

    def _getModifiedTime(self):
        """@brief Get the modified time of the config file."""
        mtime = 0
        try:

            if isfile(self._cfgFile):
                mtime = getmtime(self._cfgFile)

        except OSError:
            pass

        return mtime

    def updateModifiedTime(self):
        """@brief Update the modified time held as an attr in this nistance with the current modified time of the file."""
        self._modifiedTime = self._getModifiedTime()

    def isModified(self):
        """@Return True if the config file has been updated."""
        mTime = self._getModifiedTime()
        if mTime != self._modifiedTime:
            return True
        return False

    def _getConfigAttDetails(self, key, configAttrDetailsDict):
        """@brief Get the configAttrDetails details instance from the dict.
           @param key The in to the value in the configAttrDetailsDict
           @param configAttrDetailsDict The dict containing attr meta data."""
        if key in configAttrDetailsDict:
            return configAttrDetailsDict[key]
        raise Exception("getConfigAttDetails(): The %s dict has no key=%s" % ( str(configAttrDetailsDict), key) )

    def edit(self, configAttrDetailsDict):
        """@brief A high level method to allow user to edit all config attributes.
           @param configAttrDetailsDict A dict that holds configAttrDetails
                  instances, each of which provide data required for the
                  user to enter the configuration parameter."""

        if len(self._configDict.keys()) == 0:
            self.load(showLoadedMsg=True)

        keyList = list(self._configDict.keys())
        keyList.sort()
        index = 0
        while index < len(keyList):

            try:

                key = keyList[index]

                configAttrDetails = self._getConfigAttDetails(key, configAttrDetailsDict)

                if key.endswith("_FLOAT"):

                    self.inputFloat(key, configAttrDetails.prompt, minValue=configAttrDetails.minValue, maxValue=configAttrDetails.maxValue)

                elif key.endswith("_INT"):

                    self.inputDecInt(key, configAttrDetails.prompt, minValue=configAttrDetails.minValue, maxValue=configAttrDetails.maxValue)

                elif key.endswith("_HEXINT"):

                    self.inputHexInt(key, configAttrDetails.prompt, minValue=configAttrDetails.minValue, maxValue=configAttrDetails.maxValue)

                elif key.endswith("_STR"):

                    self.inputStr(key, configAttrDetails.prompt, configAttrDetails.allowEmpty)

                index = index + 1

            except KeyboardInterrupt:

                if index > 0:
                    index=index-1
                    print('\n')

                else:
                    while True:
                        try:
                            print('\n')
                            if self.getYesNo("Quit ?"):
                                sys.exit(0)
                            break
                        except KeyboardInterrupt:
                            pass

        self.store()

    def show(self, uio):
        """@brief Show the state of configuration parameters.
           @param uio The UIO instance to use to show the parameters."""
        attrList = self.getAttrList()
        attrList.sort()

        maxAttLen=0
        for attr in attrList:
            if len(attr) > maxAttLen:
                maxAttLen=len(attr)

        for attr in attrList:
            padding = " "*(maxAttLen-len(attr))
            uio.info("%s%s = %s" % (attr, padding, self.getAttr(attr)) )

class ConfigAttrDetails(object):
    """@brief Responsible for holding config attribute meta data."""

    def __init__(self, prompt, minValue=ConfigManager.UNSET_VALUE, maxValue=ConfigManager.UNSET_VALUE, allowEmpty=True):
        self.prompt         =   prompt      #Always used to as k user to enter attribute value.
        self.minValue       =   minValue    #Only used for numbers
        self.maxValue       =   maxValue    #Only used for numbers
        self.allowEmpty     =   allowEmpty  #Only used for strings
