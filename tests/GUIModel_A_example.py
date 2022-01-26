import  threading

from    time import sleep
from    math import sin
from    p3lib.bokeh_gui import GUIModel_A
from    bokeh.layouts import gridplot
from    bokeh.plotting import figure, show, ColumnDataSource
from    bokeh.palettes import Category10_10
from    bokeh.models import HoverTool

class ExtendedGUIModel_A(GUIModel_A):
    """@brief This example is a single figure (plot area) containing two taces, both sine 
              waves, one double the amplitude of the other.."""

    PLOT_DATA_KEY   = 0             # Key used to identify plot data in dict passed into GUI thread.
    TRACE_NAME_KEY  = "trace_name"  # The key for the name of the trace in the trace HoverTool
    
    @staticmethod
    def GetColumnDataSource():
        """@return the expected column data source."""
        return ColumnDataSource({'x': [], 'y': [], ExtendedGUIModel_A.TRACE_NAME_KEY: []})
    
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
        plotArea = figure(title="Legend Example", tools=tools)
        
        traceName = "sin(x)"
        self._traceNames.append(traceName)
        # Create an object that data can be streamed to to update in real time for trace 0.
        t0Src = ExtendedGUIModel_A.GetColumnDataSource()
        # Create the trace line for trace 0.
        plotArea.line(source=t0Src, legend_label=traceName,   color=self.getNextColor() )
        # Add to the list of sources 
        self._sourceList.append( t0Src )
        # Define the attributes to be displayed when the user hovers over a trace point.
        tooltips=[
            ("X",         "@x{0.0}"),
            ("Y",         "@y{0.0}"),
            ("Trace",     "@{}".format(ExtendedGUIModel_A.TRACE_NAME_KEY))
        ]
        plotArea.add_tools( HoverTool(tooltips=tooltips ) )
                
        #Repeat above for the second trace.
        traceName = "2*sin(x)"
        self._traceNames.append(traceName)
        t1Src = ExtendedGUIModel_A.GetColumnDataSource()
        plotArea.line(source=t1Src, legend_label=traceName,   color=self.getNextColor() )
        self._sourceList.append( t1Src )
       
        #Add the plot area to the grid plot array.
        self._guiTable.append([plotArea])
   
    def _processDict(self, theDict):
        """@brief Called when the dict is received by GUI thread.
           @param theDict A dictionary containing data to be used by GUI thread."""
        # Check the data in the dict. Not really necessary in this case but when multiple 
        # messages are passesd to the GUI thread we need to differentiate between the 
        # message types.  
        if ExtendedGUIModel_A.PLOT_DATA_KEY in theDict:
            # Get the x and y (sin value) data to be plotted
            x,y = theDict[ExtendedGUIModel_A.PLOT_DATA_KEY]
            mul=1
            #Plot on each trace. The second trace has twice the amplitude of the first.
            for src in self._sourceList:
                traceIndex = mul-1
                new = {'x': [x], 
                       'y': [mul*y],
                       ExtendedGUIModel_A.TRACE_NAME_KEY:  [self._traceNames[traceIndex]]}
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
            plotDataDict[ExtendedGUIModel_A.PLOT_DATA_KEY]=(x,y)
            self.send(plotDataDict)
            x = x+0.25
            sleep(0.050)

# Create the GUI
extendedGUIModelA = ExtendedGUIModel_A("PLOT TITLE")
#Start a thread sending data to the ExtendedGUIModel_A instance
getPlotDataThread = threading.Thread(target=extendedGUIModelA.genPlotData)
getPlotDataThread.setDaemon(True)
getPlotDataThread.start()
# Open the browser and show the GUI
extendedGUIModelA.runBlockingBokehServer()


