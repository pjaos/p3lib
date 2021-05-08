#!/usr/bin/env python3

import sys
import os
import re
import traceback
from   getpass import getpass
from   time import strftime, localtime
from   datetime import datetime

class UIO(object):
    """@brief responsible for user output and input via stdout/stdin"""

    DISPLAY_ATTR_RESET          =   0
    DISPLAY_ATTR_BRIGHT         =   1
    DISPLAY_ATTR_DIM            =   2
    DISPLAY_ATTR_UNDERSCORE     =   4
    DISPLAY_ATTR_BLINK          =   5
    DISPLAY_ATTR_REVERSE        =   7
    DISPLAY_ATTR_HIDDEN         =   8

    DISPLAY_ATTR_FG_BLACK       =   30
    DISPLAY_ATTR_FG_RED         =   31
    DISPLAY_ATTR_FG_GREEN       =   32
    DISPLAY_ATTR_FG_YELLOW      =   33
    DISPLAY_ATTR_FG_BLUE        =   34
    DISPLAY_ATTR_FG_MAGNETA     =   35
    DISPLAY_ATTR_FG_CYAN        =   36
    DISPLAY_ATTR_FG_WHITE       =   37

    DISPLAY_ATTR_BG_BLACK       =   40
    DISPLAY_ATTR_BG_RED         =   41
    DISPLAY_ATTR_BG_GREEN       =   42
    DISPLAY_ATTR_BG_YELLOW      =   43
    DISPLAY_ATTR_BG_BLUE        =   44
    DISPLAY_ATTR_BG_MAGNETA     =   45
    DISPLAY_ATTR_BG_CYAN        =   46
    DISPLAY_ATTR_BG_WHITE       =   47

    DISPLAY_RESET_ESCAPE_SEQ    = "\x1b[0m"

    PROG_BAR_LENGTH             =   40

    USER_LOG_SYM_LINK           = "log.txt"
    DEBUG_LOG_SYM_LINK          = "debug_log.txt"

    @staticmethod
    def GetInfoEscapeSeq():
        """@return the info level ANSI escape sequence."""
        return "\x1b[{:01d};{:02d}m".format(UIO.DISPLAY_ATTR_FG_GREEN, UIO.DISPLAY_ATTR_BRIGHT)

    @staticmethod
    def GetDebugEscapeSeq():
        """@return the debug level ANSI escape sequence."""
        return "\x1b[{:01d};{:02d};{:02d}m".format(UIO.DISPLAY_ATTR_FG_BLACK, UIO.DISPLAY_ATTR_BG_WHITE, UIO.DISPLAY_ATTR_BRIGHT)

    @staticmethod
    def GetWarnEscapeSeq():
        """@return the warning level ANSI escape sequence."""
        return "\x1b[{:01d};{:02d}m".format(UIO.DISPLAY_ATTR_FG_RED, UIO.DISPLAY_ATTR_BRIGHT)

    @staticmethod
    def GetErrorEscapeSeq():
        """@return the warning level ANSI escape sequence."""
        return "\x1b[{:01d};{:02d}m".format(UIO.DISPLAY_ATTR_FG_RED, UIO.DISPLAY_ATTR_BLINK)

    @staticmethod
    def RemoveEscapeSeq(text):
        """@brief Remove ANSI escape sequences that maybe present in text.
           @param text A string that may contain ANSI escape sequences.
           @return The text with any ANSI escape sequences removed."""
        escapeSeq =re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
        return escapeSeq.sub('', line)

    def __init__(self, debug=False, colour=True):
        self._debug                         = debug
        self._colour                        = colour
        self._logFile                       = None
        self._progBarSize                   = 0
        self._progBarGrow                   = True
        self._debugLogEnabled               = False
        self._debugLogFile                  = None
        self._symLinkDir                    = None

    def logAll(self, enabled):
        """@brief Turn on/off the logging of all output including debug output even if debugging is off."""
        self._debugLogEnabled = enabled

    def enableDebug(self, enabled):
        """@brief Enable/Disable debugging
           @param enabled If True then debugging is enabled"""
        self._debug = enabled

    def isDebugEnabled(self):
        """@return True if debuggin is eenabled."""
        return self._debug

    def info(self, text, highlight=False):
        """@brief Present an info level message to the user.
           @param text The line of text to be presented to the user."""
        if self._colour:
            if highlight:
                self._print('{}INFO:  {}{}'.format(UIO.GetInfoEscapeSeq(), text, UIO.DISPLAY_RESET_ESCAPE_SEQ))
            else:
                self._print('{}INFO{}:  {}'.format(UIO.GetInfoEscapeSeq(), UIO.DISPLAY_RESET_ESCAPE_SEQ, text))
        else:
            self._print('INFO:  {}'.format(text))

    def debug(self, text):
        """@brief Present a debug level message to the user if debuging is enabled.
           @param text The line of text to be presented to the user."""
        if self._debug:
            if self._colour:
                self._print('{}DEBUG{}: {}'.format(UIO.GetDebugEscapeSeq(), UIO.DISPLAY_RESET_ESCAPE_SEQ, text))
            else:
                self._print('DEBUG: {}'.format(text))
        elif self._debugLogEnabled and self._debugLogFile:
            if self._colour:
                self.storeToDebugLog('{}DEBUG{}: {}'.format(UIO.GetDebugEscapeSeq(), UIO.DISPLAY_RESET_ESCAPE_SEQ, text))
            else:
                self.storeToDebugLog('DEBUG: {}'.format(text))

    def warn(self, text):
        """@brief Present a warning level message to the user.
           @param text The line of text to be presented to the user."""
        if self._colour:
            self._print('{}WARN{}:  {}'.format(UIO.GetWarnEscapeSeq(), UIO.DISPLAY_RESET_ESCAPE_SEQ, text))
        else:
            self._print('WARN:  {}'.format(text))

    def error(self, text):
        """@brief Present an error level message to the user.
           @param text The line of text to be presented to the user."""
        if self._colour:
            self._print('{}ERROR{}: {}'.format(UIO.GetErrorEscapeSeq(), UIO.DISPLAY_RESET_ESCAPE_SEQ, text))
        else:
            self._print('ERROR: {}'.format(text))

    def _print(self, text):
        """@brief Print text to stdout"""
        self.storeToLog(text)
        if self._debugLogEnabled and self._debugLogFile:
            self.storeToDebugLog(text)
        print(text)

    def getInput(self, prompt, noEcho=False, stripEOL=True):
        """@brief Get a line of text from the user.
           @param noEcho If True then * are printed when each character is pressed.
           @param stripEOL If True then all end of line (\r, \n) characters are stripped.
           @return The line of text entered by the user."""
        if self._colour:
            if noEcho:
                prompt = "{}INPUT{}: ".format(UIO.GetInfoEscapeSeq(), UIO.DISPLAY_RESET_ESCAPE_SEQ) + prompt + ": "
                self.storeToLog(prompt, False)
                response = getpass(prompt, sys.stdout)

            else:
                prompt = "{}INPUT{}: ".format(UIO.GetInfoEscapeSeq(), UIO.DISPLAY_RESET_ESCAPE_SEQ) + prompt + ": "
                self.storeToLog(prompt, False)
                response = input(prompt)

        else:
            if noEcho:
                prompt = "INPUT: " + prompt + ": "
                self.storeToLog(prompt, False)
                response = getpass(prompt, sys.stdout)

            else:
                prompt = "INPUT: " + prompt + ": "
                self.storeToLog(prompt, False)
                response = input(prompt)

        if stripEOL:
            response = response.rstrip('\n')
            response = response.rstrip('\r')

        self.storeToLog(response)
        return response

    def getBoolInput(self, prompt, allowQuit=True):
        """@brief Get boolean repsonse from user (y or n response).
           @param allowQuit If True and the user enters q then the program will exit.
           @return True or False"""
        while True:
            response = self.getInput(prompt=prompt)
            if response.lower() == 'y':
                return True
            elif response.lower() == 'n':
                return False
            elif allowQuit and response.lower() == 'q':
                sys.exit(0)

    def getIntInput(self, prompt, allowQuit=True):
      """@brief Get a decimal int number from the user.
         @param allowQuit If True and the user enters q then the program will exit.
         @return True or False"""
      while True:
        response = self.getInput(prompt=prompt)
        try:
          return int(response)
        except ValueError:
          self.warn("%s is not a valid integer value." % (response))

        if allowQuit and response.lower() == 'q':
          return None

    def errorException(self):
        """@brief Show an exception traceback if debugging is enabled"""
        if self._debug:
            lines = traceback.format_exc().split('\n')
            for l in lines:
                self.error(l)

    def getPassword(self, prompt):
        """@brief Get a password from a user.
           @param prompt The user prompt.
           @return The password entered."""
        return self.getInput(prompt, noEcho=True)

    def setSymLinkDir(self, symLinkDir):
        """@brief Set a shortcut location for symLink.
           @param symLinkDir The directory to create the simlink.
           @return None"""
        self._symLinkDir=symLinkDir

    def setLogFile(self, logFile):
        """@brief Set a logfile for all output.
           @param logFile The file to send all output to.
           @return None"""
        self._logFile=logFile
        self._debugLogFile = "{}.debug.txt".format(self._logFile)

    def storeToLog(self, text, addLF=True, addDateTime=True):
        """@brief Save the text to the main log file if one is defined.
           @param text The text to be saved.
           @param addLF If True then a line feed is added to the output in the log file.
           @return None"""
        self._storeToLog(text, self._logFile, addLF=addLF, addDateTime=addDateTime)

    def storeToDebugLog(self, text, addLF=True, addDateTime=True):
        """@brief Save the text to the debug log file if one is defined. This file holds all the
                  data from the main log file plus debug data even if debugging is not enabled.
           @param text The text to be saved.
           @param addLF If True then a line feed is added to the output in the log file.
           @return None"""
        self._storeToLog(text, self._debugLogFile, addLF=addLF, addDateTime=addDateTime, symLinkFile=UIO.DEBUG_LOG_SYM_LINK)

    def _storeToLog(self, text, logFile, addLF=True, addDateTime=True, symLinkFile=USER_LOG_SYM_LINK):
        """@brief Save the text to the log file if one is defined.
           @param text The text to be saved.
           @param logFile The logFile to save data to.
           @param addLF If True then a line feed is added to the output in the log file.
           @param addDateTime If True add the date and time to the logfile.
           @param symLinkFile The name of the fixed symlink file to point to the latest log file.
           @return None"""
        createSymLink = False
        if logFile:
            if addDateTime:
                timeStr = datetime.now().strftime("%d/%m/%Y-%H:%M:%S.%f")
                text = "{}: {}".format(strftime(timeStr, localtime()).lower(), text)

            # If the log file is about to be created then we will create a symlink
            # to the file.
            if not os.path.isfile(logFile):
                createSymLink = True

            fd = open(logFile, 'a')
            if addLF:
                fd.write("{}\n".format(text))
            else:
                fd.write(text)
            fd.close()

            if createSymLink:
                #This is helpful as the link will point to the latest log file
                #which can be useful when debugging. I.E  no need to find the
                #name of the latest file.
                dirName = self._symLinkDir
                # if the simlink has not been set then default to the logging file
                if dirName is None:
                    dirName = os.path.dirname(logFile)
                absSymLink = os.path.join(dirName, symLinkFile)
                if os.path.lexists(absSymLink):
                    os.remove(absSymLink)
                os.symlink(logFile, absSymLink)

    def showProgBar(self, barChar='*'):
        """@brief Show a bar that grows and shrinks to indicate an activity is occuring."""
        if self._progBarGrow:
            sys.stdout.write(barChar)
            self._progBarSize+=1
            if self._progBarSize > UIO.PROG_BAR_LENGTH:
                self._progBarGrow=False
        else:
            sys.stdout.write('\b')
            sys.stdout.write(' ')
            sys.stdout.write('\b')
            self._progBarSize-=1
            if self._progBarSize == 0:
                self._progBarGrow=True

        sys.stdout.flush()

    def clearProgBar(self):
        """@brief Clear any progress characters that maybe present"""
        sys.stdout.write('\b' * UIO.PROG_BAR_LENGTH)
        sys.stdout.write(' '*UIO.PROG_BAR_LENGTH)
        sys.stdout.write('\r')
        sys.stdout.flush()

    def getLogFile(self):
        """@return the name of the user output log file or None if not set"""
        return self._logFile

    def getDebugLogFile(self):
        """@return The name of the debug log file or None if not set."""
        return self._debugLogFile