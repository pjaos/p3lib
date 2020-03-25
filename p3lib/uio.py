#!/usr/bin/env python3

################################################################################
#
# Copyright (c) 2010, Paul Austen. All rights reserved.
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

import sys
import traceback
from   getpass import getpass


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

    def __init__(self, debug=False, colour=True):
        self._debug  = debug
        self._colour = colour

    @staticmethod
    def GetInfoEscapeSeq():
        """@return the info level escape sequence."""
        return "\x1b[{:01d};{:02d}m".format(UIO.DISPLAY_ATTR_FG_GREEN, UIO.DISPLAY_ATTR_BRIGHT)

    @staticmethod
    def GetDebugEscapeSeq():
        """@return the debug level escape sequence."""
        return "\x1b[{:01d};{:02d};{:02d}m".format(UIO.DISPLAY_ATTR_FG_BLACK, UIO.DISPLAY_ATTR_BG_WHITE, UIO.DISPLAY_ATTR_BRIGHT)

    @staticmethod
    def GetWarnEscapeSeq():
        """@return the warning level escape sequence."""
        return "\x1b[{:01d};{:02d}m".format(UIO.DISPLAY_ATTR_FG_RED, UIO.DISPLAY_ATTR_BRIGHT)

    @staticmethod
    def GetErrorEscapeSeq():
        """@return the warning level escape sequence."""
        return "\x1b[{:01d};{:02d}m".format(UIO.DISPLAY_ATTR_FG_RED, UIO.DISPLAY_ATTR_BLINK)

    def enableDebug(self, enabled):
        """@brief Enable/Disable debugging
           @param enabled If True then debugging is enabled"""
        self._debug = enabled

    def info(self, text):
        """@brief Present an info level message to the user.
           @param text The line of text to be presented to the user."""
        if self._colour:
            print('{}INFO{}:  {}'.format(UIO.GetInfoEscapeSeq(), UIO.DISPLAY_RESET_ESCAPE_SEQ, text))
        else:
            print('INFO:  {}'.format(text))

    def debug(self, text):
        """@brief Present a debug level message to the user if debuging is enabled.
           @param text The line of text to be presented to the user."""
        if self._debug:
            if self._colour:
                print('{}DEBUG{}: {}'.format(UIO.GetDebugEscapeSeq(), UIO.DISPLAY_RESET_ESCAPE_SEQ, text))
            else:
                print('DEBUG: {}'.format(text))

    def warn(self, text):
        """@brief Present a warning level message to the user.
           @param text The line of text to be presented to the user."""
        if self._colour:
            print('{}WARN{}:  {}'.format(UIO.GetWarnEscapeSeq(), UIO.DISPLAY_RESET_ESCAPE_SEQ, text))
        else:
            print('WARN:  {}'.format(text))

    def error(self, text):
        """@brief Present an error level message to the user.
           @param text The line of text to be presented to the user."""
        if self._colour:
            print('{}ERROR{}: {}'.format(UIO.GetErrorEscapeSeq(), UIO.DISPLAY_RESET_ESCAPE_SEQ, text))
        else:
            print('ERROR: {}'.format(text))

    def getInput(self, prompt, noEcho=False, stripEOL=True):
        """@brief Get a line of text from the user.
           @param noEcho If True then * are printed when each character is pressed.
           @param stripEOL If True then all end of line (\r, \n) characters are stripped.
           @return The line of text entered by the user."""
        if self._colour:
            if noEcho:
                response = getpass("{}INPUT{}: ".format(UIO.GetInfoEscapeSeq(), UIO.DISPLAY_RESET_ESCAPE_SEQ) + prompt + ": ", sys.stdout)

            else:
                response = input("{}INPUT{}: ".format(UIO.GetInfoEscapeSeq(), UIO.DISPLAY_RESET_ESCAPE_SEQ) + prompt + ": ")

        else:
            if noEcho:
                response = getpass("INPUT: " + prompt + ": ", sys.stdout)

            else:
                response = input("INPUT: " + prompt + ": ")

        if stripEOL:
            response = response.rstrip('\n')
            response = response.rstrip('\r')

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
