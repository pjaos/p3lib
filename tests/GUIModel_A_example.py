#!/usr/bin/env python3

import  threading
import  argparse
from    time import sleep
from    math import sin, cos, pi

from    bokeh.layouts import gridplot
from    bokeh.plotting import figure, show, ColumnDataSource
from    bokeh.palettes import Category10_10, Category20_20
from    bokeh.models import HoverTool
from    bokeh.io import curdoc

from    p3lib.bokeh_gui import GUIModel_A
from    p3lib.uio import UIO

class DynamicPlotExample(GUIModel_A):
    """@brief This example is a single figure (plot area) containing two traces, both sine 
              waves, one double the amplitude of the other.
              This example can be used as a template for plots that update dynamically as
              data is received."""

    PLOT_DATA_KEY   = 0             # Key used to identify plot data in dict passed into GUI thread.
    TRACE_NAME_KEY  = "trace_name"  # The key for the name of the trace in the trace HoverTool
    
    @staticmethod
    def GetColumnDataSource():
        """@return the expected column data source."""
        return ColumnDataSource({'x': [], 'y': [], DynamicPlotExample.TRACE_NAME_KEY: []})
    
    def __init__(self, docTitle, 
                 bokehServerPort=GUIModel_A.GetNextUnusedPort(), 
                 includeSaveHTML=True, 
                 theme=GUIModel_A.BOKEH_THEME_DARK_MINIMAL):
        """@brief Constuctor.
           @param docTitle The title of the document as displayed in the browser tab.
           @param bokehServerPort The TCP port used for the Bokeh server. If not defined 
                                  then the next available TCP port will be used.
           @param includeSaveHTML If True then widgets will be displayed at the bottom of
                                  the page to allow the user to save the page to an HTML file.
           @param theme           The Bokeh theme to use when displaying the plot area."""
        super().__init__(docTitle, bokehServerPort, includeSaveHTML, theme)
        self._colorIter = iter(Category10_10)
        self._sourceList = []
        self._traceNames = []
        
    def getNextColor(self):
        """@brief A Helper method to get the next trace color.
           @return The name of the next trace color."""
        return next(self._colorIter)
        
    def _initGUI(self):
        """@brief Called to initialise the GUI. All the components of the GUI should 
           be added here. The components must be appended to self._guiTable."""
        # This example shows one figure (plot area) containing two traces.
        tools = "pan,wheel_zoom,box_zoom,reset,save,box_select"
        #Create the plot canvas/figure
        curdoc().title
        plotArea = figure(title=curdoc().title, tools=tools)
        #Don't display legends as the trace may be identified with the HoverTool
        plotArea.legend.visible = False
        
        traceName = "sin(x)"
        self._traceNames.append(traceName)
        # Create an object that data can be streamed to to update in real time for trace 0.
        t0Src = DynamicPlotExample.GetColumnDataSource()
        # Create the trace line for trace 0.
        plotArea.line(source=t0Src, color=self.getNextColor() )
        # Add to the list of sources 
        self._sourceList.append( t0Src )
        # Define the attributes to be displayed when the user hovers over a trace point.
        tooltips=[
            ("X",         "@x{0.0}"),
            ("Y",         "@y{0.0}"),
            ("Trace",     "@{}".format(DynamicPlotExample.TRACE_NAME_KEY))
        ]
        plotArea.add_tools( HoverTool(tooltips=tooltips ) )
                
        #Repeat above for the second trace.
        traceName = "2*sin(x)"
        self._traceNames.append(traceName)
        t1Src = DynamicPlotExample.GetColumnDataSource()
        plotArea.line(source=t1Src, color=self.getNextColor() )
        self._sourceList.append( t1Src )
       
        #Add the plot area to the grid plot array.
        self._guiTable.append([plotArea])
   
    def _processDict(self, theDict):
        """@brief Called when the dict is received by GUI thread.
           @param theDict A dictionary containing data to be used by GUI thread."""
        # Check the data in the dict. Not really necessary in this case but when multiple 
        # messages are passed to the GUI thread we need to differentiate between the 
        # message types.  
        if DynamicPlotExample.PLOT_DATA_KEY in theDict:
            # Get the x and y (sin value) data to be plotted
            x,y = theDict[DynamicPlotExample.PLOT_DATA_KEY]
            mul=1
            #Plot on each trace. The second trace has twice the amplitude of the first.
            for src in self._sourceList:
                traceIndex = mul-1
                new = {'x': [x], 
                       'y': [mul*y],
                       DynamicPlotExample.TRACE_NAME_KEY:  [self._traceNames[traceIndex]]}
                source = self._sourceList[traceIndex]
                source.stream(new)
                mul=mul+1           
        
    def genPlotData(self):
        """@brief Generate data to update the plot."""
        # Generate data to be sent to the GUI thread.
        x=0
        while True:
            y = sin(x)
            plotDataDict = {}
            plotDataDict[DynamicPlotExample.PLOT_DATA_KEY]=(x,y)
            self.send(plotDataDict)
            x = x+0.25
            sleep(0.050)


class StaticPlotExample(GUIModel_A):
    """@brief This example is a single figure (plot area) containing 16 static traces, sine 
              waves, offset from each other.
              This example can be used as a template for plots that update dynamically as
              data is received."""
    
    TRACE_NAME_KEY  = "trace_name"  # The key for the name of the trace in the trace HoverTool
    
    @staticmethod
    def AddExampleData(staticExample):
        """@brief Add example static data to the plot.
                  This adds several sinwaves with differnt phases."""
        p=0
        numTraces = 8
        phaseShiftInDegrees=360/numTraces
        traceCount = 1
        phaseDegrees = 0
        while traceCount <= numTraces:
            xValueList = []
            yValueList = []
            traceName = "{:f} °".format(phaseDegrees)
            for pointCount in range(0,101):
                v = (float(pointCount)/10.0)
                xValueList.append(v)
                yValueList.append( sin(v+p) )
            staticExample.addBeamPlotValues(traceName, xValueList, yValueList)
            p=p+(phaseShiftInDegrees/360.0)*2*pi
            phaseDegrees=phaseDegrees+phaseShiftInDegrees
            traceCount=traceCount+1
        
    def __init__(self, docTitle, 
                 bokehServerPort=GUIModel_A.GetNextUnusedPort(), 
                 includeSaveHTML=True, 
                 theme=GUIModel_A.BOKEH_THEME_DARK_MINIMAL):
        """@brief Constuctor.
           @param docTitle The title of the document as displayed in the browser tab.
           @param bokehServerPort The TCP port used for the Bokeh server. If not defined 
                                  then the next available TCP port will be used.
           @param includeSaveHTML If True then widgets will be displayed at the bottom of
                                  the page to allow the user to save the page to an HTML file.
           @param theme           The Bokeh theme to use when displaying the plot area."""
        super().__init__(docTitle, bokehServerPort, includeSaveHTML, theme)
        self._colorIter = iter(Category20_20)
        self._sourceList = []
        self._traceNames = []
        self._dataSetList = []
        
    def getNextColor(self, restartOnNoColor=True):
        """@brief A Helper method to get the next trace color.
           @return The name of the next trace color."""
        while True:
            try:
                color = next(self._colorIter)
                break
            except StopIteration:
                if restartOnNoColor:
                    self._colorIter = iter(Category20_20)
                else:
                    raise
        return color
        
    def addBeamPlotValues(self, traceName, xValueList, yValueList):
        """@brief Add the plot values. This must be called before runBlockingBokehServer()
                  or runNonBlockingBokehServer is called.
           @param traceName The name of the trace to plot.
           @param xValueList A list of X axis values.
           @param yValueList A list of Y axis values."""
        traceNameList = len(xValueList)*(traceName,)
        data = {'x': xValueList,
                'y': yValueList,
                StaticPlotExample.TRACE_NAME_KEY: traceNameList
                }
        self._dataSetList.append(data)
        
    def _initGUI(self):
        """@brief Called to initialise the GUI. All the components of the GUI should 
           be added here. The components must be appended to self._guiTable."""
        # Show all available tools 
        tools = "box_select,box_zoom,lasso_select,pan,xpan,ypan,poly_select,tap,wheel_zoom,xwheel_zoom,ywheel_zoom,xwheel_pan,ywheel_pan,undo,redo,reset,save,zoom_in,xzoom_in,yzoom_in,zoom_out,xzoom_out,yzoom_out,crosshair"
        #Create the plot canvas/figure
        plotArea = figure(title=curdoc().title, tools=tools)
        
        # Define the attributes to be displayed when the user hovers over a trace point.
        tooltips=[
            ("X",         "@x{0.0}"),
            ("Y",         "@y{0.0}"),
            ("Phase",     "@{}".format(StaticPlotExample.TRACE_NAME_KEY))
        ]
        plotArea.add_tools( HoverTool(tooltips=tooltips ) )
                
        #Create each trace from the data set list.
        for data in self._dataSetList:
            traceName = data[StaticPlotExample.TRACE_NAME_KEY]
            self._traceNames.append(traceName)
            source = ColumnDataSource(data=data)
            plotArea.line(source=source, color=self.getNextColor() )
       
        #Add the plot area to the grid plot array.
        self._guiTable.append([plotArea])
   
    def _processDict(self, theDict):
        """@brief Called when the dict is received by GUI thread.
                  Not used as no dynamic updates are processed by this example."""

def main():
    """@brief Program entry point"""
    uio = UIO()

    try:
        parser = argparse.ArgumentParser(description="Some examples of how the GUIModel_A class may be used.\n"\
                                                     "",
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
        parser.add_argument("--static",         action='store_true', help="An example of a static plot. The default is to show a plot that updates dynamically.")
        parser.add_argument("-d", "--debug",    action='store_true', help="Enable debugging.")

        options = parser.parse_args()

        uio.enableDebug(options.debug)

        if options.static:
            # Create the GUI
            staticPlotExample = StaticPlotExample("A Static Plot")
            staticPlotExample.setUIO(uio)
            StaticPlotExample.AddExampleData(staticPlotExample)
            # Open the browser and show the GUI
            staticPlotExample.runBlockingBokehServer()
        else:
            # Create the GUI
            dynamicPlotExample = DynamicPlotExample("Sine and 2*Sine Traces")
            dynamicPlotExample.setUIO(uio)
            # Open the browser and show the GUI
            dynamicPlotExample.runNonBlockingBokehServer()
            # Call method to send data to the plot and update dynamically. 
            dynamicPlotExample.genPlotData()

    #If the program throws a system exit exception
    except SystemExit:
        pass
    #Don't print error information if CTRL C pressed
    except KeyboardInterrupt:
        pass
    except Exception as ex:

        if options.debug:
            raise
        else:
            uio.error(str(ex))

if __name__== '__main__':
    main()
    



