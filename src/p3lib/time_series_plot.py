#!/usr/bin/env python3

import  sys
import  queue
from    datetime import datetime
import  itertools

from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.plotting import figure, ColumnDataSource
from bokeh.models import Range1d
from bokeh.palettes import Category20_20 as palette

from bokeh.plotting import save, output_file
from bokeh.layouts import gridplot, column, row
from bokeh.models.widgets import CheckboxGroup
from bokeh.models.widgets.buttons import Button
from bokeh.models.widgets import TextInput
from bokeh.models import TextAreaInput
from bokeh.models import Panel, Tabs

class TimeSeriesPoint(object):
    """@brief Resonsible for holding a time series point on a trace."""
    def __init__(self, traceIndex, value, timeStamp=None):
        """@brief Constructor
           @param traceIndex The index of the trace this reading should be applied to.
                             The trace index starts at 0 for the top left plot (first
                             trace added) and increments with each call to addTrace()
                             on TimeSeriesPlotter instances.
           @param value The Y value
           @param timeStamp The x Value."""
        self.traceIndex = traceIndex
        if timeStamp:
            self.time = timeStamp
        else:
            self.time = datetime.now()
        self.value = value

class TabbedGUI(object):
    """@brief A Generalised class responsible for plotting real time data."""

    @staticmethod
    def GetFigure(title=None, yAxisName=None, yRangeLimits=None, width=400, height=400):
        """@brief A Factory method to obtain a figure instance.
                  A figure is a single plot area that can contain multiple traces.
           @param title The title of the figure.
           @param yAxisName The name of the Y axis.
           @param yRangeLimits If None then the Y azxis will auto range.
                               If a list of two numerical values then this
                               defines the min and max Y axis range values.
           @param width The width of the plot area in pixels.
           @param height The height of the plot area in pixels.
           @return A figure instance."""
        if yRangeLimits and len(yRangeLimits) == 2:
            yrange = Range1d(yRangeLimits[0], yRangeLimits[1])
        else:
            yrange = None

        fig = figure(title=title,
                     x_axis_type="datetime",
                     x_axis_location="below",
                     y_range=yrange,
                     plot_width=width,
                     plot_height=height)
        fig.yaxis.axis_label = yAxisName
        return fig

    def __init__(self, docTitle, topCtrlPanel=True, bokehPort=9090):
        """@brief Constructor.
           @param docTitle The document title.
           @param topCtrlPanel If True then a control panel is displayed at the top of the plot.
           @param bokehPort The port to run the server on."""
        self._docTitle=docTitle
        self._topCtrlPanel=topCtrlPanel
        self._bokehPort=bokehPort
        self._srcList = []
        self._colors = itertools.cycle(palette)
        self._queue = queue.Queue()
        self._doc = None
        self._plottingEnabled = True
        self._tabList = []
        self._server = None

    def stopServer(self):
        """@brief Stop the bokeh server"""
        sys.exit()

    def addTrace(self, fig, legend_label, line_color=None, line_width=1):
        """@brief Add a trace to a figure.
           @param fig The figure to add the trace to.
           @param line_color The line color
           @param legend_label The text of the label.
           @param line_width The trace line width."""
        src = ColumnDataSource({'x': [], 'y': []})

        #Allocate a line color if one is not defined
        if not line_color:
            line_color = next(self._colors)

        fig.line(source=src,
                 line_color = line_color,
                 legend_label = legend_label,
                 line_width = line_width)
        self._srcList.append(src)

    def _update(self):
        """@brief called periodically to update the plot traces."""
        if self._plottingEnabled:
            while not self._queue.empty():
                timeSeriesPoint = self._queue.get()
                new = {'x': [timeSeriesPoint.time],
                       'y': [timeSeriesPoint.value]}
                source = self._srcList[timeSeriesPoint.traceIndex]
                source.stream(new)

    def addValue(self, traceIndex, value, timeStamp=None):
        """@brief Add a value to be plotted. This adds to queue of values
                  to be plotted the next time _update() is called.
           @param traceIndex The index of the trace this reading should be applied to.
           @param value The Y value to be plotted.
           @param timeStamp The timestamp associated with the value. If not supplied
                            then the timestamp will be created at the time when This
                            method is called."""
        timeSeriesPoint = TimeSeriesPoint(traceIndex, value, timeStamp=timeStamp)
        self._queue.put(timeSeriesPoint)

    def isServerRunning(self):
        """@brief Check if the server is running.
           @param True if the server is running. It may take some time (~ 20 seconds)
                  after the browser is closed before the server session shuts down."""
        serverSessions = "not started"
        if self._server:
            serverSessions = self._server.get_sessions()

        serverRunning = True
        if not serverSessions:
                serverRunning = False

        return serverRunning

    def runBokehServer(self):
        """@brief Run the bokeh server. This is a blocking method."""
        apps = {'/': Application(FunctionHandler(self.createPlot))}
        self._server = Server(apps, port=9000)
        self._server.show("/")
        self._server.run_until_shutdown()

                
class TimeSeriesPlotter(TabbedGUI):
    """@brief Responsible for plotting data on tab 0 with no other tabs."""

    def __init__(self, docTitle, bokehPort=5001):
        """@Constructor"""
        super().__init__(docTitle, bokehPort=bokehPort)
        self._statusAreaInput = None
        self._figTable=[[]]
        self._grid = None

    def addRow(self):
        """@brief Add an empty row to the figures."""
        self._figTable.append([])

    def addToRow(self, fig):
        """@brief Add a figure to the end of the current row of figues.
           @param fig The figure to add."""
        self._figTable[-1].append(fig)

    def createPlot(self, doc, ):
        """@brief create a plot figure.
           @param doc The document to add the plot to."""
        self._doc = doc
        self._doc.title = self._docTitle

        plotPanel = self._getPlotPanel()

        self._tabList.append( Panel(child=plotPanel,  title="Plots") )
        self._doc.add_root( Tabs(tabs=self._tabList) )
        self._doc.add_periodic_callback(self._update, 100)

    def _getPlotPanel(self):
        """@brief Add tab that shows plot data updates."""
        self._grid = gridplot(children = self._figTable, sizing_mode = 'scale_both',  toolbar_location='left')

        checkbox1 = CheckboxGroup(labels=["Plot Data"], active=[0, 1],max_width=70)
        checkbox1.on_change('active', self._checkboxHandler)

        self.fileToSave = TextInput(title="File to save", max_width=150)

        saveButton = Button(label="Save", button_type="success", width=50)
        saveButton.on_click(self._savePlot)

        shutDownButton = Button(label="Quit", button_type="success", width=50)
        shutDownButton.on_click(self.stopServer)

        self._statusAreaInput = TextAreaInput(value="", width_policy="max")
        statusPanel = row([self._statusAreaInput])

        plotRowCtrl = row(children=[checkbox1, saveButton, self.fileToSave, shutDownButton])
        plotPanel = column([plotRowCtrl, self._grid, statusPanel])
        return plotPanel

    def _savePlot(self):
        """@brief Save plot to a single html file. This allows the plots to be
                  analysed later."""
        if self.fileToSave.value:
            if self.fileToSave.value.endswith(".html"):
                filename = self.fileToSave.value
            else:
                filename = self.fileToSave.value + ".html"
            output_file(filename)
            # Save all the plots in the grid to an html file that allows
            # display in a browser and plot manipulation.
            save( self._grid )
            self._statusAreaInput.value = "Saved {}".format(filename)

    def _checkboxHandler(self, attr, old, new):
        """@brief Called when the checkbox is clicked."""
        if 0 in list(new):  # Is first checkbox selected
            self._plottingEnabled = True
            self._statusAreaInput.value = "Plotting enabled"
        else:
            self._plottingEnabled = False
            self._statusAreaInput.value = "Plotting disabled"
