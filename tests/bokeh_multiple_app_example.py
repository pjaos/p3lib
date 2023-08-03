import socket
import asyncio
import threading

from time import sleep
import numpy as np

from bokeh.layouts import gridplot
from bokeh.plotting import figure
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.server.server import Server

from p3lib.bokeh_gui import MultiAppServer

class MyMultiAppServer(MultiAppServer):
    """@brief Responsible for providing the required apps."""

    def __init__(self, bokehPort=0):
        """@Constructor
           @param bokehPort The TCP port to run the server on. If left at the default
                  of 0 then a spare TCP port will be used."""
        super().__init__(bokehPort=bokehPort)

    def getAppMethodDict(self):
        """@return A dict containing the last part of the URL that denotes the
                   app to use and the method to call to invoke the app."""
        appMethodDict = {}
        appMethodDict['/']=self._mainApp
        appMethodDict['/app1']=self._app1
        appMethodDict['/app2']=self._app2
        return appMethodDict

    def _mainApp(self, doc):
        """@brief The main application.
           @param doc The document to hold the app."""
        x = np.linspace(0, 4*np.pi, 100)
        y = np.sin(x)

        TOOLS = "pan,wheel_zoom,box_zoom,reset,save,box_select"

        p1 = figure(title="Legend Example", tools=TOOLS)

        p1.circle(x,   y, legend_label="sin(x)")
        p1.circle(x, 2*y, legend_label="2*sin(x)", color="orange")
        p1.circle(x, 3*y, legend_label="3*sin(x)", color="green")

        p1.legend.title = 'Markers'

        p2 = figure(title="Another Legend Example", tools=TOOLS)

        p2.circle(x, y, legend_label="sin(x)")
        p2.line(x, y, legend_label="sin(x)")

        p2.line(x, 2*y, legend_label="2*sin(x)",
                line_dash=(4, 4), line_color="orange", line_width=2)

        p2.square(x, 3*y, legend_label="3*sin(x)", fill_color=None, line_color="green")
        p2.line(x, 3*y, legend_label="3*sin(x)", line_color="green")

        p2.legend.title = 'Lines'
        gp = gridplot([p1, p2], ncols=2, sizing_mode="stretch_both")
        doc.add_root( gp )

    def _app1(self, doc):
        """@brief The app1 application.
           @param doc The document to hold the app."""
        x = np.linspace(0, 4*np.pi, 100)
        y = np.sin(x)

        TOOLS = "pan,wheel_zoom,box_zoom,reset,save,box_select"

        p2 = figure(title="Another Legend Example", tools=TOOLS)

        p2.circle(x, y, legend_label="sin(x)")
        p2.line(x, y, legend_label="sin(x)")

        p2.line(x, 2*y, legend_label="2*sin(x)",
                line_dash=(4, 4), line_color="orange", line_width=2)

        p2.square(x, 3*y, legend_label="3*sin(x)", fill_color=None, line_color="green")
        p2.line(x, 3*y, legend_label="3*sin(x)", line_color="green")

        p2.legend.title = 'Lines'
        gp = gridplot([p2], ncols=1, sizing_mode="stretch_both")
        doc.add_root( gp )

    def _app2(self, doc):
        """@brief The app1 application.
           @param doc The document to hold the app."""
        x = np.linspace(0, 4*np.pi, 100)
        y = np.sin(x)

        TOOLS = "pan,wheel_zoom,box_zoom,reset,save,box_select"

        p2 = figure(title="Another Legend Example", tools=TOOLS)

        p2.circle(x, y, legend_label="sin(x)")
        p2.line(x, y, legend_label="sin(x)")

        p2.line(x, 2*y, legend_label="2*sin(x)",
                line_dash=(4, 4), line_color="red", line_width=2)

        p2.square(x, 3*y, legend_label="3*sin(x)", fill_color=None, line_color="yellow")
        p2.line(x, 3*y, legend_label="3*sin(x)", line_color="yellow")

        p2.legend.title = 'Lines'
        gp = gridplot([p2], ncols=1, sizing_mode="stretch_both")
        doc.add_root( gp )

myMultiAppServer = MyMultiAppServer(bokehPort=9000)

# Call this to block execution in the main thread at this point
myMultiAppServer.runBlockingBokehServer(myMultiAppServer.getAppMethodDict())

# Call this if you wish the main thread to continue execution
#myMultiAppServer.runNonBlockingBokehServer(myMultiAppServer.getAppMethodDict())
count=1
while True:
    sleep(5)
    print(f"Server running: {count}")
    count+=1
