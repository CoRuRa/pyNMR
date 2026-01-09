"""This is the abstract model.
There sould be only one instance of the pyNmrDataModel,
and this will contain all data, processors, etc. that are
 visualized by the viewer.

There may however be multiple instances of pyNmrDataSet, each corresponding
to one (possibly multi-dimensional) NMR data set.

The nmrDataModel is passed to the gui for visualization and modification."""

from pynmr.model import region

class pyNmrDataModel(object):
    def __init__(self, dataSet=None):
        self.dataSets = []

        if dataSet:
            self.dataSets.append(dataSet)


class pyNmrDataSet(object):
    def __init__(self, data=None, processor=None, regionStack = region.RegionStack()):
        self.data = data
        self.processorStack = []
        self.processorNames = {}  # Dictionary mapping processor names to indices
        self.activeProcessorName = None  # Name of the currently active processor
        self.regionStack = regionStack
        self.processor = processor

        if processor:
            self.processorStack.append(processor)
            # Initialize with default name
            self.processorNames["Processor_1"] = 0
            self.activeProcessorName = "Processor_1"
            processor.runStack(self.data)
    
    def getActiveProcessor(self):
        """Get the currently active processor."""
        if self.activeProcessorName and self.activeProcessorName in self.processorNames:
            index = self.processorNames[self.activeProcessorName]
            if 0 <= index < len(self.processorStack):
                return self.processorStack[index]
        # Fallback to first processor if available
        if len(self.processorStack) > 0:
            return self.processorStack[0]
        return None
    
    def setActiveProcessor(self, name):
        """Set the active processor by name."""
        if name in self.processorNames:
            self.activeProcessorName = name
            return True
        return False

    # def addProcessor(self, processor):
    #     """Add a processor to the data set."""
    #     self.processorStack.append(processor)
    #     processor.runStack(self.data)