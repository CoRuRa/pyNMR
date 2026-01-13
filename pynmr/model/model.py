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
        self.activeProcessorName = None  
        self.regionStack = regionStack
        self.processor = processor

        if processor:
            self.processorStack.append(processor)
            processor.runStack(self.data)
    
    def getActiveProcessor(self):
        """Get the currently active processor."""
        processorNames = {proc.name: idx for idx, proc in enumerate(self.processorStack) if hasattr(proc, 'name') and proc.name is not None}
        if self.activeProcessorName in processorNames:
            index = processorNames[self.activeProcessorName]
            if 0 <= index < len(self.processorStack):
                return self.processorStack[index]
        if len(self.processorStack) > 0:
            return self.processorStack[0]
        return None
    
    def getprocessorNames(self):
        """Get a dictionary mapping processor names to their indices."""
        return {(proc.name if (hasattr(proc, 'name') and proc.name is not None) else ''): idx for idx, proc in enumerate(self.processorStack)}
    
    def setprocessorname(self, index, name):
        """Set the name of a processor at a given index."""
        if 0 <= index < len(self.processorStack):
            proc = self.processorStack[index]
            # Skip if it's not a proper object (e.g., a list)
            if not hasattr(proc, '__dict__'):
                return False
            if not hasattr(proc, 'name'):
                proc.name = None
            proc.name = name
            return True
        return False
    
    def setActiveProcessor(self, name):
        """Set the active processor by name."""
        processorNames = {proc.name: idx for idx, proc in enumerate(self.processorStack) if hasattr(proc, 'name') and proc.name is not None}
        if name in processorNames:
            self.activeProcessorName = name
            return True
        return False

    # def addProcessor(self, processor):
    #     """Add a processor to the data set."""
    #     self.processorStack.append(processor)
    #     processor.runStack(self.data)