# !/usr/bin/env python3

"""NiceGui Tools
   Responsible for providing helper classes for nicegui interfaces
   aimed at reducing coding required for a GUI.
"""

import traceback
import os
import platform

from time import sleep
from queue import Queue
from time import time, strftime, localtime
from pathlib import Path

from p3lib.helper import getProgramVersion

from nicegui import ui

class TabbedNiceGui(object):
    """@brief Responsible for starting the providing a tabbed GUI.
              This class is designed to ease the creation of a tabbed GUI interface.
              The contents of each tab can be defined in the subclass.
              The GUI includes a message log area below each tab. Tasks can send messages
              to this log area.
              If a subclass sets the self._logFile attributed then all messages sent to the
              log area are written to a log file with timestamps."""

    # This can be used in the markdown text for a TAB description to give slightly larger text
    # than normal.
    DESCRIP_STYLE               = '<span style="font-size:1.2em;">'
    ENABLE_BUTTONS              = "ENABLE_BUTTONS"
    NOTIFY_DIALOG_INFO          = "NOTIFY_DIALOG_INFO"
    NOTIFY_DIALOG_ERROR         = "NOTIFY_DIALOG_ERROR"
    UPDATE_SECONDS              = "UPDATE_SECONDS"
    INFO_MESSAGE                = "INFO:  "
    WARN_MESSAGE                = "WARN:  "
    ERROR_MESSAGE               = "ERROR: "
    DEBUG_MESSAGE               = "DEBUG: "
    MAX_PROGRESS_VALUE          = 100
    DEFAULT_SERVER_PORT         = 9812
    GUI_TIMER_SECONDS           = 0.1
    PROGRESS_TIMER_SECONDS      = 1.0
    UPDATE_SECONDS              = "UPDATE_SECONDS"
    DEFAULT_GUI_RESPONSE_TIMEOUT= 30.0
    POETRY_CONFIG_FILE          = "pyproject.toml"
    LOCAL_PATH                  = os.path.dirname(os.path.abspath(__file__))

    @staticmethod
    def GetDateTimeStamp():
        """@return The log file date/time stamp """
        return strftime("%Y%m%d%H%M%S", localtime()).lower()

    @staticmethod
    def GetInstallFolder():
        """@return The folder where the apps are installed."""
        installFolder = os.path.dirname(__file__)
        if not os.path.isdir(installFolder):
            raise Exception(f"{installFolder} folder not found.")
        return installFolder

    @staticmethod
    def GetLogFileName(logFilePrefix):
        """@param logFilePrefix The text in the log file name before the timestamp.
           @return The name of the logfile including datetime stamp."""
        dateTimeStamp = TabbedNiceGui.GetDateTimeStamp()
        logFileName = f"{logFilePrefix}_{dateTimeStamp}.log"
        return logFileName

    @staticmethod
    def CheckPort(port):
        """@brief Check the server port.
           @param port The server port."""
        if port < 1024:
            raise Exception("The minimum TCP port that you can bind the GUI server to is 1024.")
        if port > 65535:
            raise Exception("The maximum TCP port that you can bind the GUI server to is 65535.")

    @staticmethod
    def GetProgramVersion():
        """@brief Get the program version from the poetry pyproject.toml file.
           @return The version of the installed program (string value)."""
        return getProgramVersion()

    def __init__(self, debugEnabled, logPath=None):
        """@brief Constructor
           @param debugEnabled True if debugging is enabled.
           @param logPath The path to store log files. If left as None then no log files are created."""
        self._debugEnabled                      = debugEnabled
        self._logFile                           = None              # This must be defined in subclass if logging to a file is required.
        self._buttonList                        = []
        self._logMessageCount                   = 0
        self._updateProgressOnTimer             = False
        self._progressStepValue                 = 0
        self._progressBarStartMessage           = ""
        self._progressBarExpectedMessageList    = []
        self._expectedProgressBarMessageIndex   = 0
        self._expectedProgressBarMsgCount       = 0
        self._programVersion                    = TabbedNiceGui.GetProgramVersion()

        self._logPath           = None
        if logPath:
            self._logPath       = os.path.join(os.path.expanduser('~'), logPath)
            self._ensureLogPathExists()

        self._isWindows         = platform.system() == "Windows"
        self._installFolder     = TabbedNiceGui.GetInstallFolder()

        # Make the install folder our current dir
        os.chdir(self._installFolder)

        # This queue is used to send commands from any thread to the GUI thread.
        self._toGUIQueue = Queue()
        # This queue is for the GUI thread to send messages to other threads
        self._fromGUIQueue = Queue()

    def _ensureLogPathExists(self):
        """@brief Ensure that the log path exists."""
        if not os.path.isdir(self._logPath):
            os.makedirs(self._logPath)

    def getLogPath(self):
        """@return the Log file path if defined."""
        return self._logPath

    # Start ------------------------------
    # Methods that allow the GUI to display standard UIO messages
    # This allows the GUI to be used with code that was written
    # to be used on the command line using UIO class instances
    #
    def info(self, msg):
        """@brief Send a info message to be displayed in the GUI.
                  This can be called from outside the GUI thread.
           @param msg The message to be displayed."""
        msgDict = {TabbedNiceGui.INFO_MESSAGE: str(msg)}
        self.updateGUI(msgDict)

    def warn(self, msg):
        """@brief Send a warning message to be displayed in the GUI.
                  This can be called from outside the GUI thread.
           @param msg The message to be displayed."""
        msgDict = {TabbedNiceGui.WARN_MESSAGE: str(msg)}
        self.updateGUI(msgDict)

    def error(self, msg):
        """@brief Send a error message to be displayed in the GUI.
                  This can be called from outside the GUI thread.
           @param msg The message to be displayed."""
        msgDict = {TabbedNiceGui.ERROR_MESSAGE: str(msg)}
        self.updateGUI(msgDict)

    def infoDialog(self, msg, addToMessageLog=True):
        """@brief Display an info level dialog.
           @param msg The message dialog.
           @param addToMessageLog If True the message will also be added to the message log."""
        msgDict = {TabbedNiceGui.NOTIFY_DIALOG_INFO: str(msg)}
        self.updateGUI(msgDict)
        if addToMessageLog:
            self.info(msg)

    def errorDialog(self, msg, addToMessageLog=True):
        """@brief Display an error level dialog.
           @param msg The message dialog.
           @param addToMessageLog If True the message will also be added to the message log."""
        msgDict = {TabbedNiceGui.NOTIFY_DIALOG_ERROR: str(msg)}
        self.updateGUI(msgDict)
        if addToMessageLog:
            self.error(msg)

    def debug(self, msg):
        """@brief Send a debug message to be displayed in the GUI.
                  This can be called from outside the GUI thread.
           @param msg The message to be displayed."""
        if self._debugEnabled:
            msgDict = {TabbedNiceGui.DEBUG_MESSAGE: str(msg)}
            self.updateGUI(msgDict)

    async def getInput(self, prompt):
        """@brief Allow the user to enter some text.
                  This can be called from outside the GUI thread.
           @param prompt The user prompt."""
        with ui.dialog() as dialog, ui.card():
            inputObj = ui.input(label=prompt)
            with ui.row():
                ui.button('OK', on_click=lambda: dialog.submit('OK'))
                ui.button('Cancel', on_click=lambda: dialog.submit('Cancel'))

        result = await dialog
        if result != 'OK':
            returnText = None
        else:
            returnText = inputObj.value
        return returnText

    def reportException(self, exception):
        """@brief Report an exception.
                  If debug is enabled a full stack trace is displayed.
                  If not then the exception message is displayed.
           @param exception The exception instance."""
        if self._debugEnabled:
            lines = traceback.format_exc().split("\n")
            for line in lines:
                self.error(line)
        if len(exception.args) > 0:
            self.error(exception.args[0])

    def _sendEnableAllButtons(self, state):
        """@brief Send a message to the GUI to enable/disable all the GUI buttons.
                  This can be called from outside the GUI thread.
           @param state If True enable the buttons, else disable them."""
        msgDict = {TabbedNiceGui.ENABLE_BUTTONS: state}
        self.updateGUI(msgDict)

    def updateGUI(self, msgDict):
        """@brief Send a message to the GUI so that it updates itself.
           @param msgDict A dict containing details of how to update the GUI."""
        # Record the seconds when we received the message
        msgDict[TabbedNiceGui.UPDATE_SECONDS]=time()
        self._toGUIQueue.put(msgDict)

    def showTable(self, table, rowSeparatorChar = "-", colSeparatorChar = "|"):
        """@brief Show the contents of a table to the user.
           @param table This must be a list. Each list element must be a table row (list).
                        Each element in each row must be a string.
           @param rowSeparatorChar The character used for horizontal lines to separate table rows.
           @param colSeparatorChar The character used to separate table columns."""
        columnWidths = []
        # Check we have a table to display
        if len(table) == 0:
            raise Exception("No table rows to display")

        # Check all rows have the same number of columns in the table
        colCount = len(table[0])
        for row in table:
            if len(row) != colCount:
                raise Exception(f"{str(row)} column count different from first row ({colCount})")

        for row in table:
            for col in row:
                if not isinstance(col, str):
                    raise Exception(f"Table column is not a string: {col} in {row}")

        # Get the max width for each column
        for col in range(0,colCount):
            maxWidth=0
            for row in table:
                if len(row[col]) > maxWidth:
                    maxWidth = len(row[col])
            columnWidths.append(maxWidth)

        tableWidth = 1
        for columnWidth in columnWidths:
            tableWidth += columnWidth + 3 # Space each side of the column + a column divider character

        # Add the top line of the table
        self.info(rowSeparatorChar*tableWidth)

        # The starting row index
        for rowIndex in range(0, len(table)):
            rowText = colSeparatorChar
            colIndex = 0
            for col in table[rowIndex]:
                colWidth = columnWidths[colIndex]
                rowText = rowText + " " + f"{col:>{colWidth}s}" + " " + colSeparatorChar
                colIndex += 1
            self.info(rowText)
            # Add the row separator line
            self.info(rowSeparatorChar*tableWidth)

    def logAll(self, enabled):
        pass

    def setLogFile(self, logFile):
        pass

    def storeToDebugLog(self, msg):
        pass

    # End ------------------------------

    def _saveLogMsg(self, msg):
        """@brief Save the message to a log file.
           @param msg The message text to be stored in the log file."""
        # If a log file has been set
        if self._logFile:
            # If the log file does not exist
            if not os.path.isfile(self._logFile):
                with open(self._logFile, 'w') as fd:
                    pass
            # Update the log file
            with open(self._logFile, 'a') as fd:
                dateTimeStamp = TabbedNiceGui.GetDateTimeStamp()
                fd.write(dateTimeStamp + ": " + msg + '\n')

    def _getDisplayMsg(self, msg, prefix):
        """@brief Get the msg to display. If the msg does not already have a msg level we add one.
           @param msg The source msg.
           @param prefix The message prefix (level indcator) to add."""
        if msg.startswith(TabbedNiceGui.INFO_MESSAGE) or \
           msg.startswith(TabbedNiceGui.WARN_MESSAGE) or \
           msg.startswith(TabbedNiceGui.ERROR_MESSAGE) or \
           msg.startswith(TabbedNiceGui.DEBUG_MESSAGE):
            _msg = msg
        else:
            _msg = prefix + msg
        return _msg

    def _handleMsg(self, msg):
        """@brief Log a message.
           @param msg the message to the log window and the log file."""
        self._log.push(msg)
        self._saveLogMsg(msg)
        self._logMessageCount += 1
        # We've received a log message so update progress bar if required.
        self._updateProgressBar(msg)
        # Wait a moment for DOM to update, then scroll to the end of the log
        # so that the message just added is visible.
        ui.timer(0.05, lambda: ui.run_javascript("""
            const el = document.querySelector('.my-log');
            if (el) {
                el.scrollTop = el.scrollHeight;
            }
        """), once=True)

    def _infoGT(self, msg):
        """@brief Update an info level message. This must be called from the GUI thread.
           @param msg The message to display."""
        _msg = self._getDisplayMsg(msg, TabbedNiceGui.INFO_MESSAGE)
        self._handleMsg(_msg)

    def _warnGT(self, msg):
        """@brief Update an warning level message. This must be called from the GUI thread.
           @param msg The message to display."""
        _msg = self._getDisplayMsg(msg, TabbedNiceGui.WARN_MESSAGE)
        self._handleMsg(_msg)

    def _errorGT(self, msg):
        """@brief Update an error level message. This must be called from the GUI thread.
           @param msg The message to display."""
        _msg = self._getDisplayMsg(msg, TabbedNiceGui.ERROR_MESSAGE)
        self._handleMsg(_msg)

    def _debugGT(self, msg):
        """@brief Update an debug level message. This must be called from the GUI thread.
           @param msg The message to display."""
        _msg = self._getDisplayMsg(msg, TabbedNiceGui.DEBUG_MESSAGE)
        self._handleMsg(_msg)

    def _clearMessages(self):
        """@brief Clear all messages from the log."""
        self._log.clear()
        self._logMessageCount = 0

    def _getLogMessageCount(self):
        """@return the number of messages written to the log window/file"""
        return self._logMessageCount

    def _enableAllButtons(self, enabled):
        """@brief Enable/Disable all buttons.
           @param enabled True if button is enabled."""
        if enabled:
            for button in self._buttonList:
                button.enable()
            # No buttons are enabled, any executed task must be complete therefor hide the progress bar.
            self._stopProgress()

        else:
            for button in self._buttonList:
                button.disable()
            # If the caller has defined the number of log messages for normal completion
            if self._progressStepValue > 0:
                self._progress.set_visibility(True)

    def guiTimerCallback(self):
        """@called periodically (quickly) to allow updates of the GUI."""
        while not self._toGUIQueue.empty():
            rxMessage = self._toGUIQueue.get()
            if isinstance(rxMessage, dict):
                self._processRXDict(rxMessage)

    def initGUI(self,
                tabNameList,
                tabMethodInitList,
                reload=True,
                address="0.0.0.0",
                port=DEFAULT_SERVER_PORT,
                pageTitle="NiceGUI"):
        """@brief Init the tabbed GUI.
           @param tabNameList A list of the names of each tab to be created.
           @param tabMethodInitList A list of the methods to be called to init each of the above tabs.
                                    The two lists must be the same size.
           @param reload If reload is set False then changes to python files will not cause the server to be restarted.
           @param address The address to bind the server to.
           @param The TCP port to bind the server to.
           @param pageTitle The page title that appears in the browser.
           @param maxLogLines The maximum number of lines to be displayed in the log. Be aware setting this higher will cause the browser to use more memory."""
        with ui.column().classes('h-screen w-screen p4'):
            # A bit of defensive programming.
            if len(tabNameList) != len(tabMethodInitList):
                raise Exception(f"initGUI: BUG: tabNameList ({len(tabNameList)}) and tabMethodInitList ({len(tabMethodInitList)}) are not the same length.")
            tabObjList = []
            with ui.row():
                with ui.tabs().classes('w-full') as tabs:
                    for tabName in tabNameList:
                        tabObj = ui.tab(tabName)
                        tabObjList.append(tabObj)

                with ui.tab_panels(tabs, value=tabObjList[0]).classes('w-full'):
                    for tabObj in tabObjList:
                        with ui.tab_panel(tabObj):
                            tabIndex = tabObjList.index(tabObj)
                            tabMethodInitList[tabIndex]()

            guiLogLevel = "warning"
            if self._debugEnabled:
                guiLogLevel = "debug"

            ui.label("Message Log")
            self._progress = ui.slider(min=0,max=TabbedNiceGui.MAX_PROGRESS_VALUE,step=1)
            self._progress.set_visibility(False)
            self._progress.min = 0
            # Don't allow user to adjust progress bar thumb
            self._progress.disable()
            # Setup the log area to fill the available space in the page vertically and horizontally
            # The 32px is to make space for the vertical scrollbar within the page or it will be
            # shifted out of sight to the right.
            # Previously used self._log = ui.log(max_lines=2000) but the ui.log() does not currently limit data in the log.
            self._log = ui.log().classes('my-log grow w-full max-w-[calc(100%-32px)] overflow-auto box-border')
            self._log.set_visibility(True)

            with ui.row():
                ui.button('Clear Log', on_click=self._clearLog)
                ui.button('Log Message Count', on_click=self._showLogMsgCount)
                ui.button('Quit', on_click=self.close)

            with ui.row():
                ui.label(f"Software Version: {self._programVersion}")

            ui.timer(interval=TabbedNiceGui.GUI_TIMER_SECONDS, callback=self.guiTimerCallback)
            ui.timer(interval=TabbedNiceGui.PROGRESS_TIMER_SECONDS, callback=self.progressTimerCallback)
            ui.run(host=address, port=port, title=pageTitle, dark=True, uvicorn_logging_level=guiLogLevel, reload=reload)

    def progressTimerCallback(self):
        """@brief Time to update the progress bar. We run the timer all the time because there appears to be a
                  bug in the ui.timer instance. Calling cancel() does not appear to cancel the timer."""
        if self._updateProgressOnTimer and self._progress.visible:
            # Increment the progress bar
            self._progress.set_value( self._progress.value + self._progressStepValue )

    def _startProgress(self, durationSeconds=0, startMessage=None, expectedMsgList=[], expectedMsgCount=0):
        """@brief Start a timer that will update the progress bar.
                  The progress bar can simply update on a timer every second with durationSeconds set to the expected length
                  of the task.

                  If startMessage is set to a text string the progress time will not start until the log message area contains
                  the start message.

                  Alternatively if expectedMsgList contains a list of strings we expect to receive then the progress bar is
                  updated as each message is received. The messages may be the entire line of a log message or parts of a
                  log message line.

                  Alternatively if expectedMsgCount is set to a value > 0 then the progress bar is updated as each message is
                  added to the log and reaches 100% when the number of messages added to the log file reaches the expectedMsgCount.

            @param startMessage The text of the log message we expect to receive to trigger the progress bar timer start.
            @param expectedMsgList A list of the expected log file messages.
            @param expectedMsgCount A int value that defines the number of log messages we expect to receive for normal progress
                                    completion."""
        self._progressValue                     = 0
        self._progressBarStartMessage           = ""
        self._progressBarExpectedMessageList    = []
        self._expectedProgressBarMessageIndex   = 0
        self._expectedProgressBarMsgCount       = 0
        self._updateProgressOnTimer             = False
        self._progress.set_value( self._progressValue )
        # If the caller wants to the progress bar to update as the log file message count increases.
        if expectedMsgCount > 0:
            self._expectedProgressBarMsgCount = expectedMsgCount
            self._progressStepValue = TabbedNiceGui.MAX_PROGRESS_VALUE/float(self._expectedProgressBarMsgCount)

        # If the caller wants to update the progress bar on expected messages.
        elif len(expectedMsgList):
            #Use the text of log messages to increment the progress bar.
            self._expectedProgressBarMessageIndex = 0
            self._progressBarExpectedMessageList = expectedMsgList
            self._progressStepValue = TabbedNiceGui.MAX_PROGRESS_VALUE/float(len(expectedMsgList))

        elif durationSeconds > 0:
            # Calc the step size required to give the required duration
            self._progressStepValue = TabbedNiceGui.MAX_PROGRESS_VALUE/float(durationSeconds)
            if startMessage:
                self._progressBarStartMessage = startMessage
            else:
                # Start updating the progress bar now.
                self._updateProgressOnTimer = True

        else:
            raise Exception("BUG: _startProgressTimer() called. len(expectedMsgList)=0 and durationSeconds<=0.")

        self._progress.set_visibility(True)

    def _stopProgress(self):
        """@brief Stop the progress bar being updated and hide it."""
        self._updateProgressOnTimer = False
        self._progress.set_visibility(False)

    def _updateProgressBar(self, msg):
        """@brief Update the progress bar if required when a log message is received. This is called as each message is added to the log.
           @param msg The log message received."""
        # If we update the progress bar as each message is received until we have a log with self._expectedProgressBarMsgCount many messages.
        if self._expectedProgressBarMsgCount > 0:
            self._progressValue = self._progressValue + self._progressStepValue
            self._progress.set_value( self._progressValue )

        # If we have a list of log messages to update the progress bar.
        elif len(self._progressBarExpectedMessageList) > 0:
            if self._expectedProgressBarMessageIndex < len(self._progressBarExpectedMessageList):
                # Get the message we expect to receive next
                expectedMsg = self._progressBarExpectedMessageList[self._expectedProgressBarMessageIndex]
                if msg.find(expectedMsg) != -1:
                    self._progressValue = self._progressValue + self._progressStepValue
                    self._progress.set_value( self._progressValue )
                    self._expectedProgressBarMessageIndex += 1

        # If we have a message that we expect to receive to start the progress bar timer.
        elif self._progressBarStartMessage and len(self._progressBarStartMessage):
            # If we found the start message in the message received.
            if msg.find(self._progressBarStartMessage) != -1:
                # Start updating the progress bar now on the timer.
                self._updateProgressOnTimer = True

    def _initTask(self):
        """@brief Should be called before a task is started."""
        self._enableAllButtons(False)
        self._clearMessages()

    def _clearLog(self):
        """@brief Clear the log text"""
        if self._log:
            self._log.clear()

    def _showLogMsgCount(self):
        """@brief Show the number of log messages"""
        ui.notify(f"{self._getLogMessageCount()} messages in the log.")

    def close(self):
        """@brief Close down the app server."""
        ui.notify("Press 'CTRL C' at command line or close the terminal window to quit.")
        # A subclass close() method can call
        # app.shutdown()
        # if reload=False on ui.run()

    def _appendButtonList(self, button):
        """@brief Add to the button list. These buttons are disabled during the progress of a task.
           @param button The button instance."""
        self._buttonList.append(button)

    def _processRXDict(self, rxDict):
        """@brief Process the dicts received from the GUI message queue.
           @param rxDict The dict received from the GUI message queue."""
        if TabbedNiceGui.INFO_MESSAGE in rxDict:
            msg = rxDict[TabbedNiceGui.INFO_MESSAGE]
            self._infoGT(msg)

        elif TabbedNiceGui.WARN_MESSAGE in rxDict:
            msg = rxDict[TabbedNiceGui.WARN_MESSAGE]
            self._warnGT(msg)

        elif TabbedNiceGui.ERROR_MESSAGE in rxDict:
            msg = rxDict[TabbedNiceGui.ERROR_MESSAGE]
            self._errorGT(msg)

        elif TabbedNiceGui.DEBUG_MESSAGE in rxDict:
            msg = rxDict[TabbedNiceGui.DEBUG_MESSAGE]
            self._debugGT(msg)

        elif TabbedNiceGui.ENABLE_BUTTONS in rxDict:
            state = rxDict[TabbedNiceGui.ENABLE_BUTTONS]
            self._enableAllButtons(state)

        elif TabbedNiceGui.NOTIFY_DIALOG_INFO in rxDict:
            message = rxDict[TabbedNiceGui.NOTIFY_DIALOG_INFO]
            ui.notify(message, close_button='OK', type="positive", position="center")

        elif TabbedNiceGui.NOTIFY_DIALOG_ERROR in rxDict:
            message = rxDict[TabbedNiceGui.NOTIFY_DIALOG_ERROR]
            ui.notify(message, close_button='OK', type="negative", position="center")

        else:

            self._handleGUIUpdate(rxDict)

    def _updateGUI(self, msgDict):
        """@brief Send a message to the GUI so that it updates itself.
           @param msgDict A dict containing details of how to update the GUI."""
        # Record the seconds when we received the message
        msgDict[TabbedNiceGui.UPDATE_SECONDS]=time()
        self._toGUIQueue.put(msgDict)

    def _updateExeThread(self, msgDict):
        """@brief Send a message from the GUI thread to an external (non GUI thread).
           @param msgDict A dict containing messages to be sent to the external thread."""
        # Record the seconds when we received the message
        msgDict[TabbedNiceGui.UPDATE_SECONDS]=time()
        self._fromGUIQueue.put(msgDict)

    def _updateGUIAndWaitForResponse(self, msgDict, timeout=DEFAULT_GUI_RESPONSE_TIMEOUT):
        """@brief Send a message to the GUI and wait for a response.
           @param msgDict The message dictionary to be sent to the GUI.
           @param timeout The number of seconds to wait for a response.
           @return The return dict."""
        timeoutT = time()+timeout
        rxDict = None
        self._updateGUI(msgDict)
        while True:
            if not self._fromGUIQueue.empty():
                rxMessage = self._fromGUIQueue.get()
                if isinstance(rxMessage, dict):
                    rxDict = rxMessage
                    break

            elif time() >= timeoutT:
                raise Exception(f"{timeout} second GUI response timeout.")

            else:
                # Don't spin to fast
                sleep(0.1)

        return rxDict

    def _handleGUIUpdate(self, rxDict):
        """@brief Process the dicts received from the GUI message queue
                  that were not handled by the parent class.
           @param rxDict The dict received from the GUI message queue."""
        raise NotImplementedError("_handleGUIUpdate() is not implemented. Implement this method in a subclass of TabbedNiceGUI")


class YesNoDialog(object):
    """@brief Responsible for displaying a dialog box to the user with a boolean (I.E yes/no, ok/cancel) response."""
    TEXT_INPUT_FIELD_TYPE       = 1
    NUMBER_INPUT_FIELD_TYPE     = 2
    SWITCH_INPUT_FIELD_TYPE     = 3
    DROPDOWN_INPUT_FIELD        = 4
    COLOR_INPUT_FIELD           = 5
    DATE_INPUT_FIELD            = 6
    TIME_INPUT_FIELD            = 7
    KNOB_INPUT_FIELD            = 8
    HOUR_MIN_INPUT_FIELD_TYPE   = 9
    VALID_FIELD_TYPE_LIST   = (TEXT_INPUT_FIELD_TYPE,
                               NUMBER_INPUT_FIELD_TYPE,
                               SWITCH_INPUT_FIELD_TYPE,
                               DROPDOWN_INPUT_FIELD,
                               COLOR_INPUT_FIELD,
                               DATE_INPUT_FIELD,
                               TIME_INPUT_FIELD,
                               KNOB_INPUT_FIELD,
                               HOUR_MIN_INPUT_FIELD_TYPE)

    FIELD_TYPE_KEY          = "FIELD_TYPE_KEY"      # The type of field to be displayed.
    VALUE_KEY               = "VALUE_KEY"           # The value to be displayed in the field when the dialog is displayed.
    MIN_NUMBER_KEY          = "MIN_NUMBER_KEY"      # If the type is NUMBER_INPUT_FIELD_TYPE, the min value that can be entered.
    MAX_NUMBER_KEY          = "MAX_NUMBER_KEY"      # If the type is NUMBER_INPUT_FIELD_TYPE, the max value that can be entered.
    WIDGET_KEY              = "WIDGET_KEY"          # The key to the GUI widget (E.G ui.input, ui.number etc)
    OPTIONS_KEY             = "OPTIONS_KEY"         # Some input fields require a list of options (E.G DROPDOWN_INPUT_FIELD).
    STEP_KEY                = "STEP_KEY"            # The step size for numerical input fields

    def __init__(self,
                 prompt,
                 successMethod,
                 failureMethod=None,
                 successButtonText="Yes",
                 failureButtonText="No"):
        """@brief Constructor"""
        self._dialog                 = None
        self._selectedFile           = None
        self._successButtonText      = None          # The dialogs success button text
        self._failureButtonText      = None          # The dialogs failure button text
        self._prompt                 = None          # The prompt to be displayed in the dialog
        self._successMethod          = None          # The method to be called when the success button is selected.
        self._failureMethod          = None          # The method to be called when the failure button is selected.
        self._inputFieldDict         = {}            # A dict of input field details to be included in the dialog. Can be left as an empty dict if no input fields are required.
                                                     # The key in this dict is the name of the input field that the user sees.
                                                     # The value in this dict is another dict containing details of the input field which may be

        self.setPrompt(prompt)
        self.setSuccessMethod(successMethod)
        self.setFailureMethod(failureMethod)
        self.setSuccessButtonLabel(successButtonText)
        self.setFailureButtonLabel(failureButtonText)


    def addField(self, name, fieldType, value=None, minNumber=None, maxNumber=None, options=None, step=1):
        """@brief Add a field to the dialog.
           @param name          The name of the field to be added.
           @param fieldType     The type of field to be entered.
           @param value         The optional initial value for the field when the dialog is displayed.
           @param minNumber     The optional min value if the fieldType = NUMBER_INPUT_FIELD_TYPE.
           @param maxNumber     The optional max value if the fieldType = NUMBER_INPUT_FIELD_TYPE.
           @param step          The step size for numerical input fields.
           """
        if name and len(name) > 0:
            if fieldType in YesNoDialog.VALID_FIELD_TYPE_LIST:
                self._inputFieldDict[name] = {YesNoDialog.FIELD_TYPE_KEY:     fieldType,
                                              YesNoDialog.VALUE_KEY:          value,
                                              YesNoDialog.MIN_NUMBER_KEY:     minNumber,
                                              YesNoDialog.MAX_NUMBER_KEY:     maxNumber,
                                              YesNoDialog.OPTIONS_KEY:        options,
                                              YesNoDialog.STEP_KEY:           step}

            else:
                raise Exception(f"YesNoDialog.addField() {fieldType} is an invalid field type.")

        else:
            raise Exception("YesNoDialog.addField() name not set.")

    def _init(self):
        """@brief Init the dialog."""
        with ui.dialog() as self._dialog, ui.card():
            ui.label(self._prompt)
            for fieldName in self._inputFieldDict:
                fieldType = self._inputFieldDict[fieldName][YesNoDialog.FIELD_TYPE_KEY]
                if fieldType == YesNoDialog.TEXT_INPUT_FIELD_TYPE:
                    widget = ui.input(label=fieldName).style('width: 200px;')

                elif fieldType == YesNoDialog.NUMBER_INPUT_FIELD_TYPE:
                    value = self._inputFieldDict[fieldName][YesNoDialog.VALUE_KEY]
                    min = self._inputFieldDict[fieldName][YesNoDialog.MIN_NUMBER_KEY]
                    max = self._inputFieldDict[fieldName][YesNoDialog.MAX_NUMBER_KEY]
                    step = self._inputFieldDict[fieldName][YesNoDialog.STEP_KEY]
                    widget = ui.number(label=fieldName,
                                        value=value,
                                        min=min,
                                        max=max,
                                        step=step).style('width: 200px;')

                elif fieldType == YesNoDialog.SWITCH_INPUT_FIELD_TYPE:
                    widget = ui.switch(fieldName)

                elif fieldType == YesNoDialog.DROPDOWN_INPUT_FIELD:
                    #ui.label(fieldName)
                    options = self._inputFieldDict[fieldName][YesNoDialog.OPTIONS_KEY]
                    if options:
                        widget = ui.select(options)
                        widget.tooltip(fieldName)
                    else:
                        raise Exception("BUG: DROPDOWN_INPUT_FIELD defined without defining the options.")

                elif fieldType == YesNoDialog.COLOR_INPUT_FIELD:
                    widget = ui.color_input(label=fieldName)

                elif fieldType == YesNoDialog.DATE_INPUT_FIELD:
                    widget = ui.date()
                    widget.tooltip(fieldName)

                elif fieldType == YesNoDialog.TIME_INPUT_FIELD:
                    widget = ui.time()
                    widget.tooltip(fieldName)

                elif fieldType == YesNoDialog.KNOB_INPUT_FIELD:
                    widget = ui.knob(show_value=True)
                    widget.tooltip(fieldName)

                elif fieldType == YesNoDialog.HOUR_MIN_INPUT_FIELD_TYPE:
                    widget = self._get_input_time_field(fieldName)
                    widget.tooltip(fieldName)

                # Save a ref to the widet in the field dict
                self._inputFieldDict[fieldName][YesNoDialog.WIDGET_KEY] = widget

                # If we have an initial value then set it
                value = self._inputFieldDict[fieldName][YesNoDialog.VALUE_KEY]
                if value:
                    widget.value = value

            with ui.row():
                ui.button(self._successButtonText, on_click=self._internalSuccessMethod)
                ui.button(self._failureButtonText,  on_click=self._internalFailureMethod)

    def _get_input_time_field(self, label):
        """@brief Add a control to allow the user to enter the time as an hour and min.
           @param label The label for the time field.
           @return The input field containing the hour and minute entered."""
        # Put this off the bottom of the mobile screen as most times it will not be needed
        # and there is not enough room on the mobile screen above the plot pane.
        with ui.row().classes('w-full'):
            ui.label(label)
            with ui.row().classes('w-full'):
                time_input = ui.input("Time (HH:MM)")
                with time_input as time:
                    with ui.menu().props('no-parent-event') as menu:
                        with ui.time().bind_value(time):
                            with ui.row().classes('justify-end'):
                                ui.button('Close', on_click=menu.close).props('flat')
                    with time.add_slot('append'):
                        ui.icon('access_time').on('click', menu.open).classes('cursor-pointer')
        return time_input

    def setPrompt(self, prompt):
        """@brief Set the user prompt.
           @param prompt The user prompt."""
        self._prompt = prompt

    def setSuccessMethod(self, successMethod):
        """@brief Set the text of the success button.
           @param successMethod The method called when the user selects the success button."""
        self._successMethod = successMethod

    def setFailureMethod(self, failureMethod):
        """@brief Set the text of the success button.
           @param failureMethod The method called when the user selects the failure button."""
        self._failureMethod = failureMethod

    def setSuccessButtonLabel(self, label):
        """@brief Set the text of the success button.
           @param label The success button text."""
        self._successButtonText = label

    def setFailureButtonLabel(self, label):
        """@brief Set the text of the failure button.
           @param label The failure button text."""
        self._failureButtonText = label

    def show(self):
        """@brief Allow the user to select yes/no, ok/cancel etc in response to a question."""
        self._init()
        self._dialog.open()

    def getValue(self, fieldName):
        """@brief Get the value entered by the user.
           @param fieldName The name of the field entered."""
        value = None
        widget = self._inputFieldDict[fieldName][YesNoDialog.WIDGET_KEY]
        if hasattr(widget, 'value'):
            value = widget.value

        elif isinstance(widget, ui.upload):
            value = self._selectedFile

        return value

    def _internalSuccessMethod(self):
        """@brief Called when the user selects the success button."""
        self.close()
        # Save the entered values for all fields
        for fieldName in self._inputFieldDict:
            widget = self._inputFieldDict[fieldName][YesNoDialog.WIDGET_KEY]
            if hasattr(widget, 'value'):
                self._inputFieldDict[fieldName][YesNoDialog.VALUE_KEY] = self._inputFieldDict[fieldName][YesNoDialog.WIDGET_KEY].value
        # If defined call the method
        if self._successMethod:
            self._successMethod()

    def _internalFailureMethod(self):
        """@brief Called when the user selects the failure button."""
        self.close()
        if self._failureMethod:
            self._failureMethod()

    def close(self):
        """@brief Close the boolean dialog."""
        self._dialog.close()

class local_file_picker(ui.dialog):
    """@brief Allows the user to select local files and folders.
       This is is a change to https://github.com/zauberzeug/nicegui/blob/main/examples/local_file_picker/local_file_picker.py"""

    def __init__(self,
                 directory: str,
                 *,
                 upper_limit: str = None,
                 multiple: bool = False,
                 show_hidden_files: bool = False) -> None:
        """Local File Picker

        This is a simple file picker that allows you to select a file from the local filesystem where NiceGUI is running.

        :param directory: The directory to start in.
        :param upper_limit: The directory to stop at (None: no limit, default: same as the starting directory).
        :param multiple: Whether to allow multiple files to be selected.
        :param show_hidden_files: Whether to show hidden files.
        """
        super().__init__()
        self._selected_drive = None
        # If on a Windows platform attempt to separate the drive and the directory
        if platform.system() == 'Windows' and directory and len(directory) >= 2:
            if directory[0].isalpha() and directory[1] == ':':
                self._selected_drive = directory[:2]
                directory = directory[2:]

        self.path = Path(directory).expanduser()
        if upper_limit is None:
            self.upper_limit = None
        else:
            self.upper_limit = Path(directory if upper_limit == ... else upper_limit).expanduser()
        self.show_hidden_files = show_hidden_files

        with self, ui.card().style('overflow-x: auto; max-width: 100%;'):
            self.add_drives_toggle()
            self.grid = ui.aggrid({
                'columnDefs': [{'field': 'name', 'headerName': 'File'}],
                'rowSelection': 'multiple' if multiple else 'single',
            }, html_columns=[0]).style('min-width: 600px')
            self.grid.on('cellDoubleClicked', self.handle_double_click)
            with ui.row().classes('w-full justify-end'):
                self._select_folder_checkbox = ui.switch('Select Folder')
                #self._select_folder_checkbox = ui.checkbox('Folder')
                self._select_folder_checkbox.tooltip("Select this if you wish to select a folder.")
                ui.button('Cancel', on_click=self.close).props('outline')

        self.update_grid()

    def add_drives_toggle(self):
        if platform.system() == 'Windows':
            import win32api
            drives = win32api.GetLogicalDriveStrings().split('\000')[:-1]
            drive = drives[0]
            # If the caller passed a drive letter select this drive
            if self._selected_drive:
                for drive in drives:
                    if drive.startswith(self._selected_drive):
                        break
            self.drives_toggle = ui.toggle(drives, value=drive, on_change=self.update_drive)

        # Display the current path
        self._path_label = ui.label(str(self.path))

    def update_drive(self):
        self.path = Path(self.drives_toggle.value).expanduser()
        self.update_grid()

    def update_grid(self) -> None:
        paths = list(self.path.glob('*'))
        if not self.show_hidden_files:
            paths = [p for p in paths if not p.name.startswith('.')]
        paths.sort(key=lambda p: p.name.lower())
        paths.sort(key=lambda p: not p.is_dir())

        self.grid.options['rowData'] = [
            {
                'name': f'📁 <strong>{p.name}</strong>' if p.is_dir() else p.name,
                'path': str(p),
            }
            for p in paths
        ]
        if (self.upper_limit is None and self.path != self.path.parent) or \
                (self.upper_limit is not None and self.path != self.upper_limit):
            self.grid.options['rowData'].insert(0, {
                'name': '📁 <strong>..</strong>',
                'path': str(self.path.parent),
            })
        self.grid.update()

    def handle_double_click(self, e) -> None:
        self.path = Path(e.args['data']['path'])
        if self.path.is_dir() and not self._select_folder_checkbox.value:
            self.update_grid()
        else:
            selected = str(self.path)
            # If Windows platform add the drive letter to the path
            if platform.system() == 'Windows':
                if selected.startswith('\\'):
                    selected=selected[1:]
                    selected = self.drives_toggle.value + selected

            self.submit([selected])

        # Update the displayed path
        self._path_label.set_text(str(self.path))