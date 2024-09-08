#!/usr/bin/env python3

import datetime

from   optparse import OptionParser
from   random import randrange

import plotly.express as px
import plotly.graph_objects as go
from   plotly.subplots import make_subplots

from   p3lib.uio import UIO
from   p3lib.netplotly import NetPlotly

class NetPlotlyDemo(object):
    """@brief Responsible for demonstrating the capabilities of the NetPlotly tool."""

    DEFAULT_HOST_ADDRESS = "localhost"

    def getDataSetA(self):
        """@return A dataset with three traces y = DOWNMBPS, DOWNMBPS & TEMPC, x = TIMESTAMP"""
        # Generate data to plot
        dataSet = []
        for index in range(0, 10):
            row = {}
            row["DOWNMBPS"] = 10 + index
            row["UPMBPS"] = 2 + index
            row["TEMPC"] = randrange(-40, 75)
            row["TIMESTAMP"] = datetime.datetime.now() + datetime.timedelta(days=index + 1)
            dataSet.append(row)
        return dataSet

    def __init__(self, uio, options):
        self._uio = uio
        self._options = options

        self._netPlotly = NetPlotly(host=self._options.host,
                                    username=self._options.u,
                                    password=self._options.p,
                                    port=self._options.port,
                                    uio=self._uio)

    def singleTimeSeries(self):
        """@brief A single trace with a time X axis"""
        df = px.data.gapminder().query("country=='Canada'")
        fig = px.line(df, x="year", y="lifeExp", title='Life expectancy in Canada')
        self._netPlotly.save(fig, autoOpen=True)
        self._netPlotly.upload()

    def threeTracesTwoPlot(self):
        """@brief Three traces two plots"""
        dataSet = self.getDataSetA()
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Throughput", "LB2120 Temperature"))

        xVals = [row["TIMESTAMP"] for row in dataSet ]
        yVals = [row["DOWNMBPS"] for row in dataSet ]
        fig.add_trace(
            go.Scatter(x=xVals, y=yVals, name="Down"),
            row=1, col=1
        )

        yVals = [row["UPMBPS"] for row in dataSet ]
        fig.add_trace(
            go.Scatter(x=xVals, y=yVals, name="Up"),
            row=1, col=1
        )

        yVals = [row["TEMPC"] for row in dataSet ]
        fig.add_trace(
            go.Scatter(x=xVals, y=yVals, name="Temp"),
            row=1, col=2
        )
        fig.update_layout(title_text="4G Broadband")
        self._netPlotly.save(fig, autoOpen=True)
        self._netPlotly.upload()

    def subPlotsSharedAxis(self):
        trace1 = go.Scatter(
            x=[1, 2, 3],
            y=[2, 3, 4]
        )
        trace2 = go.Scatter(
            x=[20, 30, 40],
            y=[5, 5, 5],
            xaxis="x2",
            yaxis="y"
        )
        trace3 = go.Scatter(
            x=[2, 3, 4],
            y=[600, 700, 800],
            xaxis="x",
            yaxis="y3"
        )
        trace4 = go.Scatter(
            x=[4000, 5000, 6000],
            y=[7000, 8000, 9000],
            xaxis="x4",
            yaxis="y4"
        )
        data = [trace1, trace2, trace3, trace4]
        layout = go.Layout(
            xaxis=dict(
                domain=[0, 0.45]
            ),
            yaxis=dict(
                domain=[0, 0.45]
            ),
            xaxis2=dict(
                domain=[0.55, 1]
            ),
            xaxis4=dict(
                domain=[0.55, 1],
                anchor="y4"
            ),
            yaxis3=dict(
                domain=[0.55, 1]
            ),
            yaxis4=dict(
                domain=[0.55, 1],
                anchor="x4"
            )
        )
        fig = go.Figure(data=data, layout=layout)
        fig.update_layout(title_text='Shared Axis subplots')
        self._netPlotly.save(fig, autoOpen=True)
        self._netPlotly.upload()

    def subPlots4Types(self):
        fig = make_subplots(
            rows=2, cols=2,
            specs=[[{"type": "bar"}, {"type": "barpolar"}],
                   [{"type": "pie"}, {"type": "scatter3d"}]],
            subplot_titles=("1", "2", "3", "4")
        )

        fig.add_trace(go.Bar(y=[2, 3, 1]),
                      row=1, col=1)

        fig.add_trace(go.Barpolar(theta=[0, 45, 90], r=[2, 3, 1]),
                      row=1, col=2)

        fig.add_trace(go.Pie(values=[2, 3, 1]),
                      row=2, col=1)

        fig.add_trace(go.Scatter3d(x=[2, 3, 1], y=[0, 0, 0],
                                   z=[0.5, 1, 2], mode="lines"),
                      row=2, col=2)

        fig.update_layout(height=700, showlegend=True)
        fig.update_layout(title_text="5 different subplots")
        self._netPlotly.save(fig, autoOpen=True)
        self._netPlotly.upload()

    def demo(self):
        """@brief show the demo of all features."""
        self.singleTimeSeries()
        self.threeTracesTwoPlot()
        self.subPlotsSharedAxis()
        self.subPlots4Types()

    def listPlots(self):
        """@brief List the available plots."""
        pl = self._netPlotly.getPlotNameList()
        id=1
        for p in pl:
            self._uio.info("{:02d}: {}".format(id, p))
            id=id+1
        return pl

    def delPlot(self):
        """@allow the user to delete a plot."""
        pl = self.listPlots()
        if len(pl) > 0:
            id = int(self._uio.getInput("Enter the ID of the plot to delete"))
            plotName = pl[id-1]
            self._netPlotly.remove(plotName)
            self._netPlotly.upload()
            self._uio.info("Removed {}".format(plotName))
        else:
            self._uio.info("No plots to delete.")

    def deleteAllPlots(self):
        """@brief Delete the local root folder."""
        self._netPlotly.removeLocalRoot()
        self._netPlotly.upload()
        self._uio.info("All plots have been removed.")

# Very simple cmd line template using optparse
def main():
    uio = UIO()

    opts = OptionParser(version="1.0", description="A demo of the NetPlotly capabilities.")
    opts.add_option("--host",    help="The ssh server address.")
    opts.add_option("-u",        help="The ssh server username.")
    opts.add_option("-p",        help="The ssh server password.")
    opts.add_option("--port",    help="The ssh server port (default=22).", type="int", default=22)
    opts.add_option("--lroot",   help="The local netplotly folder where all html files are stored (default={}).".format(NetPlotly.DEFAULT_LOCAL_ROOT), default=NetPlotly.DEFAULT_LOCAL_ROOT)
    opts.add_option("--rroot",   help="The remote (ssh server) netplotly folder where all html files are stored (default={}).".format(NetPlotly.DEFAULT_LOCAL_ROOT), default=NetPlotly.DEFAULT_LOCAL_ROOT)
    opts.add_option("--list",    help="List the available plots.", action="store_true", default=False)
    opts.add_option("--delete",  help="Delete a single plot.", action="store_true", default=False)
    opts.add_option("--del_all", help="Delete all plots.", action="store_true", default=False)
    opts.add_option("--debug", help="Enable debugging.", action="store_true", default=False)

    try:
        (options, args) = opts.parse_args()
        uio.enableDebug(options.debug)
        netPlotlyDemo = NetPlotlyDemo(uio, options)
        if options.list:
            netPlotlyDemo.listPlots()

        elif options.delete:
            netPlotlyDemo.delPlot()

        elif options.del_all:
            netPlotlyDemo.deleteAllPlots()

        else:
            netPlotlyDemo.demo()

    # If the program throws a system exit exception
    except SystemExit:
        pass
    # Don't print error information if CTRL C pressed
    except KeyboardInterrupt:
        pass
    except Exception as error:
        if options.debug:
            raise

        else:
            uio.error(error)


if __name__ == '__main__':
    main()
