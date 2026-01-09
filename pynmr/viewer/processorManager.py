import os
import dill
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc

import pynmr.model.processor as PROC
import pynmr.model.operations as OPS


class ProcessorManager(qtw.QDialog):
    """Dialog to manage the processor stack."""
    
    # Signal emitted when the active processor changes
    activeProcessorChanged = qtc.pyqtSignal(str)
    # Signal emitted when processors are modified
    processorsModified = qtc.pyqtSignal()
    
    def __init__(self, model=None, dataSetIndex=0, parent=None):
        super().__init__(parent)
        
        if model is None:
            raise ValueError("Model cannot be None")
        
        self.model = model
        self.dataSetIndex = dataSetIndex
        self.parent = parent
        
        # Get the processor stack from the model
        self.processorStack = self.model.dataSets[dataSetIndex].processorStack
        
        self.setWindowTitle("Processor Manager")
        self.resize(800, 600)
        
        self.initUI()
        self.updateProcessorList()
        
    def initUI(self):
        """Initialize the user interface."""
        layout = qtw.QVBoxLayout()
        self.setLayout(layout)
        
        # Top section: Active processor selection
        topLayout = qtw.QHBoxLayout()
        topLayout.addWidget(qtw.QLabel("Active Processor:"))
        
        self.activeProcessorCombo = qtw.QComboBox()
        self.activeProcessorCombo.currentTextChanged.connect(self.onActiveProcessorChanged)
        topLayout.addWidget(self.activeProcessorCombo, 1)
        
        layout.addLayout(topLayout)
        
        # Main section: List of processors with their operations
        self.processorListWidget = qtw.QListWidget()
        self.processorListWidget.setSelectionMode(qtw.QAbstractItemView.SingleSelection)
        self.processorListWidget.currentRowChanged.connect(self.onProcessorSelected)
        layout.addWidget(qtw.QLabel("Processors:"))
        layout.addWidget(self.processorListWidget, 3)
        
        # Operations view for selected processor
        layout.addWidget(qtw.QLabel("Operations in Selected Processor:"))
        self.operationsTextEdit = qtw.QTextEdit()
        self.operationsTextEdit.setReadOnly(True)
        layout.addWidget(self.operationsTextEdit, 2)
        
        # Button section
        buttonLayout = qtw.QHBoxLayout()
        
        self.newButton = qtw.QPushButton("New Processor")
        self.newButton.clicked.connect(self.newProcessor)
        buttonLayout.addWidget(self.newButton)
        
        self.renameButton = qtw.QPushButton("Rename")
        self.renameButton.clicked.connect(self.renameProcessor)
        buttonLayout.addWidget(self.renameButton)
        
        self.deleteButton = qtw.QPushButton("Delete")
        self.deleteButton.clicked.connect(self.deleteProcessor)
        buttonLayout.addWidget(self.deleteButton)
        
        self.loadButton = qtw.QPushButton("Load from File")
        self.loadButton.clicked.connect(self.loadProcessorsFromFile)
        buttonLayout.addWidget(self.loadButton)
        
        self.saveButton = qtw.QPushButton("Save to File")
        self.saveButton.clicked.connect(self.saveProcessorsToFile)
        buttonLayout.addWidget(self.saveButton)
        
        layout.addLayout(buttonLayout)
        
        # Close button
        closeLayout = qtw.QHBoxLayout()
        closeLayout.addStretch()
        closeButton = qtw.QPushButton("Close")
        closeButton.clicked.connect(self.accept)
        closeLayout.addWidget(closeButton)
        layout.addLayout(closeLayout)
        
    def updateProcessorList(self):
        """Update the list of processors displayed."""
        self.processorListWidget.clear()
        self.activeProcessorCombo.clear()
        
        if not hasattr(self.model.dataSets[self.dataSetIndex], 'processorNames'):
            # Initialize processor names if not exists
            self.model.dataSets[self.dataSetIndex].processorNames = {}
            for i, proc in enumerate(self.processorStack):
                self.model.dataSets[self.dataSetIndex].processorNames[f"Processor_{i+1}"] = i
        
        processorNames = self.model.dataSets[self.dataSetIndex].processorNames
        
        for name in processorNames.keys():
            self.processorListWidget.addItem(name)
            self.activeProcessorCombo.addItem(name)
        
        # Set active processor in combo box
        if hasattr(self.model.dataSets[self.dataSetIndex], 'activeProcessorName'):
            activeName = self.model.dataSets[self.dataSetIndex].activeProcessorName
            index = self.activeProcessorCombo.findText(activeName)
            if index >= 0:
                self.activeProcessorCombo.setCurrentIndex(index)
        elif len(processorNames) > 0:
            # Set first processor as active if none is set
            self.model.dataSets[self.dataSetIndex].activeProcessorName = list(processorNames.keys())[0]
            self.activeProcessorCombo.setCurrentIndex(0)
            
    def onProcessorSelected(self, currentRow):
        """Display operations for the selected processor."""
        if currentRow < 0:
            self.operationsTextEdit.clear()
            return
        
        processorName = self.processorListWidget.item(currentRow).text()
        processorNames = self.model.dataSets[self.dataSetIndex].processorNames
        
        if processorName in processorNames:
            processorIndex = processorNames[processorName]
            processor = self.processorStack[processorIndex]
            
            # Display operations
            text = f"<b>{processorName}</b><br><br>"
            text += f"<i>Number of operations: {len(processor.operationStack)}</i><br><br>"
            
            for i, op in enumerate(processor.operationStack):
                text += f"<b>{i+1}. {op.name}</b><br>"
                
                # Display operation parameters
                if hasattr(op, '__dict__'):
                    params = {k: v for k, v in op.__dict__.items() if not k.startswith('_') and k != 'name'}
                    if params:
                        for key, value in params.items():
                            text += f"&nbsp;&nbsp;&nbsp;&nbsp;{key}: {value}<br>"
                text += "<br>"
            
            self.operationsTextEdit.setHtml(text)
    
    def onActiveProcessorChanged(self, processorName):
        """Handle change of active processor."""
        if processorName and processorName in self.model.dataSets[self.dataSetIndex].processorNames:
            self.model.dataSets[self.dataSetIndex].activeProcessorName = processorName
            self.activeProcessorChanged.emit(processorName)
    
    def newProcessor(self):
        """Create a new processor."""
        name, ok = qtw.QInputDialog.getText(self, 'New Processor', 'Enter Processor Name:')
        
        if ok and name:
            if not hasattr(self.model.dataSets[self.dataSetIndex], 'processorNames'):
                self.model.dataSets[self.dataSetIndex].processorNames = {}
            
            processorNames = self.model.dataSets[self.dataSetIndex].processorNames
            
            if name in processorNames:
                qtw.QMessageBox.warning(self, "Error", f"Processor '{name}' already exists!")
                return
            
            # Create a default processor
            data = self.model.dataSets[self.dataSetIndex].data
            newProcessor = PROC.Processor([
                OPS.LeftShift(data.shiftPoints if hasattr(data, 'shiftPoints') else 0),
                OPS.LineBroadening(0.0),
                OPS.ZeroFilling(0),
                OPS.FourierTransform(),
                OPS.SetPPMScale(),
                OPS.Phase0D(0),
                OPS.Phase1D(data.timeShift if hasattr(data, 'timeShift') else 0, unit="time")
            ])
            
            # Add to stack
            self.processorStack.append(newProcessor)
            processorNames[name] = len(self.processorStack) - 1
            
            # Set as active
            self.model.dataSets[self.dataSetIndex].activeProcessorName = name
            
            self.updateProcessorList()
            self.processorsModified.emit()
            
            qtw.QMessageBox.information(self, "Success", f"Processor '{name}' created!")
    
    def renameProcessor(self):
        """Rename the selected processor."""
        currentRow = self.processorListWidget.currentRow()
        if currentRow < 0:
            qtw.QMessageBox.warning(self, "Error", "Please select a processor to rename!")
            return
        
        oldName = self.processorListWidget.item(currentRow).text()
        newName, ok = qtw.QInputDialog.getText(self, 'Rename Processor', 
                                                'Enter New Name:', 
                                                text=oldName)
        
        if ok and newName:
            processorNames = self.model.dataSets[self.dataSetIndex].processorNames
            
            if newName in processorNames and newName != oldName:
                qtw.QMessageBox.warning(self, "Error", f"Processor '{newName}' already exists!")
                return
            
            # Rename
            processorIndex = processorNames[oldName]
            del processorNames[oldName]
            processorNames[newName] = processorIndex
            
            # Update active processor name if necessary
            if hasattr(self.model.dataSets[self.dataSetIndex], 'activeProcessorName'):
                if self.model.dataSets[self.dataSetIndex].activeProcessorName == oldName:
                    self.model.dataSets[self.dataSetIndex].activeProcessorName = newName
            
            self.updateProcessorList()
            self.processorsModified.emit()
    
    def deleteProcessor(self):
        """Delete the selected processor."""
        currentRow = self.processorListWidget.currentRow()
        if currentRow < 0:
            qtw.QMessageBox.warning(self, "Error", "Please select a processor to delete!")
            return
        
        processorName = self.processorListWidget.item(currentRow).text()
        
        # Confirm deletion
        reply = qtw.QMessageBox.question(self, 'Delete Processor', 
                                         f"Are you sure you want to delete '{processorName}'?",
                                         qtw.QMessageBox.Yes | qtw.QMessageBox.No)
        
        if reply == qtw.QMessageBox.No:
            return
        
        processorNames = self.model.dataSets[self.dataSetIndex].processorNames
        
        if len(processorNames) == 1:
            qtw.QMessageBox.warning(self, "Error", "Cannot delete the last processor!")
            return
        
        # Get the index to delete
        processorIndex = processorNames[processorName]
        
        # Remove from stack
        del self.processorStack[processorIndex]
        del processorNames[processorName]
        
        # Update indices for remaining processors
        for name, idx in processorNames.items():
            if idx > processorIndex:
                processorNames[name] = idx - 1
        
        # Update active processor if necessary
        if hasattr(self.model.dataSets[self.dataSetIndex], 'activeProcessorName'):
            if self.model.dataSets[self.dataSetIndex].activeProcessorName == processorName:
                # Set first remaining processor as active
                self.model.dataSets[self.dataSetIndex].activeProcessorName = list(processorNames.keys())[0]
        
        self.updateProcessorList()
        self.processorsModified.emit()
        
        qtw.QMessageBox.information(self, "Success", f"Processor '{processorName}' deleted!")
    
    def loadProcessorsFromFile(self):
        """Load processors from a file with selection dialog."""
        if self.parent and hasattr(self.parent, 'settings'):
            openPath = self.parent.settings.value("openPath", os.path.expanduser('~'))
        else:
            openPath = os.path.expanduser('~')
        
        filePath, _ = qtw.QFileDialog.getOpenFileName(
            self, 
            "Load Processors", 
            openPath, 
            "Pickle Files (*.pickle *.dill);;All Files (*.*)"
        )
        
        if not filePath:
            return
        
        try:
            with open(filePath, 'rb') as f:
                loadedData = dill.load(f)
            
            # Handle different file formats
            if isinstance(loadedData, list):
                processors = loadedData
            elif isinstance(loadedData, PROC.Processor):
                processors = [loadedData]
            else:
                qtw.QMessageBox.warning(self, "Error", "Invalid file format!")
                return
            
            # Show selection dialog if multiple processors
            if len(processors) > 1:
                selectedProcessors = self.showProcessorSelectionDialog(processors)
                if not selectedProcessors:
                    return
            else:
                selectedProcessors = processors
            
            # Add selected processors to stack
            processorNames = self.model.dataSets[self.dataSetIndex].processorNames
            
            for i, proc in enumerate(selectedProcessors):
                # Generate unique name
                baseName = f"Loaded_Processor_{len(processorNames) + 1}"
                name = baseName
                counter = 1
                while name in processorNames:
                    name = f"{baseName}_{counter}"
                    counter += 1
                
                self.processorStack.append(proc)
                processorNames[name] = len(self.processorStack) - 1
            
            self.updateProcessorList()
            self.processorsModified.emit()
            
            qtw.QMessageBox.information(self, "Success", 
                                       f"{len(selectedProcessors)} processor(s) loaded!")
            
        except Exception as e:
            qtw.QMessageBox.critical(self, "Error", f"Failed to load processors:\n{str(e)}")
    
    def showProcessorSelectionDialog(self, processors):
        """Show a dialog to select which processors to load."""
        dialog = qtw.QDialog(self)
        dialog.setWindowTitle("Select Processors to Load")
        dialog.resize(600, 400)
        
        layout = qtw.QVBoxLayout()
        dialog.setLayout(layout)
        
        layout.addWidget(qtw.QLabel(f"Found {len(processors)} processor(s). Select which to load:"))
        
        # List widget with checkboxes
        listWidget = qtw.QListWidget()
        listWidget.setSelectionMode(qtw.QAbstractItemView.MultiSelection)
        
        for i, proc in enumerate(processors):
            numOps = len(proc.operationStack) if hasattr(proc, 'operationStack') else 0
            item = qtw.QListWidgetItem(f"Processor {i+1} ({numOps} operations)")
            listWidget.addItem(item)
            item.setSelected(True)  # Select all by default
        
        layout.addWidget(listWidget)
        
        # Buttons
        buttonLayout = qtw.QHBoxLayout()
        
        selectAllButton = qtw.QPushButton("Select All")
        selectAllButton.clicked.connect(lambda: listWidget.selectAll())
        buttonLayout.addWidget(selectAllButton)
        
        deselectAllButton = qtw.QPushButton("Deselect All")
        deselectAllButton.clicked.connect(lambda: listWidget.clearSelection())
        buttonLayout.addWidget(deselectAllButton)
        
        buttonLayout.addStretch()
        
        okButton = qtw.QPushButton("Load Selected")
        okButton.clicked.connect(dialog.accept)
        buttonLayout.addWidget(okButton)
        
        cancelButton = qtw.QPushButton("Cancel")
        cancelButton.clicked.connect(dialog.reject)
        buttonLayout.addWidget(cancelButton)
        
        layout.addLayout(buttonLayout)
        
        if dialog.exec() == qtw.QDialog.Accepted:
            selectedIndices = [listWidget.row(item) for item in listWidget.selectedItems()]
            return [processors[i] for i in selectedIndices]
        else:
            return []
    
    def saveProcessorsToFile(self):
        """Save all processors to a file."""
        if self.parent and hasattr(self.parent, 'settings'):
            openPath = self.parent.settings.value("openPath", os.path.expanduser('~'))
        else:
            openPath = os.path.expanduser('~')
        
        filePath, _ = qtw.QFileDialog.getSaveFileName(
            self,
            "Save Processors",
            openPath,
            "Pickle Files (*.pickle);;Dill Files (*.dill)"
        )
        
        if not filePath:
            return
        
        try:
            with open(filePath, 'wb') as f:
                dill.dump(self.processorStack, f)
            
            qtw.QMessageBox.information(self, "Success", 
                                       f"{len(self.processorStack)} processor(s) saved!")
        except Exception as e:
            qtw.QMessageBox.critical(self, "Error", f"Failed to save processors:\n{str(e)}")
