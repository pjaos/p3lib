#!/usr/bin/env python3

import  queue
from    datetime import datetime
import  asyncio
import  itertools

from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.plotting import figure, ColumnDataSource, save, output_file
from bokeh.models import Range1d
from bokeh.layouts import gridplot, column, row
from bokeh.palettes import Category20_20 as palette
from bokeh.models.widgets import CheckboxGroup, Div
from bokeh.models.widgets.buttons import Button
from bokeh.models.widgets import TextInput

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

class TimeSeriesPlotter(object):
    """@brief Responsible for plotting the values."""

    @staticmethod
    def GetFigure(title=None, yAxisName=None, yRangeLimits=None):
        """@brief A Factory method for a figure instance. A figure is a
                  single plot area.
           @param title The title of the figure.
           @param yAxisName The name of the Y axis.
           @param yRangeLimits If None then the Y zxis will auto range.
                               If a list of two numerical values then this
                               defines the min and max Y axis range values.
           @return A figure instance."""
        if yRangeLimits and len(yRangeLimits) == 2:
            yrange = Range1d(yRangeLimits[0], yRangeLimits[1])
        else:
            yrange = None

        fig = figure(title=title,
                     x_axis_type="datetime",
                     x_axis_location="below",
                     y_range=yrange)
        fig.yaxis.axis_label = yAxisName
        return fig

    def __init__(self, docTitle, pageTitle=None, topCtrlPanel=True, bokehPort=5001):
        """@brief Constructor.
           @param docTitle The document title.
           @param pageTitle The title displayed at the top of the web page.
           @param topCtrlPanel If True then a control panel is displayed at the top of the plot.
           @param label The label associated with the trace to plot.
           @param yRangeLimits Limits of the Y axis. By default auto range.
           @param bokehPort The TCP IP port for the bokeh server."""
        self._docTitle=docTitle
        self._pageTitle=pageTitle
        self._topCtrlPanel=topCtrlPanel
        self._bokehPort=bokehPort
        self._figTable=[[]]
        self._srcList = []
        self._evtLoop = None
        self._colors = itertools.cycle(palette)
        self._queue = queue.Queue()
        self._doc = None
        self._plottingEnabled = True
        self._layout = None

    def addRow(self):
        """@brief Add an empty row to the figures."""
        self._figTable.append([])

    def addToRow(self, fig):
        """@brief Add a figure to the end of the current row of figues.
           @param fig The figure to add."""
        self._figTable[-1].append(fig)

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

    def runBokehServer(self):
        """@brief Run the bokeh server. This is a blocking method."""
        apps = {'/': Application(FunctionHandler(self._createPlot))}
        #As this gets run in a thread we need to start an event loop
        evtLoop = asyncio.new_event_loop()
        asyncio.set_event_loop(evtLoop)
        server = Server(apps, port=self._bokehPort)
        server.start()
        #Show the server in a web browser window
        server.io_loop.add_callback(server.show, "/")
        server.io_loop.start()

    def _createPlot(self, doc, ):
        """@brief create a plot figure.
           @param doc The document to add the plot to."""
        self._doc = doc
        self._doc.title = self._docTitle
        grid = gridplot(children = self._figTable, sizing_mode = 'scale_both',  toolbar_location='left')
        checkbox1 = CheckboxGroup(labels=["Plot Data"], active=[0, 1])
        checkbox1.on_change('active', self._checkboxHandler)

        saveButton = Button(label="Save", button_type="success", width=50)
        saveButton.on_click(self._savePlot)

        self._inputFileToSave = TextInput()

        ctrlPanel = row(checkbox1, saveButton, self._inputFileToSave)

        if self._pageTitle:
            text1 = Div(text="""<h1 style="color:blue">{}</h1>""".format(self._pageTitle), width=900, height=50)
            if self._topCtrlPanel:
                self._layout = column(text1, ctrlPanel, row(grid))
            else:
                self._layout = column(text1, row(grid))
        else:
            if self._topCtrlPanel:
                self._layout = column(ctrlPanel, grid)
            else:
                self._layout = column(grid)

        self._doc.add_root(self._layout)
        self._doc.add_periodic_callback(self._update, 100)

    def _update(self):
        """@brief called periodically to update the plot trace."""
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

    def _checkboxHandler(self, attr, old, new):
        """@brief Called when the checkbox is clicked."""
        if 0 in list(new):  # Is first checkbox selected
            self._plottingEnabled = True
        else:
            self._plottingEnabled = False

    def _savePlot(self):
        """@brief Save plot to a single html file. This allows the plots to be
                  analysed later."""
        output_file(self._inputFileToSave.value)
        save(self._layout)
