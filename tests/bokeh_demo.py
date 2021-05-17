#!/usr/bin/env python3

# A demo running a bokeh app showing real time plotting and a number of the bokeh widgets.

import  queue
from    datetime import datetime
import  asyncio
import  itertools
import  base64
from    datetime import date
from    random import randint
import  threading
import  random
from    time import sleep

from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.plotting import figure, ColumnDataSource, save, output_file
from bokeh.models import Range1d
from bokeh.layouts import gridplot, column, row
from bokeh.palettes import Category20_20 as palette
from bokeh.models.widgets import CheckboxGroup, Div
from bokeh.models.widgets.buttons import Button
from bokeh.models.widgets import Select
from bokeh.models.widgets import TextInput
from bokeh.models.widgets import Slider
from bokeh.models.widgets import FileInput
from bokeh.models.widgets import Dropdown
from bokeh.models.widgets.groups import RadioGroup
from bokeh.models import CheckboxButtonGroup
from bokeh.models import ColorPicker
from bokeh.models import DataTable, DateFormatter, TableColumn
from bokeh.models import DatePicker
from bokeh.models import DateRangeSlider
from bokeh.models import MultiChoice
from bokeh.models import MultiSelect
from bokeh.models import Paragraph
from bokeh.models import PasswordInput
from bokeh.models import PreText
from bokeh.models import RadioButtonGroup
from bokeh.models import RangeSlider
from bokeh.models import Spinner
from bokeh.models import Panel, Tabs
from bokeh.models import TextAreaInput
from bokeh.models import Toggle
from bokeh.models import CustomJS
from bokeh import events
from pickle import NONE

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

class TimeSeriesGUI(object):
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

    def __init__(self, docTitle, topCtrlPanel=True, bokehPort=5001):
        """@brief Constructor.
           @param docTitle The document title.
           @param topCtrlPanel If True then a control panel is displayed at the top of the plot.
           @param label The label associated with the trace to plot.
           @param yRangeLimits Limits of the Y axis. By default auto range.
           @param bokehPort The TCP IP port for the bokeh server."""
        self._docTitle=docTitle
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
        self._grid = None
        self._tabList = []
        self._server = None

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
        apps = {'/': Application(FunctionHandler(self._createPlot))}
        self._server = Server(apps, port=9000)
        self._server.show("/")
        self._server.run_until_shutdown()

class BokehDemoA(TimeSeriesGUI):
    """@brief Responsible for plotting data on tab 0. Other tabs show how some widgets can be used."""

    def __init__(self, docTitle, topCtrlPanel=True, bokehPort=5001):
        """@Constructor"""
        super().__init__(docTitle, topCtrlPanel=topCtrlPanel, bokehPort=bokehPort)

    def _createPlot(self, doc, ):
        """@brief create a plot figure.
           @param doc The document to add the plot to."""
        self._doc = doc
        self._doc.title = self._docTitle

        plotPanel = self._getPlotPanel()
        demoWidgetsTab = self._getDemoWidgetsTab()
        textTab = self._getTextTab()

        self._tabList.append( Panel(child=plotPanel,  title="Plots") )
        self._tabList.append( Panel(child=demoWidgetsTab,  title="Demo Widets") )
        self._tabList.append( Panel(child=textTab,  title="Text Panel") )

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

        self._statusAreaInput = TextAreaInput(value="", width_policy="max")
        statusPanel = row([self._statusAreaInput])

        plotRowCtrl = row(children=[checkbox1, saveButton, self.fileToSave])
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

    def _getDemoWidgetsTab(self):
        """@brief Add tab that shows some widgets."""
        messageButton = Button(label="Call JS alert(msg)", button_type="success", width=50)
        #This doen't seem very useful as clicking a button to display a dialog is not something
        #thats particularly useful but it shows how javascripot is called.
        msg = "A message from Python"
        source = {"msg": msg}
        callback1 = CustomJS(args=dict(source=source), code="""
            var msg = source['msg']
            alert(msg);
        """)
        messageButton.js_on_event(events.ButtonClick, callback1)

        slider = Slider(start=0, end=30, value=0, step=1, title="Smoothing by N Days", max_width=100)
        slider.on_change('value', self._oldNewHandler)

        self.file_input = FileInput(accept=".*,.json,.txt")
        self.file_input.on_change('value', self._file_input_handler)

        itemList = [("Item 1", "item_1"), ("Item 2", "item_2"), None, ("Item 3", "item_3")]
        dropdown = Dropdown(label="Item List", menu=itemList, max_width=100)
        dropdown.on_click(self._dropDownEventHandler)

        radio = RadioGroup( labels=["line", "SqureCurve", "CubeCurve"], active=0)
        radio.on_change('active', self._oldNewHandler)

        select = Select(title="Select:", value='line', options=["STR1", "STR2", "STR3"])
        select.on_change('value', self._oldNewHandler)

        LABELS = ["Option 1", "Option 2", "Option 3"]
        checkbox_button_group = CheckboxButtonGroup(labels=LABELS, active=[0, 1])
        checkbox_button_group.on_change('active', self._oldNewHandler)

        LABELS = ["Option 1", "Option 2", "Option 3"]
        checkbox_group = CheckboxGroup(labels=LABELS, active=[0, 1])
        checkbox_group.on_change('active', self._oldNewHandler)

        colorPicker = ColorPicker(title="Line Color", max_width=100)

        date_picker = DatePicker(title='Select date', value="2019-09-20", min_date="2019-08-01", max_date="2019-10-30")
        date_picker.on_change('value', self._oldNewHandler)

        date_range_slider = DateRangeSlider(value=(date(2016, 1, 1), date(2016, 12, 31)),
                                            start=date(2015, 1, 1), end=date(2017, 12, 31))
        date_range_slider.on_change('value', self._oldNewHandler)

        OPTIONS = ["foo", "bar", "baz", "quux"]
        multi_choice = MultiChoice(value=["foo", "baz"], options=OPTIONS)
        multi_choice.on_change('value', self._oldNewHandler)

        OPTIONS = [("1", "foo"), ("2", "bar"), ("3", "baz"), ("4", "quux")]
        multi_select = MultiSelect(value=["1", "2"], options=OPTIONS)
        multi_select.on_change('value', self._oldNewHandler)

        LABELS = ["Option 1", "Option 2", "Option 3"]
        radio_button_group = RadioButtonGroup(labels=LABELS, active=0)
        radio_button_group.on_change('active', self._oldNewHandler)

        password_input = PasswordInput(placeholder="enter password...")
        password_input.on_change('value', self._oldNewHandler)

        range_slider = RangeSlider(start=0, end=10, value=(1,9), step=.1, title="Range Slider")
        range_slider.on_change('value', self._oldNewHandler)

        spinner = Spinner(title="Number Spinner", low=1, high=40, step=0.5, value=4, width=80)
        spinner.on_change('value', self._oldNewHandler)

        toggle = Toggle(label="Foo")
        toggle.on_change('active', self._oldNewHandler)

        #to add spacing between items in row set spacing > 0
        ctrlPanel = row(  column([messageButton, slider, self.file_input, dropdown, radio]),\
                          column([select, checkbox_button_group, checkbox_group, colorPicker, date_picker]),\
                          column([date_range_slider, password_input, multi_choice, multi_select, range_slider]),\
                          column([spinner, toggle]))
        return ctrlPanel

    def _getTextTab(self):
        """@brief Add tab that shows some text."""
        #Text panel stuff
        p = Paragraph(text="""Your text is initialized with the 'text' argument.  The
        remaining Paragraph arguments are 'width' and 'height'. For this example, those values
        are 200 and 100, respectively.""",
        width=200, height=100)

        #Add HTML to the page.
        div = Div(text="""Your <a href="https://en.wikipedia.org/wiki/HTML">HTML</a>-supported text is initialized with the <b>text</b> argument.  The
        remaining div arguments are <b>width</b> and <b>height</b>. For this example, those values
        are <i>200</i> and <i>100</i>, respectively.""",
        width=200, height=100)

        # ----Table ---
        data = dict(
                dates=[date(2014, 3, i+1) for i in range(10)],
                downloads=[randint(0, 100) for i in range(10)],
            )
        source = ColumnDataSource(data)

        columns = [
                TableColumn(field="dates", title="Date", formatter=DateFormatter()),
                TableColumn(field="downloads", title="Downloads"),
            ]
        data_table = DataTable(source=source, columns=columns, width=400, height=280)
        ###

        pre = PreText(text="""Your text is initialized with the 'text' argument.
        The remaining Paragraph arguments are 'width' and 'height'. For this example,
        those values are 500 and 100, respectively.""",
        width=500, height=100)

        text_area_input = TextAreaInput(value="default", rows=6, title="Label:")
        # !!! Callback ia not called when test is updated.
        text_area_input.on_change('value', self._oldNewHandler)

        infoPanel = row(  column([div, data_table, p]),\
                           column(pre, text_area_input))
        return infoPanel

    def _checkboxHandler(self, attr, old, new):
        """@brief Called when the checkbox is clicked."""
        if 0 in list(new):  # Is first checkbox selected
            self._plottingEnabled = True
        else:
            self._plottingEnabled = False

    def _dropDownChangeHandler(self, attr, old, new):
        """@brief Called when a dropdown item is selected."""
        print("attr={}, old={}, new={}".format(attr, old, new))

    def _dropDownEventHandler(self, event):
        """@brief Called for dropdown events."""
        print("event.item={}".format(event.item))

    def _file_input_handler(self, attr, old, new):
        #Browsers will not reveal the file path, as a security policy. There’s nothing we can do about that.
        #The data from the file is returned
        textStr = base64.b64decode(new).decode()
        print("File contents={}".format(textStr))

    def _oldNewHandler(self, attr, old, new):
        """@brief Called when a radio group item is selected."""
        print("attr={}, old={}, new={}".format(attr, old, new))


class BokehDemoB(TimeSeriesGUI):
    """@brief Responsible for plotting data on tab 0 with no other tabs."""

    def __init__(self, docTitle, topCtrlPanel=True, bokehPort=5001):
        """@Constructor"""
        super().__init__(docTitle, topCtrlPanel=topCtrlPanel, bokehPort=bokehPort)
        self._statusAreaInput = None

    def _createPlot(self, doc, ):
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

        self._statusAreaInput = TextAreaInput(value="", width_policy="max")
        statusPanel = row([self._statusAreaInput])

        plotRowCtrl = row(children=[checkbox1, saveButton, self.fileToSave])
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
        else:
            self._plottingEnabled = False

def updatePlots(plotter):
    min=0
    max=100
    #Server started now we send data to the server to be plotted.
    while plotter.isServerRunning():
        #Trace indexes from 0-6 are valid
        for traceIndex in range(0,7):
            value = min + (max-min)*random.random()
            plotter.addValue(traceIndex, value)
        sleep(1)

def main():

    # Two different demos are shown.
    plotter = BokehDemoA("Bokeh Real Time Plot And Widgets Demo")
    # A cut down version of the above
    #plotter = BokehDemoB("Bokeh Real Time Plot Demo")

    fig1 = TimeSeriesGUI.GetFigure("PLOT 1", "PLOT 1 Y Range")
    #Trace index 0
    plotter.addTrace(fig1, "Volts")
    #Trace index 1
    plotter.addTrace(fig1, "Amps")
    #Trace index 2
    plotter.addTrace(fig1, "Watts")

    fig2 = TimeSeriesGUI.GetFigure("PLOT 2", "PLOT 2 Y Range")
    #Trace index 3
    plotter.addTrace(fig2, "Distance")

    fig3 = TimeSeriesGUI.GetFigure("PLOT 3", "PLOT 3 Y Range")
    #Trace index 4
    plotter.addTrace(fig3, "Height")

    fig4 = TimeSeriesGUI.GetFigure("PLOT 4", "PLOT 4 Y Range")
    #Trace index 5
    plotter.addTrace(fig4, "Trains")

    fig5 = TimeSeriesGUI.GetFigure("PLOT 4", "PLOT 4 Y Range")
    #Trace index 6
    plotter.addTrace(fig5, "Cars")

    plotter.addToRow(fig1)
    plotter.addToRow(fig2)
    plotter.addRow()
    plotter.addToRow(fig3)
    plotter.addToRow(fig4)
    plotter.addToRow(fig5)

    plotUpdateThread = threading.Thread(target=updatePlots, args=(plotter,))
    plotUpdateThread.setDaemon(True)
    plotUpdateThread.start()

    #This method blocks
    plotter.runBokehServer()

if __name__== '__main__':
    main()
