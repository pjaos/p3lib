#!/usr/bin/env python3

import random
from   time import sleep
import threading

from   p3lib.time_series_plot import TimeSeriesPlotter

class TimeSeriesPlotExample(object):
    """An example that shows five separate plots/figures.
       Each figure has a single trace except the first that has three traces.
     """

    def __init__(self):
        self._plotter = None

    def run(self):
        plotPaneWidth = 800
        self._plotter = TimeSeriesPlotter("DOC TITLE")

        fig1 = TimeSeriesPlotter.GetFigure("PLOT 1", "PLOT 1 Y Range", width=plotPaneWidth)
        #Trace index 0
        self._plotter.addTrace(fig1, "Volts")
        #Trace index 1
        self._plotter.addTrace(fig1, "Amps")
        #Trace index 2
        self._plotter.addTrace(fig1, "Watts")

        fig2 = TimeSeriesPlotter.GetFigure("PLOT 2", "PLOT 2 Y Range", width=plotPaneWidth)
        #Trace index 3
        self._plotter.addTrace(fig2, "Distance")

        fig3 = TimeSeriesPlotter.GetFigure("PLOT 3", "PLOT 3 Y Range", width=plotPaneWidth)
        #Trace index 4
        self._plotter.addTrace(fig3, "Height")

        fig4 = TimeSeriesPlotter.GetFigure("PLOT 4", "PLOT 4 Y Range", width=plotPaneWidth)
        #Trace index 5
        self._plotter.addTrace(fig4, "Trains")

        self._plotter.addToRow(fig1)
        self._plotter.addToRow(fig2)
        self._plotter.addRow()
        self._plotter.addToRow(fig3)
        self._plotter.addToRow(fig4)

        plotUpdateThread = threading.Thread(target=updatePlots, args=(self._plotter,))
        plotUpdateThread.setDaemon(True)
        plotUpdateThread.start()

        # If called using the 'python bokeh_demo.py' command then uncomment
        # the following line. Only a single client will be able to connect
        # to the server if this is used.
        self._plotter.runBokehServer()

def updatePlots(plotter):
    min=0
    max=100
    #Server started now we send data to the server to be plotted.
    while plotter.isServerRunning():
        #Trace indexes from 0-5 are valid
        for traceIndex in range(0,6):
            value = min + (max-min)*random.random()
            plotter.addValue(traceIndex, value)
        sleep(1)
        
def main():
    timeSeriesPlotExample = TimeSeriesPlotExample()
    timeSeriesPlotExample.run()

if __name__== '__main__':
    main()
