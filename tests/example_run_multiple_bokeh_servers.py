import asyncio
import threading
import argparse
import socket

import numpy as np

from time import sleep

from p3lib.uio import UIO
from p3lib.helper import logTraceBack
from p3lib.bokeh_gui import StatusBarWrapper
from p3lib.bokeh_gui import ReadOnlyTableWrapper, SingleAppServer

from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.models import Panel
from bokeh.layouts import column, row, gridplot
from bokeh.plotting import figure, ColumnDataSource
from bokeh.models import DataTable, TableColumn, Div
from bokeh.io.output import output_file

class ExampleAppServer(SingleAppServer):
    """@brief An example of a bokeh server running a single app with specialised functionality."""

    def __init__(self,  pageTitle, updatePollSecs=100):
        """@Constructor
           @param pageTitle The title of the web page that appears in the browser window.
           @param bokehPort The port to run the server on.
           @param updatePollSecs The poll period (in milli seconds) for GUI updates.
           """
        super().__init__()
        self._pageTitle         = pageTitle
        self._updatePollSecs    = updatePollSecs
        self._appInitComplete   = False
        self._figTable          = [[]]
        self._updateCount       = 0

    def app(self, doc):
        """@brief Start the process of creating an app.
           @param doc The document to add the plot to."""
        self._doc = doc
        self._doc.title = self._pageTitle
        #self._doc.theme = "dark_minimal"
        # The status bar can be added to the bottom of the window showing status information.
        self._statusBar = StatusBarWrapper()
        #Setup the callback through which all updates to the GUI will be performed.
        self._doc.add_periodic_callback(self._update, self._updatePollSecs)

    def _addTableHeader(self):
        """@brief Add a table to the top of the page."""
        # The bokeh DataTable does not have a title. This shows how one may be added.
        # The CSS style attribute can be used to set the title text style
        # E.G
        # div = Div(text = 'Table Title', name = "bokeh_div", style={'font-size': '200%', 'color': 'blue', "font-weight": "bold"})
        div = Div(text = 'Table Title', name = "bokeh_div", style={'font-weight': 'bold'})

        infoTable = ReadOnlyTableWrapper(["Column 1", "Column 2", "Column 3", "Column 4", "Column 5", "Column 6"])
        rows = []
        rows.append(["1","2","3","4",5,6])
        rows.append(["10","12","13","14",15,16])
        rows.append(["","","30","40",50,60])
        infoTable.setRows(rows)
        infoTable.getWidget().header_row=False
        infoTable.getWidget().height=50
        # Add the title dic above the table
        titledTable = column(div, infoTable.getWidget(), sizing_mode="scale_both")

        #Add table at the top of the page
        self._figTable.append([titledTable])

    def _getTable(self):
        infoTable = ReadOnlyTableWrapper(["1", "2"])
        rows = []
        rows.append(["MIN",     "1"])
        rows.append(["MAX",     "2"])
        rows.append(["RANGE",   "3"])
        rows.append(["AVG",     "4"])
        infoTable.setRows(rows)
        infoTable.getWidget().width=200
        infoTable.getWidget().sizing_mode = 'stretch_height'
        infoTable.getWidget().header_row=False
        return infoTable.getWidget()

    def _update(self):
        """@brief called periodically to update the plot traces."""
        #If we have reached a point where we have all the data to layout the GUI in the server
        if not self._appInitComplete:
            self._addTableHeader()

            #Single column of plots the width of the page
            t = self._getTable()
            r = row(self._getPlotPanel(), t, height=200)
            self._figTable.append([r])
            t = self._getTable()
            r = row(self._getPlotPanel(), t, height=200)
            self._figTable.append([r])
            t = self._getTable()
            r = row(self._getPlotPanel(), t, height=200)
            self._figTable.append([r])

            self._figTable.append([self._statusBar.getWidget()])

            self._statusBar.setStatus("STATUS BAR TEXT **************************************************************************************************************************************")

            gp = gridplot( children = self._figTable, sizing_mode='stretch_width', toolbar_location="above")
            self._doc.add_root( gp )

            # Only init the app once
            self._appInitComplete = True

        else:
            #Updated every 100 ms
            self._statusBar.setStatus("Update {}".format(self._updateCount))
            self._updateCount = self._updateCount + 1

    def _getPlotPanel(self):
        """@brief Add tab that shows plot data updates."""
        # Set up data
        N = 200
        x = np.linspace(0, 4*np.pi, N)
        y = np.sin(x)
        source = ColumnDataSource(data=dict(x=x, y=y))

        # Set up plot
        plot = figure(title="my sine wave",
                      x_range=[0, 4*np.pi], y_range=[-2.5, 2.5],
                      sizing_mode = 'stretch_both')

        plot.line('x', 'y', source=source, line_width=3, line_alpha=0.6)

        return plot

def main():
    """@brief Program entry point"""
    uio = UIO()

    try:
        parser = argparse.ArgumentParser(description="An example of running the bokeh server in a background thread.\n"\
                                                     ".",
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
        parser.add_argument("-d", "--debug",  action='store_true', help="Enable debugging.")

        parser.epilog = "Example\n"\
                        "\n"

        options = parser.parse_args()

        uio.enableDebug(options.debug)

        #Every delaySecs start a new bokeh server on a different port
        delaySecs = 10
        while True:
            exampleAppServer = ExampleAppServer("PAGE TITLE")
            exampleAppServer.runNonBlockingBokehServer(exampleAppServer.app)
            uio.info("Started server on port {}".format(exampleAppServer.getServerPort()))
            sleep(delaySecs)

    #If the program throws a system exit exception
    except SystemExit:
        pass
    #Don't print error information if CTRL C pressed
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        logTraceBack(uio)

        if options.debug:
            raise
        else:
            uio.error(str(ex))

if __name__== '__main__':
    main()
