#!/usr/bin/env python
# -*- coding: utf-8 -*-

import  threading
import  queue
import  os
import  tempfile

from    time import sleep, time
from    datetime import datetime

from    p3lib.json_networking import JSONServer, JsonServerHandler
from    p3lib.bokeh_gui import StatusBarWrapper, SingleAppServer, ReadOnlyTableWrapper

from    bokeh.settings import PrioritizedSetting
from    bokeh.settings import Settings as bokeh_settings
from    bokeh.layouts import gridplot, row, column
from    bokeh.plotting import figure, ColumnDataSource
from    bokeh.palettes import Category20
from    bokeh.models import HoverTool, Div
from    bokeh.models.widgets.buttons import Button
from    bokeh.models.widgets import TextInput
from    bokeh.plotting import output_file, save

# Example code for generating plots from 2D table data is shown at the bottom of this file.

class PSError(Exception):
    pass
           
class StaticPlotParams(object):
    """@brief Holds plot parameters that do not change through the life of a single plot window."""
    
    def __init__(self):
        """@brief Constructor."""
        self.windowTitle            = "UNSET WINDOW TITLE" # The HTML page title for the GUI.
        self.tableColNames          = None      # The names of all the columns in the plot table. Each column is displayed as a row plot in the GUI.
        self.xAxisType              = None      # The type of X axis. Either Table2DPlotServer.FLOAT_X_AXIS_TYPE or Table2DPlotServer.DATETIME_X_AXIS_TYPE.
        self.plotPanelHeight        = 250       # The vertical size in pixels of each individual trace plot panel.
        self.linePlot               = True      # If True then a line plot is displayed. If False then a scatter plot is displayed.
        self.plotLineWidth          = 2         # The width of the line in pixels when al ine plot is displayed.
        self.scatterPlotDotSize     = 8         # The size in pixels of the dot size when a scatter plot is displayed.
        self.theme                  = "dark_minimal" # The Bokeh color theme used for the plots
        self.xAxisName              = None      # The name of the X axis on all plots
        self.singlePanel            = False     # If False each trace is displayed in it's own panel
                                                # Each panel is one above the other.
        self.htmlFile               = None      # The text that appears in the HTML file save text box. 
        self.disableResult          = False     # If True then the Result field on the right hand end of the trace is not displayed.
        self.resultWidth            = 50        # The width in pixels of the result table
        self.resultTitle            = "Result"  # The title of the table where the result of the trace is displayed.

class Table2DPlotServer(object):
    
    """@brief Provides a server that accepts JSON data in the form of a 2D table.
              Each row of which contains one or more plot points in a time series.
              The first column is assumed to be the time (float or dataetime)"""
          
    DEFAULT_HOST            = "localhost"
    DEFAULT_PORT            = 31927
    
    # Valid dict keys for the data received by the server START
    WINDOW_TTLE             = "WINDOW_TTLE"
    TABLE_COLUMNS           = "TABLE_COLUMNS"
    TABLE_ROW               = "TABLE_ROW"
    XAXIS_TYPE              = "XAXIS_TYPE"
    PLOT_PANEL_HEIGHT       = "PLOT_PANEL_HEIGHT"
    LINE_PLOT               = "LINE_PLOT"
    PLOT_LINE_WIDTH         = "PLOT_LINE_WIDTH"
    SCATTER_PLOT_DOT_SIZE   = "SCATTER_PLOT_DOT_SIZE"
    THEME                   = "THEME"
    X_AXIS_NAME             = "X_AXIS_NAME"
    HTML_FILE               = "HTML_FILE"
    DISABLE_RESULT          = "DISABLE_RESULT"
    RESULT_WIDTH            = "RESULT_WIDTH"
    RESULT_TITLE            = "RESULT_TITLE"
    SET_RESULT              = "SET_RESULT" 
    # Valid dict keys for the data received by the server END
    
    # Dict keys for the data sent by the server START
    ERROR   = "ERROR"
    # Dict keys for the data sent by the server END
        
    FLOAT_X_AXIS_TYPE       = 1
    DATETIME_X_AXIS_TYPE    = 2
    VALID_X_AXIS_TYPES      = (FLOAT_X_AXIS_TYPE, DATETIME_X_AXIS_TYPE)
    VALID_THEMES            = ("caliber", "dark_minimal", "light_minimal", "night_sky", "contrast")
    
    @staticmethod
    def GetTimeString(dateTimeInstance):
        """@brief Get a string representation of a datetime instance.
           @param dateTimeInstance The datetime instance to convert to a string."""
        return dateTimeInstance.strftime("%d/%m/%Y-%H:%M:%S.%f")
    
    def __init__(self):
        """@brief Constructor."""
        self._host = Table2DPlotServer.DEFAULT_HOST
        self._port = Table2DPlotServer.DEFAULT_PORT
        self._server = None
        self._bokeh2DTablePlotter = None
        self._bokehServerBasePort = Bokeh2DTablePlotter.BOKEH_SERVER_BASE_PORT
        self.staticPlotParams = StaticPlotParams()

    # Setters start
    
    def setHost(self, host):
        """@brief Set the host address for the server to bind to.
           @param host The servers bind address."""
        self._host = host
        
    def setPort(self, port):
        """@brief Set the port for the server to bind to.
           @param port The servers bind port."""
        self._port = port
    
    # Setters end
                    
    class ServerSessionHandler(JsonServerHandler):
        """@brief Inner class to handle connections to the server."""
        def handle(self):
            errorDict = None
            try:
                while True:
                    
                    # Set static parameters start
                    
                    rxDict = self.rx()
                    if Table2DPlotServer.WINDOW_TTLE in rxDict:
                        wTitle = rxDict[Table2DPlotServer.WINDOW_TTLE]
                        if isinstance(wTitle,str) and len(wTitle) > 0 and len(wTitle) <= 250:
                            self.server.parent.staticPlotParams.windowTitle = wTitle
                        else:
                            errorDict = {Table2DPlotServer.ERROR: f"{Table2DPlotServer.WINDOW_TTLE} must be > 0 and <= 250 characters in length: {wTitle}"}
                        
                    elif Table2DPlotServer.XAXIS_TYPE in rxDict:
                        xAxisType = rxDict[Table2DPlotServer.XAXIS_TYPE]
                        if xAxisType in Table2DPlotServer.VALID_X_AXIS_TYPES:
                            self.server.parent.staticPlotParams.xAxisType = xAxisType
                        else:
                            errorDict = {Table2DPlotServer.ERROR: f"{Table2DPlotServer.XAXIS_TYPE} invalid: {xAxisType}"}
                            
                        
                    elif Table2DPlotServer.PLOT_PANEL_HEIGHT in rxDict:
                        pHeight = rxDict[Table2DPlotServer.PLOT_PANEL_HEIGHT]
                        if pHeight > 10 and pHeight < 2048:
                            self.server.parent.staticPlotParams.plotPanelHeight = pHeight
                        else:
                            errorDict = {Table2DPlotServer.ERROR: f"{Table2DPlotServer.PLOT_PANEL_HEIGHT} invalid: {pHeight} must be > 10 and < 2048"}
                        
                    elif Table2DPlotServer.LINE_PLOT in rxDict:
                        lPlot = rxDict[Table2DPlotServer.LINE_PLOT]
                        if lPlot in (True, False):
                            self.server.parent.staticPlotParams.linePlot = lPlot
                        else:
                            errorDict = {Table2DPlotServer.ERROR: f"{Table2DPlotServer.LINE_PLOT} invalid, must be True of False not {lPlot}"}
                        
                    elif Table2DPlotServer.PLOT_LINE_WIDTH in rxDict:
                        plWidth = rxDict[Table2DPlotServer.PLOT_LINE_WIDTH]
                        if plWidth > 0 and plWidth < 100:
                            self.server.parent.staticPlotParams.plotLineWidth = plWidth
                        else:
                            errorDict = {Table2DPlotServer.ERROR: f"{Table2DPlotServer.PLOT_LINE_WIDTH} invalid, must be > 0 and < 100 not {plWidth}"}
                        
                    elif Table2DPlotServer.SCATTER_PLOT_DOT_SIZE in rxDict:
                        spDotSize = rxDict[Table2DPlotServer.SCATTER_PLOT_DOT_SIZE]
                        if spDotSize > 0 and spDotSize < 250:
                            self.server.parent.staticPlotParams.scatterPlotDotSize = spDotSize
                        else:
                            errorDict = {Table2DPlotServer.ERROR: f"{Table2DPlotServer.SCATTER_PLOT_DOT_SIZE} invalid, must be > 0 and < 250 not {spDotSize}"}                           
                            
                    elif Table2DPlotServer.THEME in rxDict:
                        theme = rxDict[Table2DPlotServer.THEME]
                        if theme in Table2DPlotServer.VALID_THEMES:
                            self.server.parent.staticPlotParams.theme = theme
                        else:
                            errorDict = {Table2DPlotServer.ERROR: f"{Table2DPlotServer.XAXIS_TYPE} invalid: {theme}"}

                    elif Table2DPlotServer.X_AXIS_NAME in rxDict:
                        xAxisName = rxDict[Table2DPlotServer.X_AXIS_NAME]
                        if isinstance(xAxisName,str) and len(xAxisName) > 0 and len(xAxisName) <= 150:
                            self.server.parent.staticPlotParams.xAxisName = xAxisName
                        else:
                            errorDict = {Table2DPlotServer.ERROR: f"{Table2DPlotServer.X_AXIS_NAME} must be > 0 and <= 150 characters in length: {xAxisName}"}

                    elif Table2DPlotServer.HTML_FILE in rxDict:
                        htmlFile = rxDict[Table2DPlotServer.HTML_FILE]
                        if isinstance(htmlFile,str) and len(htmlFile) > 0 and len(htmlFile) <= 250:
                            self.server.parent.staticPlotParams.htmlFile = htmlFile
                        else:
                            errorDict = {Table2DPlotServer.ERROR: f"{Table2DPlotServer.HTML_FILE} must be > 0 and <= 250 characters in length: {htmlFile}"}

                    elif Table2DPlotServer.DISABLE_RESULT in rxDict:
                        disableResult = rxDict[Table2DPlotServer.DISABLE_RESULT]
                        if disableResult in (True, False):
                            self.server.parent.staticPlotParams.disableResult = disableResult
                        else:
                            errorDict = {Table2DPlotServer.ERROR: f"{Table2DPlotServer.DISABLE_RESULT} invalid, must be True of False not {disableResult}"}

                    elif Table2DPlotServer.RESULT_WIDTH in rxDict:
                        resultWidth = rxDict[Table2DPlotServer.RESULT_WIDTH]
                        if resultWidth > 10 and resultWidth < 2048:
                            self.server.parent.staticPlotParams.resultWidth = resultWidth
                        else:
                            errorDict = {Table2DPlotServer.ERROR: f"{Table2DPlotServer.RESULT_WIDTH} invalid: {resultWidth} must be > 10 and < 2048"}
   
                    elif Table2DPlotServer.RESULT_TITLE in rxDict:
                        resultTitle = rxDict[Table2DPlotServer.RESULT_TITLE]
                        if isinstance(resultTitle,str) and len(resultTitle) > 0 and len(resultTitle) <= 250:
                            self.server.parent.staticPlotParams.resultTitle = resultTitle
                        else:
                            errorDict = {Table2DPlotServer.ERROR: f"{Table2DPlotServer.RESULT_TITLE} must be > 0 and <= 250 characters in length: {resultTitle}"}
                    
                    # Set static parameters stop
                            
                    elif Table2DPlotServer.SET_RESULT in rxDict:
                        guiMsg = GUIMessage()
                        guiMsg.type = GUIMessage.RESULT_DATA_TYPE
                        guiMsg.data = rxDict[Table2DPlotServer.SET_RESULT]
                        if self.server.parent._bokeh2DTablePlotter:
                            self.server.parent._bokeh2DTablePlotter.sendMessage(guiMsg)

                    elif Table2DPlotServer.TABLE_COLUMNS in rxDict:
                        self.server.parent.createNewPlot(rxDict[Table2DPlotServer.TABLE_COLUMNS])
                        
                    elif Table2DPlotServer.TABLE_ROW in rxDict:
                        self.server.parent.updatePlot(rxDict[Table2DPlotServer.TABLE_ROW])
                        
                    else:
                        errorDict = {Table2DPlotServer.ERROR: f"{rxDict} contains no valid keys to be processed."}    
                        
                    if errorDict:                    
                        self.tx(self.request, errorDict)
    
            except:
                # PJA TODO show error
                raise
        
    def info(self, msg):
        print(f"INFO:  {msg}")
        
    def createNewPlot(self, tableColList):
        """@brief Create a new plot. Each trace will be a table column.
           @param tableColList The list of 2D table columns."""
        if len(tableColList) < 2:
            raise PSError("BUG: _createNewPlot() called with a list of less than 2 columns.")
        self.staticPlotParams.tableColNames = tableColList
        
        if self.staticPlotParams.xAxisType not in Table2DPlotServer.VALID_X_AXIS_TYPES:
            raise PSError(f"BUG: _createNewPlot() called before {Table2DPlotServer.XAXIS_TYPE} set.") 
        
        # Supress bokeh some bokeh warnings to reduce chatter on stdout/err
        #bokeh_settings.log_level = PrioritizedSetting("log_level", "BOKEH_LOG_LEVEL", default="fatal", dev_default="debug")
        bokeh_settings.log_level = PrioritizedSetting("log_level", "BOKEH_LOG_LEVEL", default="warn", dev_default="warn")
        if not self._bokeh2DTablePlotter or (self._iptGUI and not self._options.overlay):
            self.info("Opening a web browser window.")
            self._bokehServerPort = SingleAppServer.GetNextUnusedPort(basePort=self._bokehServerBasePort+1)
            self._bokeh2DTablePlotter = Bokeh2DTablePlotter(self.staticPlotParams.windowTitle, self._bokehServerPort)
            self._bokeh2DTablePlotter.setStaticPlotParams(self.staticPlotParams)
            self._bokeh2DTablePlotter.runNonBlockingBokehServer(self._bokeh2DTablePlotter.app)
            # Allow a short while for the server to start.
            sleep(0.25)
        
    def updatePlot(self, rowValueList):
        """@brief Update a plot. Each trace will be a table column.
           @param rowData A list of each value to be plotted."""
        self._rowValueList = rowValueList
        if len(self.staticPlotParams.tableColNames) != len(self._rowValueList):
            raise PSError(f"BUG: _updatePlot() called with a list that is not equal to the number of table columns ({self.staticPlotParams.tableColNames}/{self._rowValueList}).")

        guiMessage = GUIMessage()
        guiMessage.type = GUIMessage.TABLE_DATA_TYPE
        guiMessage.data = rowValueList
        self._bokeh2DTablePlotter.sendMessage(guiMessage)
        
    def start(self, blocking=False):
        """@brief Start the server running.
           @param blocking IF True then the server blocks."""
        self._server = JSONServer((self._host, self._port), Table2DPlotServer.ServerSessionHandler)
        self._server.parent = self # Set parent to give inner class access to this classes instance
        self._server = threading.Thread(target=self._server.serve_forever)
        if not blocking:
            self._server.setDaemon(True)
        self._server.start()
        
class GUIMessage(object):
    """@brief Contains the messages passed to the GUI message queue."""

    TABLE_DATA_TYPE     = "TDATA"
    RESULT_DATA_TYPE    = "RDATA"

    def __init__(self):
        self.type = None
        self.data = None
        
    def __repr__(self):
        """@brief Return this instance state as a string."""
        return f"type: {self.type}, data {self.data}"
        
class Bokeh2DTablePlotter(SingleAppServer):
    UPDATE_MSEC             = 100
    MAX_GUI_BLOCK_SECONDS   = 1.0
    BOKEH_SERVER_BASE_PORT  = 36000
    TOOLS = "box_select,box_zoom,lasso_select,pan,xpan,ypan,poly_select,tap,wheel_zoom,xwheel_zoom,ywheel_zoom,xwheel_pan,ywheel_pan,examine,undo,redo,reset,save,xzoom_in,xzoom_out,yzoom_in,yzoom_out,crosshair"
    
    @staticmethod
    def GetColumnDataSource():
        """@return the expected column data source."""
        return ColumnDataSource({'name': [], 'x': [], 'y': []})

    @staticmethod
    def GetTimeValue(xValue):
        """@brief Get the X value time as either a float value or a datetime instance converted from a string."""
        if isinstance(xValue, str):
            timeValue = datetime.strptime(xValue, "%d/%m/%Y-%H:%M:%S.%f") 
        else:
            timeValue = float(xValue)
        return timeValue
            
        
    def __init__(self, docTitle, bokehServerPort):
        """@Constructor.
           @param docTitle The title of the HTML doc page.
           @param bokehServerPort The TCP port to bind the server to."""
        super().__init__(bokehPort=bokehServerPort)
        self.docTitle                   = docTitle
        self._guiInitComplete           = False
        self._guiTable                  = [[]]          # A two dimensional table that holds the GUI components.
        self._msgQueue                  = queue.Queue() # Queue through which messages pass into the GUI thread.
        self._plotColumnDataSourceList  = None
        self._plotFigureList            = None
        self._plotFigureList            = None
        self._plotColorIndex            = 3
        self._pColor                    = None
        self._resultTableList           = []
        
        self._newPlotColor()
        
     # Setters start
     
    def setStaticPlotParams(self, staticPlotParams):
        """@brief Set table columnm names. This must be called before runNonBlockingBokehServer() is called.
           @param staticPlotParams All the parameters that may be set which do not change through the life of the plot."""
        self._staticPlotParams = staticPlotParams
     
    # Setters stop
    
    def sendMessage(self, msgDict):
        """@brief Send a message to the GUI thread.
           @brief msgDict The dict holding the message t be sent to the GUI."""
        self._msgQueue.put(msgDict)
        
    def app(self, doc):
        """@brief create the app to run in the bokeh server.
           @param doc The document to add the plot to."""
        self._doc = doc
        self._doc.title = self.docTitle
        self._doc.theme = self._staticPlotParams.theme
        # The status bar is added to the bottom of the window showing status information.
        self._statusBar = StatusBarWrapper()
        self._doc.add_periodic_callback(self._updateGUI, Bokeh2DTablePlotter.UPDATE_MSEC)
        
    def _updateGUI(self):
        """@brief Called to update the state of the GUI."""
        try:
            self._update()
        except:
            # PJA Handle exception here
            raise 
            
    def _getSaveHTMLComponment(self):
        """@brief Get a component to be used to save plots to an HTML file."""
        saveButton = Button(label="Save HTML File", button_type="success", width=50)
        saveButton.on_click(self._savePlot)

        self.fileToSave = TextInput()
        
        #If the HTML file has been defined then use this
        if self._staticPlotParams.htmlFile:
            self.fileToSave.value = self._staticPlotParams.htmlFile
        else:
            # else set default output file name
            self.fileToSave.value = os.path.join( tempfile.gettempdir(), "result.html" )

        return row(self.fileToSave, saveButton)

    def _savePlot(self):
        """@brief Save an html file with the current GUI state."""
        try:
            htmlFile = self.fileToSave.value
            if len(htmlFile) > 0:
                fileBasename = os.path.basename(htmlFile)
                filePath = htmlFile.replace(fileBasename, "")
                if not htmlFile.endswith(".html"):
                    htmlFile = htmlFile + ".html"
                if os.path.isdir(filePath):
                    if os.access(filePath, os.W_OK):
                        msg = "Saving {}. Please wait...".format(htmlFile)
                        self._setStatus(msg)
                        output_file(filename=htmlFile, title="Static HTML file")
                        save(self._doc)
                        self._setStatus( "Saved {}".format(htmlFile) )
                    else:
                        self._setStatus( "{} exists but no write access.".format(filePath) )
                else:
                    self._setStatus( "{} path not found.".format(filePath) )
            else:
                self._setStatus("Please enter the html file to save.")
                
        except Exception as ex:
            self._setStatus( str(ex) )

    def _setStatus(self, msg):
        """@brief Show a status message in the GUI.
           @param msg The message to show."""
        self._statusBar.setStatus(msg)
        
    def _update(self):
        """@Called periodically to update the GUI state."""
        callTime = time()
        # If the GUI layout is not yet complete
        if not self._guiInitComplete:
            self._addPlots()
            hmtlSaveRow = self._getSaveHTMLComponment()
            self._guiTable.append([hmtlSaveRow])
            # Put the status bar below all the traces.
            self._guiTable.append([self._statusBar.getWidget()])
            gp = gridplot( children = self._guiTable, sizing_mode='stretch_width', toolbar_location="below", merge_tools=True)
            self._doc.add_root( gp )
            self._setStatus("GUI init complete.")
            self._guiInitComplete = True

        #While we have data in the queue to process
        while not self._msgQueue.empty():
            #Don't block the bokeh thread for to long or it will crash.
            if time() > callTime+Bokeh2DTablePlotter.MAX_GUI_BLOCK_SECONDS:
                self._uio.debug("Quit _update() with {} outstanding messages after {:.1f} seconds.".format( self._plotDataQueue.qsize(), time()-callTime ))
                break

            msgReceived = self._msgQueue.get()
            if msgReceived and msgReceived.type == GUIMessage.TABLE_DATA_TYPE:
                self._processPlotPoint(msgReceived.data)
                
            elif msgReceived and msgReceived.type == GUIMessage.RESULT_DATA_TYPE:
                self._processResult(msgReceived.data)
                
    def _getResultTable(self):
        """@brief Get a table to contain the result data.
           @return The table widget."""
        resultTable = ReadOnlyTableWrapper(["results"], showLastRows=-1)
        resultTable.getWidget().width=self._staticPlotParams.resultWidth
        resultTable.getWidget().sizing_mode = 'stretch_height'
        resultTable.getWidget().header_row=False
        div = Div(text = self._staticPlotParams.resultTitle, name = "bokeh_div", styles={'font-weight': 'bold'})
        # Add the title div above the table
        titledTable = column(div, resultTable.getWidget(), sizing_mode="stretch_height")
        self._resultTableList.append(resultTable)
        return titledTable

    def _addPlots(self):
        """@brief Display all the plots to be displayed."""
        self._plotColumnDataSourceList  = []
        self._plotFigureList            = []
        if self._staticPlotParams.tableColNames is None:
            raise PSError("BUG: self._staticPlotParams.tableColNames is None")
        
        # Add plot traces ignoring the first column as we expect this to be a float value or datetime.
        for tableColName in self._staticPlotParams.tableColNames[1:]:
            plotFigure = self._getPlotFigure(tableColName)
            self._plotFigureList.append(plotFigure)
            resultTable = self._getResultTable()
            if self._staticPlotParams.disableResult:
                # Don't add the result table to the GUI layout
                tRow = row(plotFigure, height=self._staticPlotParams.plotPanelHeight)                
            else:
                tRow = row(plotFigure, resultTable, height=self._staticPlotParams.plotPanelHeight)

            self._guiTable.append([tRow])
            
    def _getPlotFigure(self, tableColName):
        """@brief Create a plot figure.
           @param tableColName The name of the trace.
           @return The figure instance."""
        # Add the hover menu for each plot point
        if self._staticPlotParams.xAxisType == Table2DPlotServer.FLOAT_X_AXIS_TYPE:
            tooltips=[
                ("name",         "@name"),
                ("Seconds",      "@x{0.0}"),
                (tableColName,   "@y{0.0}"),
            ]
            xAxisName = "Seconds" # We defailt the X axis name to seconds.
            xAxisType = 'auto'
        
        elif self._staticPlotParams.xAxisType == Table2DPlotServer.DATETIME_X_AXIS_TYPE:
            tooltips=[
                ("name",        "@name"),
                ('date',        "$x{%Y-%m-%d}"), 
                ('time',        "$x{%H:%M:%S}"),
                (tableColName,   "@y{0.0}"),
            ]
            xAxisName = "Time"
            xAxisType = 'datetime'
                    
        else:
            raise PSError(f"BUG: Invalid X Axis type set ({self._staticPlotParams.xAxisType}).")
        
        #If the x axis name is set this overrides the name associated with the x axis type. 
        if self._staticPlotParams.xAxisName:
            xAxisName = self._staticPlotParams.xAxisName
        
        # Set up plot/figure attributes.
        plot = figure(title="", # Don't set the title as the Y axis has the title
                      sizing_mode = 'stretch_both',
                      x_axis_label=xAxisName,
                      y_axis_label=tableColName,
                      tools=Bokeh2DTablePlotter.TOOLS,
                      active_drag="box_zoom",
                      x_axis_type=xAxisType)
            
        # For sliding window of displayed values
#        plot.x_range.follow = "end"
#        from datetime import timedelta
#        plot.x_range.follow_interval = 200
        # timedelta(seconds=50)

        source = Bokeh2DTablePlotter.GetColumnDataSource()
        self._plotColumnDataSourceList.append( source )

        if self._staticPlotParams.linePlot:
            plot.line('x', 'y', source=source, line_width=self._staticPlotParams.plotLineWidth, color=self._pColor)
        else:
            plot.circle('x', 'y', source=source, size=self._staticPlotParams.scatterPlotDotSize, color=self._pColor)
        
        if self._staticPlotParams.xAxisType == Table2DPlotServer.FLOAT_X_AXIS_TYPE:
            plot.add_tools(HoverTool(
                tooltips=tooltips
            ))
                        
        else:
            formatters = {'$x': 'datetime'}
            plot.add_tools(HoverTool(
                tooltips=tooltips,
                formatters=formatters
            ))

        #self._newPlotColor()
        
        return plot
        
    def _newPlotColor(self):
        """@brief Allocate a new color for the plot trace."""
        # Use the next color for the next plot
        self._plotColorIndex += 1
        if self._plotColorIndex > 20:
            self._plotColorIndex = 3
        self._pColor = Category20[20][self._plotColorIndex]

    def _processPlotPoint(self, plotPointList):
        """@brief Update a single plot point for each trace displayed."""
        xValue = Bokeh2DTablePlotter.GetTimeValue(plotPointList[0])
        colNumber = 1
        for plotPoint in plotPointList[1:]:
            plotPoint= {'name': [self._staticPlotParams.tableColNames[colNumber]],
                        'x': [xValue],
                        'y': [plotPointList[colNumber]] }

            if colNumber < len(self._plotColumnDataSourceList)+1:
                self._plotColumnDataSourceList[colNumber-1].stream(plotPoint)
                           
            colNumber += 1           
            
    def _processResult(self, resultList):
        """@brief Process a final result message.
           @param resultList A list of the final results for each column in the table."""
        plotIndex = 0
        for resultTable in self._resultTableList:
            resultTable.setRows( [ [resultList[plotIndex]] ] )
            plotIndex += 1




"""
# Example code. This shows how 2D table data may be plotted. 

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import sleep
from datetime import datetime

from p3lib.table_plot import Table2DPlotServer
from p3lib.json_networking import JSONClient

# This starts the server in the background waiting for the data to be plotted.
table2DPlotServer = Table2DPlotServer()
table2DPlotServer.start()

# Create the client to talk to the above server and send parameters and table data
client = JSONClient(Table2DPlotServer.DEFAULT_HOST, Table2DPlotServer.DEFAULT_PORT)

# Set the X Axis type
# Set X AXIS as a float value values
xAxisTypeDict = {Table2DPlotServer.XAXIS_TYPE: Table2DPlotServer.FLOAT_X_AXIS_TYPE}
# Set X Axis as datetime values
#xAxisTypeDict = {Table2DPlotServer.XAXIS_TYPE: Table2DPlotServer.DATETIME_X_AXIS_TYPE}
client.tx(xAxisTypeDict)

# Set height of each trace panel to 500 pixels (default = 250)
#paramDict = {Table2DPlotServer.PLOT_PANEL_HEIGHT: 500}
#client.tx(paramDict)

# Set the plot line with to 10 pixels rather than the default of 10
#paramDict = {Table2DPlotServer.PLOT_LINE_WIDTH: 10}
#client.tx(paramDict)

# Set scatter plot rather than the default line plot
#paramDict = {Table2DPlotServer.LINE_PLOT: False}
#client.tx(paramDict)

# Set scatter plot dot size rather than the default of 8
#paramDict = {Table2DPlotServer.SCATTER_PLOT_DOT_SIZE: 20}
#client.tx(paramDict)

# Set the color theme for the plot
# Valid strings are caliber,dark_minimal,light_minimal,night_sky,contrast
#paramDict = {Table2DPlotServer.THEME: "night_sky"}
#client.tx(paramDict)

# Force the X axis name. 
# If not set and XAXIS_TYPE = SECONDS_X_AXIS_TYPE the # x axis will be Seconds.
# If not set and XAXIS_TYPE = DATETIME_X_AXIS_TYPE the # x axis will be Time".
#paramDict = {Table2DPlotServer.X_AXIS_NAME: "ABCDEF"}
#client.tx(paramDict)

# Set the html file
#paramDict = {Table2DPlotServer.HTML_FILE: "/home/auser/result.html"}
#client.tx(paramDict)

# Remove the result table from the GUI.
#paramDict = {Table2DPlotServer.DISABLE_RESULT: True}
#client.tx(paramDict)

# Set the width (in pixels) of the result table. 
# If set to small then it will expand to fit the the text. 
#paramDict = {Table2DPlotServer.RESULT_WIDTH: 10}
#client.tx(paramDict)

# Set the title of the result table. By default this is result.
#paramDict = {Table2DPlotServer.RESULT_TITLE: "FINAL RESULT"}
#client.tx(paramDict)


titleDict = {Table2DPlotServer.WINDOW_TTLE: "An example Plot"}
client.tx(titleDict)

headerDict = {Table2DPlotServer.TABLE_COLUMNS: ["Seconds","Value 1","Value 2", "V3", "V4"]}
client.tx(headerDict)

for seconds in range(1,100):
    # Add a plot point for each trace with the X axis as seconds
    rowDict =  {Table2DPlotServer.TABLE_ROW: [seconds, seconds+10, seconds*2, seconds*30, seconds/10.0]}

    # Use this when setting X axis as datetime rather than seconds values.
    # timeStr = Table2DPlotServer.GetTimeString(datetime.now())
    # rowDict =  {Table2DPlotServer.TABLE_ROW: [timeStr, seconds+10, seconds*2]}
    client.tx(rowDict)
    sleep(.02)
    
# Set the final result in the table on the right.
resultDict = {Table2DPlotServer.SET_RESULT: [1.1,2.2,3.3,4.4]}
client.tx(resultDict)

# Stay running to keep server running or saving an HTML file will not work.
while True:
    sleep(1)
    
"""    