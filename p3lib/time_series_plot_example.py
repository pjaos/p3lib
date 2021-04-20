#!/usr/bin/env python3

import random
from time import sleep
import  threading

from time_series_plot import TimeSeriesPlotter

class TimeSeriesPlotExample(object):
    """An example that shows five separate plots/figures.
       Each figure has a single trace except the first that has three traces.
     """

    def __init__(self):
        self._plotter = None

    def run(self):

        self._plotter = TimeSeriesPlotter("DOC TITLE", pageTitle="Page title")

        fig1 = TimeSeriesPlotter.GetFigure("PLOT 1", "PLOT 1 Y Range")
        #Trace index 0
        self._plotter.addTrace(fig1, "Volts")
        #Trace index 1
        self._plotter.addTrace(fig1, "Amps")
        #Trace index 2
        self._plotter.addTrace(fig1, "Watts")

        fig2 = TimeSeriesPlotter.GetFigure("PLOT 2", "PLOT 2 Y Range")
        #Trace index 3
        self._plotter.addTrace(fig2, "Distance")

        fig3 = TimeSeriesPlotter.GetFigure("PLOT 3", "PLOT 3 Y Range")
        #Trace index 4
        self._plotter.addTrace(fig3, "Height")

        fig4 = TimeSeriesPlotter.GetFigure("PLOT 4", "PLOT 4 Y Range")
        #Trace index 5
        self._plotter.addTrace(fig4, "Trains")

        fig5 = TimeSeriesPlotter.GetFigure("PLOT 4", "PLOT 4 Y Range")
        #Trace index 6
        self._plotter.addTrace(fig5, "Busses")

        self._plotter.addToRow(fig1)
        self._plotter.addToRow(fig2)
        self._plotter.addRow()
        self._plotter.addToRow(fig3)
        self._plotter.addToRow(fig4)
        self._plotter.addToRow(fig5)

        #The bokeh server runs in a separate thread.
        bt = threading.Thread(target=self._plotter.runBokehServer)
        bt.setDaemon(True)
        bt.start()

        min=0
        max=100
        #Server started now we send data to the server to be plotted.
        while True:
            #Trace indexes from 0-6 are valid
            for traceIndex in range(0,7):
                value = min + (max-min)*random.random()
                self._plotter.addValue(traceIndex, value)
            sleep(1)
        bt.join()

def main():
    timeSeriesPlotExample = TimeSeriesPlotExample()
    timeSeriesPlotExample.run()

if __name__== '__main__':
    main()
