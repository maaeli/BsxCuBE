import sys
import os
import time
import logging
from curses import ascii
    
from Framework4.GUI import Core
from Framework4.GUI.Core import Property, PropertyGroup, Connection, Signal, Slot                   

from PyQt4 import QtCore, QtGui, Qt, Qwt5 as qwt
from Qub.Widget.DataDisplay import QubDataImageDisplay    
from Qub.Widget.QubActionSet import QubOpenDialogAction, QubPrintPreviewAction, QubZoomListAction, QubZoomAction
from Qub.Widget.QubDialog import QubMaskToolsDialog, QubDataStatWidget
from Qub.Widget.QubColormap import QubColormapDialog
from Qub.Print.QubPrintPreview import getPrintPreviewDialog    

__category__ = "BsxCuBE"



class BsxRobotBrick(Core.BaseBrick):

     
    properties = {}       
    connections = {"samplechanger": Connection("Sample Changer object",
					[Signal('seuTemperatureChanged', 'seu_temperature_changed')
                                       , Signal('storageTemperatureChanged', 'storage_temperature_changed')
                                       , Signal('stateChanged', 'state_changed')
                                        ],
					[],
                                       "sample_changer_connected")}


    def sample_changer_connected(self, sc):        
        if sc is not None:
	    self._sampleChanger = sc
	    self.__updateTimer.start(50)
        else:
	    self.__updateTimer.stop()
   

    def __init__(self, *args, **kargs):
        Core.BaseBrick.__init__(self, *args, **kargs)

    def init(self):
        self.__sampleChangerFrame = None
        self.__robotMoveState = 0
        self.__scanCurveX = {}
        self.__scanCurveY = {}
        self._isDrawing = False        
        self._beamLocation = None
        self._sampleChanger = None
        
        
        self.count = 0
        
        
        self.robotLayout = Qt.QVBoxLayout(self.brick_widget)
        
        self.robotSampleChangerFrameLabel = RobotSampleChangerFrameLabel(self, self.brick_widget)
        self.robotSampleChangerFrameLabel.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.robotSampleChangerFrameLabel.setScaledContents(True)
        self.robotSampleChangerFramePainter = Qt.QPainter()
        self.robotSampleChangerFramePixmap = QtGui.QPixmap()        
        self.robotLayout.addWidget(self.robotSampleChangerFrameLabel)
        
        self.robotHBoxLayout1 = Qt.QHBoxLayout()
        self.robotSampleStateLabel = Qt.QLabel("State", self.brick_widget)
        self.robotHBoxLayout1.addWidget(self.robotSampleStateLabel)         
        self.robotSampleChangerStateLineEdit = Qt.QLineEdit(self.brick_widget)
        self.robotSampleChangerStateLineEdit.setDisabled(True)
        self.robotHBoxLayout1.addWidget(self.robotSampleChangerStateLineEdit)         
        self.robotSampleChangerStatusLineEdit = Qt.QLineEdit(self.brick_widget)
        self.robotSampleChangerStatusLineEdit.setDisabled(True)
        self.robotHBoxLayout1.addWidget(self.robotSampleChangerStatusLineEdit)
        self.robotLayout.addLayout(self.robotHBoxLayout1)

        self.robotHBoxLayout2 = Qt.QHBoxLayout()
        self.robotStorageTemperatureLabel = Qt.QLabel("Temperature (SEU, storage)", self.brick_widget)
        self.robotHBoxLayout2.addWidget(self.robotStorageTemperatureLabel)
        self.robotSEUTemperatureLineEdit = Qt.QLineEdit(self.brick_widget)
        self.robotSEUTemperatureLineEdit.setDisabled(True)
        self.robotHBoxLayout2.addWidget(self.robotSEUTemperatureLineEdit)
        self.robotSEUTemperaturePushButton = Qt.QPushButton("Set", self.brick_widget)
        Qt.QObject.connect(self.robotSEUTemperaturePushButton, Qt.SIGNAL("clicked()"), self.robotSEUTemperaturePushButtonClicked)        
        self.robotHBoxLayout2.addWidget(self.robotSEUTemperaturePushButton)                                          
        self.robotStorageTemperatureLineEdit = Qt.QLineEdit(self.brick_widget)
        self.robotStorageTemperatureLineEdit.setDisabled(True)
        self.robotHBoxLayout2.addWidget(self.robotStorageTemperatureLineEdit)
        self.robotStorageTemperaturePushButton = Qt.QPushButton("Set", self.brick_widget)
        Qt.QObject.connect(self.robotStorageTemperaturePushButton, Qt.SIGNAL("clicked()"), self.robotStorageTemperaturePushButtonClicked)        
        self.robotHBoxLayout2.addWidget(self.robotStorageTemperaturePushButton)      
        self.robotLayout.addLayout(self.robotHBoxLayout2)                                      

        self.robotHBoxLayout3 = Qt.QHBoxLayout()
        self.robotMoveBackwardPushButton = Qt.QPushButton("|<<", self.brick_widget)
        Qt.QObject.connect(self.robotMoveBackwardPushButton, Qt.SIGNAL("pressed()"), self.robotMoveBackwardPushButtonPressed)
        Qt.QObject.connect(self.robotMoveBackwardPushButton, Qt.SIGNAL("released()"), self.robotMoveBackwardPushButtonReleased)                
        self.robotHBoxLayout3.addWidget(self.robotMoveBackwardPushButton)
        self.robotStopPushButton = Qt.QPushButton("||", self.brick_widget)
        Qt.QObject.connect(self.robotStopPushButton, Qt.SIGNAL("clicked()"), self.robotStopPushButtonClicked)        
        self.robotHBoxLayout3.addWidget(self.robotStopPushButton)
        #self.robotMovePushButton = Qt.QPushButton(">", self.brick_widget)        
        #Qt.QObject.connect(self.robotMovePushButton, Qt.SIGNAL("clicked()"), self.robotMovePushButtonClicked)
        #self.robotHBoxLayout3.addWidget(self.robotMovePushButton)
        self.robotMoveForwardPushButton = Qt.QPushButton(">>|", self.brick_widget)        
        Qt.QObject.connect(self.robotMoveForwardPushButton, Qt.SIGNAL("pressed()"), self.robotMoveForwardPushButtonPressed)        
        Qt.QObject.connect(self.robotMoveForwardPushButton, Qt.SIGNAL("released()"), self.robotMoveForwardPushButtonReleased)
        self.robotHBoxLayout3.addWidget(self.robotMoveForwardPushButton)
        self.robotFlowPushButton = Qt.QPushButton("Flow", self.brick_widget)        
        Qt.QObject.connect(self.robotFlowPushButton, Qt.SIGNAL("clicked()"), self.robotFlowPushButtonClicked)        
        self.robotHBoxLayout3.addWidget(self.robotFlowPushButton)
        self.robotRecuperatePushButton = Qt.QPushButton("Recuperate", self.brick_widget)        
        Qt.QObject.connect(self.robotRecuperatePushButton, Qt.SIGNAL("clicked()"), self.robotRecuperatePushButtonClicked)        
        self.robotHBoxLayout3.addWidget(self.robotRecuperatePushButton)                        
        self.robotLayout.addLayout(self.robotHBoxLayout3)
        
        self.robotHBoxLayout4 = Qt.QHBoxLayout()
        self.robotRestartPushButton = Qt.QPushButton("Restart", self.brick_widget)
        self.robotRestartMenu = Qt.QMenu(self.robotRestartPushButton)        
        self.robotRestartWithHomingAction = Qt.QAction("With homing", self.robotRestartMenu)
        self.robotRestartMenu.addAction(self.robotRestartWithHomingAction)
        self.robotRestartWithoutHomingAction = Qt.QAction("Without homing", self.robotRestartMenu)
        self.robotRestartMenu.addAction(self.robotRestartWithoutHomingAction)
        Qt.QObject.connect(self.robotRestartWithHomingAction, Qt.SIGNAL("triggered(bool)"), self.robotRestartWithHomingActionTriggered)
        Qt.QObject.connect(self.robotRestartWithoutHomingAction, Qt.SIGNAL("triggered(bool)"), self.robotRestartWithoutHomingActionTriggered)
        self.robotRestartPushButton.setMenu(self.robotRestartMenu)        
        self.robotHBoxLayout4.addWidget(self.robotRestartPushButton)
        self.robotAbortPushButton = Qt.QPushButton("Abort", self.brick_widget)       
        Qt.QObject.connect(self.robotAbortPushButton, Qt.SIGNAL("clicked()"), self.robotAbortPushButtonClicked)
        self.robotHBoxLayout4.addWidget(self.robotAbortPushButton)
        self.robotCleanPushButton = Qt.QPushButton("Clean", self.brick_widget)        
        Qt.QObject.connect(self.robotCleanPushButton, Qt.SIGNAL("clicked()"), self.robotCleanPushButtonClicked)
        self.robotHBoxLayout4.addWidget(self.robotCleanPushButton)
        self.robotFillPushButton = Qt.QPushButton("Fill", self.brick_widget)       
        Qt.QObject.connect(self.robotFillPushButton, Qt.SIGNAL("clicked()"), self.robotFillPushButtonClicked)
        self.robotHBoxLayout4.addWidget(self.robotFillPushButton)        
        self.robotDryPushButton = Qt.QPushButton("Dry", self.brick_widget)       
        Qt.QObject.connect(self.robotDryPushButton, Qt.SIGNAL("clicked()"), self.robotDryPushButtonClicked)
        self.robotHBoxLayout4.addWidget(self.robotDryPushButton)
        self.robotFixLiquidPositionPushButton = Qt.QPushButton("Fix liquid position", self.brick_widget)       
        Qt.QObject.connect(self.robotFixLiquidPositionPushButton, Qt.SIGNAL("clicked()"), self.robotFixLiquidPositionPushButtonClicked)
        self.robotHBoxLayout4.addWidget(self.robotFixLiquidPositionPushButton)                        
        self.robotSnapshotPushButton = Qt.QPushButton("Snapshot", self.brick_widget)        
        Qt.QObject.connect(self.robotSnapshotPushButton, Qt.SIGNAL("clicked()"), self.robotSnapshotPushButtonClicked)
        self.robotHBoxLayout4.addWidget(self.robotSnapshotPushButton)
        self.robotLayout.addLayout(self.robotHBoxLayout4)
        
        self.__sampleChangerDisplayFlag = False
        self.__sampleChangerDisplayMessage = ""        

	self.__updateTimer = QtCore.QTimer(self.brick_widget)

	QtCore.QObject.connect(self.__updateTimer, QtCore.SIGNAL('timeout()'), self.updateSampleChanger) 

    def updateSampleChanger(self):
        self._sampleChangerFrame = self._sampleChanger.getImageJPG()
        self.refreshSampleChangerFrame()

    def robotStorageTemperaturePushButtonClicked(self):
        def cancelPushButtonClicked():
            dialog.reject()

        def okPushButtonClicked():
            dialog.accept()
                        
        dialog = Qt.QDialog(self.brick_widget)
        dialog.setWindowTitle("Storage temperature")
        dialog.setModal(True)
        
        vBoxLayout = Qt.QVBoxLayout()
        dialog.setLayout(vBoxLayout)
        
        vBoxLayout.addWidget(Qt.QLabel("Please, insert new storage temperature:"))        
        temperatureDoubleSpinBox = Qt.QDoubleSpinBox(dialog)
        temperatureDoubleSpinBox.setSuffix(" C")
        temperatureDoubleSpinBox.setDecimals(2)        
        temperatureDoubleSpinBox.setRange(4, 40)        
        try:
            temperatureDoubleSpinBox.setValue(float(self.robotStorageTemperatureLineEdit.text().split(" ")[0]))
        except:
            temperatureDoubleSpinBox.setValue(20)        
        vBoxLayout.addWidget(temperatureDoubleSpinBox)
                
        buttonHBoxLayout = Qt.QHBoxLayout(dialog)
        cancelPushButton = Qt.QPushButton("Cancel", dialog)
        Qt.QObject.connect(cancelPushButton, Qt.SIGNAL("clicked()"), cancelPushButtonClicked)
        buttonHBoxLayout.addWidget(cancelPushButton)        
        okPushButton = Qt.QPushButton("Ok", dialog)
        Qt.QObject.connect(okPushButton, Qt.SIGNAL("clicked()"), okPushButtonClicked)
        buttonHBoxLayout.addWidget(okPushButton)
        vBoxLayout.addLayout(buttonHBoxLayout)

        if dialog.exec_():
            logging.getLogger().info("Setting storage temperature to '" + str(temperatureDoubleSpinBox.value()) + "'...")
            self.__sampleChangerDisplayFlag = True
            self.__sampleChangerDisplayMessage = "Error when trying to set storage temperature!"
            self._sampleChanger.setStorageTemperature(temperatureDoubleSpinBox.value())
        
    
    def robotSEUTemperaturePushButtonClicked(self):
        def cancelPushButtonClicked():
            dialog.reject()

        def okPushButtonClicked():
            dialog.accept()
                        
        dialog = Qt.QDialog(self.brick_widget)
        dialog.setWindowTitle("SEU temperature")
        dialog.setModal(True)
        
        vBoxLayout = Qt.QVBoxLayout()
        dialog.setLayout(vBoxLayout)
        
        vBoxLayout.addWidget(Qt.QLabel("Please, insert new SEU temperature:"))        
        temperatureDoubleSpinBox = Qt.QDoubleSpinBox(dialog)
        temperatureDoubleSpinBox.setSuffix(" C")
        temperatureDoubleSpinBox.setDecimals(2)        
        temperatureDoubleSpinBox.setRange(4, 60)
        try:
            temperatureDoubleSpinBox.setValue(float(self.robotSEUTemperatureLineEdit.text().split(" ")[0]))
        except:
            temperatureDoubleSpinBox.setValue(20)        
        vBoxLayout.addWidget(temperatureDoubleSpinBox)
        
        buttonHBoxLayout = Qt.QHBoxLayout(dialog)
        cancelPushButton = Qt.QPushButton("Cancel", dialog)
        Qt.QObject.connect(cancelPushButton, Qt.SIGNAL("clicked()"), cancelPushButtonClicked)
        buttonHBoxLayout.addWidget(cancelPushButton)        
        okPushButton = Qt.QPushButton("Ok", dialog)
        Qt.QObject.connect(okPushButton, Qt.SIGNAL("clicked()"), okPushButtonClicked)
        buttonHBoxLayout.addWidget(okPushButton)
        vBoxLayout.addLayout(buttonHBoxLayout)

        if dialog.exec_():
            logging.getLogger().info("Setting SEU temperature to '" + str(temperatureDoubleSpinBox.value()) + "'...")
            self.__sampleChangerDisplayFlag = True
            self.__sampleChangerDisplayMessage = "Error when trying to set SEU temperature!"
            self._sampleChanger.setSEUTemperature(temperatureDoubleSpinBox.value())
    
    def robotFillPushButtonClicked(self):
        # FUCK COPY PASTE CODE
        geometry = [self.getObject('samplechanger').getPlateInfo(i) for i in range(1, 4)]
        dialog = WellPickerDialog(geometry, title='Fill', display_volume=True, parent=self.brick_widget)
        ret = dialog.exec_()
        if ret:
            selected_well = dialog.get_selected_well()
            logging.info('filling from [plate, row, column] = %s', selected_well)
            self.getObject('samplechanger').fill(*selected_well)
            
    def robotDryPushButtonClicked(self):
        dryTime, buttonOk = Qt.QInputDialog.getInteger(self.brick_widget, "Dry", "\nPlease, insert time of drying (seconds):", 15, 1, 60, 2)
        if buttonOk:
            logging.getLogger().info("Drying robot...")
            self.__sampleChangerDisplayFlag = True
            self.__sampleChangerDisplayMessage = "Error when trying to dry robot!"
            self._sampleChanger.dry(dryTime)        

                
    def robotFixLiquidPositionPushButtonClicked(self):
        logging.getLogger().info("Fixing liquid position...")
        self.__sampleChangerDisplayFlag = True
        self.__sampleChangerDisplayMessage = "Error when trying to fix liquid position!"
        self._sampleChanger.setLiquidPositionFixed(True)


    def robotMoveBackwardPushButtonPressed(self):
        logging.getLogger().info("Moving syringe backward...")        
        self.__robotMoveState = 1
        self.__sampleChangerDisplayFlag = True
        self.__sampleChangerDisplayMessage = "Error when trying to move syringe backward!"
        self._sampleChanger.moveSyringeBackward(5)


    def robotMoveBackwardPushButtonReleased(self):
        self.__robotMoveState = 0
        self.robotStopPushButtonClicked()

        
    def robotStopPushButtonClicked(self):
        logging.getLogger().info("Stopping syringe...")
        self.__sampleChangerDisplayFlag = True
        self.__sampleChangerDisplayMessage = "Error when trying to stop syringe!"
        self._sampleChanger.stopSyringe()

    
    def robotMovePushButtonClicked(self):
        logging.getLogger().info("Moving syringe forward...")
        self.__sampleChangerDisplayFlag = True
        self.__sampleChangerDisplayMessage = "Error when trying to move syringe forward!"
        self._sampleChanger.moveSyringeForward(5)        
        

    def robotMoveForwardPushButtonPressed(self):
        self.__robotMoveState = 2
        self.robotMovePushButtonClicked()



    def robotMoveForwardPushButtonReleased(self):
        self.__robotMoveState = 0
        self.robotStopPushButtonClicked()


    def robotFlowPushButtonClicked(self):
                            
        def cancelPushButtonClicked():
            dialog.reject()

        def okPushButtonClicked():
            dialog.accept()
                
        dialog = Qt.QDialog(self.brick_widget)
        dialog.setWindowTitle("Flow")
        dialog.setModal(True)
        
        vBoxLayout = Qt.QVBoxLayout()
        dialog.setLayout(vBoxLayout)
        
        timeHBoxLayout = Qt.QHBoxLayout(dialog)
        timeHBoxLayout.addWidget(Qt.QLabel("Time", dialog))
        timeSpinBox = Qt.QSpinBox(dialog)
        timeSpinBox.setSuffix(" s")
        timeSpinBox.setRange(1, 1000)
        timeSpinBox.setValue(10)
        timeHBoxLayout.addWidget(timeSpinBox)
        vBoxLayout.addLayout(timeHBoxLayout)        
        
        buttonHBoxLayout = Qt.QHBoxLayout(dialog)
        cancelPushButton = Qt.QPushButton("Cancel", dialog)
        Qt.QObject.connect(cancelPushButton, Qt.SIGNAL("clicked()"), cancelPushButtonClicked)
        buttonHBoxLayout.addWidget(cancelPushButton)        
        okPushButton = Qt.QPushButton("Ok", dialog)
        Qt.QObject.connect(okPushButton, Qt.SIGNAL("clicked()"), okPushButtonClicked)
        buttonHBoxLayout.addWidget(okPushButton)
        vBoxLayout.addLayout(buttonHBoxLayout)

        if dialog.exec_():
            logging.getLogger().info("Flowing '" + str(timeSpinBox.value()) + "' second(s)...")
            self.__sampleChangerDisplayFlag = True
            self.__sampleChangerDisplayMessage = "Error when trying to flow!"
            self._sampleChanger.flowAll(timeSpinBox.value())
                             
                
    def robotRecuperatePushButtonClicked(self):
        geometry = [self.getObject('samplechanger').getPlateInfo(i) for i in range(1, 4)]
        logging.debug('geometry: %s', geometry)
        dialog = WellPickerDialog(geometry, title='Recuperate', parent=self.brick_widget)
        ret = dialog.exec_()
        if ret:
            selected_well = dialog.get_selected_well()
            logging.info('recuperating from [plate, row, column] = %s', selected_well)
            self.getObject('samplechanger').recuperate(*selected_well)


    def robotRestartWithHomingActionTriggered(self):
        logging.getLogger().info("Restarting (with homing) the robot...")
        self.__sampleChangerDisplayFlag = True
        self.__sampleChangerDisplayMessage = "Error when trying to restart (with homing) the robot!"
        self._sampleChanger.restart(True)



    def robotRestartWithoutHomingActionTriggered(self):
        logging.getLogger().info("Restarting (without homing) the robot...")
        self.__sampleChangerDisplayFlag = True
        self.__sampleChangerDisplayMessage = "Error when trying to restart (without homing) the robot!"
        self._sampleChanger.restart(False)

    
    
    def robotAbortPushButtonClicked(self):
        logging.getLogger().info("Aborting the robot...")
        self.__sampleChangerDisplayFlag = False
        self._sampleChanger.abort()



    def robotCleanPushButtonClicked(self):
        logging.getLogger().info("Cleaning the robot...")
        self.__sampleChangerDisplayFlag = True
        self.__sampleChangerDisplayMessage = "Error when trying to clean the robot!"
        self._sampleChanger.clean()                



    def robotSnapshotPushButtonClicked(self):
        filterList = ["Portable Network Graphics (*.png)", "Windows Bitmap (*.bmp)", "Joint Photographics Experts Group (*.jpg)"]
        qFileDialog = QtGui.QFileDialog(self.brick_widget, "Save image", ".")
        qFileDialog.setAcceptMode(QtGui.QFileDialog.AcceptSave)
        qFileDialog.setFilters(filterList)
        if qFileDialog.exec_():
            if qFileDialog.selectedNameFilter() == filterList[0]:                
                format = "PNG"
            elif qFileDialog.selectedNameFilter() == filterList[1]:
                format = "BMP"
            else:
                format = "JPG"                
            fileName = str(qFileDialog.selectedFiles()[0])
            if not fileName.upper().endswith("." + format):
                fileName += "." + format 
            if QtGui.QPixmap.grabWidget(self.robotSampleChangerFrameLabel).save(fileName, format):
                Qt.QMessageBox.information(self.brick_widget, "Info", "Image was successfully saved in file '" + fileName + "'!")
            else:
                Qt.QMessageBox.critical(self.brick_widget, "Error", "Error when trying to save image to file '" + fileName + "'!")


    def state_changed(self, state, status):
        self.robotSampleChangerStateLineEdit.setText(state)
        self.robotSampleChangerStatusLineEdit.setText(status)
        
        self.robotStorageTemperaturePushButton.setEnabled(state == "STANDBY")
        self.robotSEUTemperaturePushButton.setEnabled(state == "STANDBY")
        self.robotFillPushButton.setEnabled(state == "STANDBY")
        self.robotDryPushButton.setEnabled(state == "STANDBY" and status == "Cleaned")
        self.robotMoveBackwardPushButton.setEnabled(state == "STANDBY" or self.__robotMoveState == 1)
        self.robotStopPushButton.setEnabled(state == "MOVING")
        #self.robotMovePushButton.setEnabled(state == "STANDBY")
        self.robotMoveForwardPushButton.setEnabled(state == "STANDBY" or self.__robotMoveState == 2)
        self.robotFlowPushButton.setEnabled(state == "STANDBY" and status == "Loaded")
        self.robotRecuperatePushButton.setEnabled(state == "STANDBY" and status == "Loaded")
        self.robotRestartPushButton.setEnabled(state not in ("MOVING", "RUNNING", "INIT", "Not connected"))
        self.robotAbortPushButton.setEnabled(state in ("ALARM", "STANDBY", "MOVING", "RUNNING"))
        self.robotCleanPushButton.setEnabled(state == "STANDBY")
        
        currentLiquidPositionList = self._sampleChanger.getCurrentLiquidPosition()
        self.robotFixLiquidPositionPushButton.setEnabled(state == "STANDBY" and currentLiquidPositionList is not None and len(currentLiquidPositionList) > 0)
        
        if state == "STANDBY":
            if self.__sampleChangerDisplayFlag:
                if self.__sampleChangerDisplayMessage != "":
                    message = self.__sampleChangerDisplayMessage
                    self.__sampleChangerDisplayMessage = ""                       
                    if self._sampleChanger.getCommandException() is not None and self._sampleChanger.getCommandException() != "":
                        Qt.QMessageBox.critical(self.brick_widget, "Error", message)
                self.__sampleChangerDisplayFlag = False                            
        else:
            self.__sampleChangerDisplayFlag = True
            
    def storage_temperature_changed(self, temperature):
        #logging.debug('storage temp: %r', temperature)
        self.robotStorageTemperatureLineEdit.setText("%02.2f C" % float(temperature))
        
    def seu_temperature_changed(self, temperature):
        #logging.debug('seu temp: %r', temperature)
        self.robotSEUTemperatureLineEdit.setText("%02.2f C" % float(temperature))


    def refreshSampleChangerFrame(self):        
        self.robotSampleChangerFramePixmap = QtGui.QPixmap()
        self.robotSampleChangerFramePixmap.loadFromData(self._sampleChangerFrame, "JPG")
        self.robotSampleChangerFramePainter.begin(self.robotSampleChangerFramePixmap)
	try:
	    self.robotSampleChangerFramePainter.setPen(QtCore.Qt.green)
	    self.robotSampleChangerFramePainter.drawText(5, 15, "%d/%02d/%02d" % (time.localtime()[0], time.localtime()[1], time.localtime()[2]))
	    self.robotSampleChangerFramePainter.drawText(5, 30, "%02d:%02d:%02d" % (time.localtime()[3], time.localtime()[4], time.localtime()[5]))
	    currentLiquidPositionList = self._sampleChanger.getCurrentLiquidPosition()
	    if currentLiquidPositionList is not None:
		for currentLiquidPosition in currentLiquidPositionList:
		    self.robotSampleChangerFramePainter.drawLine(currentLiquidPosition, 0, currentLiquidPosition, self.robotSampleChangerFrameLabel.height())                                
				
		if self._isDrawing:
		    self.robotSampleChangerFramePainter.setPen(QtCore.Qt.red)
		    self.robotSampleChangerFramePainter.drawRect(self._beamLocation[0], self._beamLocation[1], self._beamLocation[2] - self._beamLocation[0], self._beamLocation[3] - self._beamLocation[1])
		else:
                    beamLocation = self._sampleChanger.getBeamLocation()
                    if beamLocation is not None:
                        # values are now separated by the UNIT SEPARATOR ascii character
                        # Many thanks to the complete moron who thought that was a good idea, and who didn't tell us it changed
                        # -- TB
                        beamLocationList = beamLocation.split(chr(ascii.US))
                        self._beamLocation = [int(beamLocationList[1]), int(beamLocationList[2]), int(beamLocationList[3]), int(beamLocationList[4])]
                        self.robotSampleChangerFramePainter.setPen(QtCore.Qt.red)
                        self.robotSampleChangerFramePainter.drawRect(self._beamLocation[0], self._beamLocation[1], self._beamLocation[2] - self._beamLocation[0], self._beamLocation[3] - self._beamLocation[1])                    
	finally:
		self.robotSampleChangerFramePainter.end()
        self.robotSampleChangerFrameLabel.setPixmap(self.robotSampleChangerFramePixmap)

class WellPickerWidget(QtGui.QWidget):
    # geometry is a list of 3 lists (one per plate)
    # each sublist should contain the num. of rows, colums and deep well columns
    def __init__(self, geometry, display_volume=False, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self._geometry = geometry
        self._display_volume = display_volume
        
        #Build the GUI according to geometry
        self.setLayout(QtGui.QGridLayout(self))
        # add the 3 labels
        self.layout().addWidget(QtGui.QLabel('Plate', self), 0, 0)
        self.layout().addWidget(QtGui.QLabel('Row', self), 1, 0)
        self.layout().addWidget(QtGui.QLabel('Column', self), 2, 0)

        # Add the 3 combo boxes
        self.plate_combo = QtGui.QComboBox(self)
        self.row_combo = QtGui.QComboBox(self)
        self.column_combo = QtGui.QComboBox(self)

    
        self.layout().addWidget(self.plate_combo, 0, 1)
        self.layout().addWidget(self.row_combo, 1, 1)
        self.layout().addWidget(self.column_combo, 2, 1)

        # the optional volume spinbox
        if self._display_volume:
           self.layout().addWidget(QtGui.QLabel('Volume', self), 3, 0)

           self.volume_spinbox = Qt.QSpinBox(self)
           self.volume_spinbox.setSuffix(" u/l")
           self.volume_spinbox.setRange(5, 150)
           self.volume_spinbox.setValue(10)
           self.layout().addWidget(self.volume_spinbox, 3, 1)

        self.plate_combo.addItems(['1', '2', '3'])
        # other 2 combos filled  by callbacks

        QtCore.QObject.connect(self.plate_combo, QtCore.SIGNAL("currentIndexChanged(const QString &)"), self.plate_changed)
        #self.plate_combo.currentIndexChanged.connect(self.plate_changed)

        #force initialization of rows/cols with the first (default) plate
        self.plate_changed('1')
        
    @QtCore.pyqtSlot(str)
    def plate_changed(self, selected_plate):
        # fill the row and colum combos with acceptable values
        # select the first one by default

        # Yeah, sucks
        selected_plate = int(selected_plate) - 1

        # XXX see with the beamline scientist since visitors tend to
        # click OK without thinking and trash samples. We may want to
        # autoselect a buffer instead to protect them from their own
        # stupidity
        self.row_combo.clear()
        self.column_combo.clear()

        # in the geometry, most of the numerical stuff are floats
        num_rows = int(self._geometry[selected_plate][0])
        num_cols = int(self._geometry[selected_plate][1])
        self.row_combo.addItems(['%d' % (x+1) for x in range(0, num_rows)])
        self.column_combo.addItems(['%d' % (x+1) for x in range(0, num_cols)])

    def get_selected_well(self):
        #returns a 3 elem list: [plate, column, row]
        selected_well = [int(self.plate_combo.currentText()),
                         int(self.row_combo.currentText()),
                         int(self.column_combo.currentText())]
        if self._display_volume:
            selected_well.append(int(self.volume_spinbox.value()))
        return selected_well

class WellPickerDialog(QtGui.QDialog):
    # same as the widget but encapsulated in a dialog
    def __init__(self, geometry, title='Choose a buffer', display_volume=False, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setLayout(QtGui.QVBoxLayout(self))
        self.setWindowTitle(title)
        
        self.well_picker = WellPickerWidget(geometry, display_volume=display_volume, parent=self)
        
        self.button_layout = QtGui.QHBoxLayout(self)

        self.ok_button = QtGui.QPushButton('Ok', self)
        self.cancel_button = QtGui.QPushButton('Cancel', self)

        self.ok_button.clicked.connect(self.ok_clicked)
        self.cancel_button.clicked.connect(self.cancel_clicked)
        
        self.button_layout.addWidget(self.ok_button)
        self.button_layout.addWidget(self.cancel_button)
        
        self.layout().addWidget(self.well_picker)
        self.layout().addLayout(self.button_layout)

    def ok_clicked(self):
        self.accept()
    def cancel_clicked(self):
        self.reject()

    def get_selected_well(self):
        # proxy to get the value after ok has been clicked
        return self.well_picker.get_selected_well()
        

class RobotSampleChangerFrameLabel(Qt.QLabel):

    def __init__(self, pParent, pBrickWidget):
        self.__parent = pParent
        self.__brickWidget = pBrickWidget
        Qt.QLabel.__init__(self, pBrickWidget)
        Qt.QObject.connect(self.__brickWidget, Qt.SIGNAL("refreshSampleChangerFrame()"), self.__parent.refreshSampleChangerFrame)
        self.setMouseTracking(True)
        self.__parent._isDrawing = False
        self.__isDefining = False
        self.__isMovingAll = False
        
        self.__isMovingHorizontalUp = False
        self.__isHorizontalUp = False
        self.__isMovingHorizontalDown = False
        self.__isHorizontalDown = False
        
        self.__isMovingVerticalLeft = False
        self.__isVerticalLeft = False
        self.__isMovingVerticalRight = False
        self.__isVerticalRight = False
        
        self.__moveDiagonalUpLeft = False
        self.__isDiagonalUpLeft = False
        self.__moveDiagonalDownLeft = False
        self.__isDiagonalDownLeft = False
        
        self.__moveDiagonalUpRight = False
        self.__isDiagonalUpRight = False
        self.__moveDiagonalDownRight = False
        self.__isDiagonalDownRight= False
                
        self.__isInside = False        
        self.__moveLocation = []
        
                
    
    def mouseDoubleClickEvent(self, pEvent):
        if pEvent.button() == 1:
            self.setCursor(Qt.Qt.CrossCursor)
            self.__parent._beamLocation = [pEvent.x(), pEvent.y(), pEvent.x(), pEvent.y()]                                        
            self.__parent._isDrawing = True
            self.__isDefining = True
            self.__isMovingAll = False
            
            self.__isMovingHorizontalUp = False
            self.__isHorizontalUp = False
            self.__isMovingHorizontalDown = False
            self.__isHorizontalDown = False
            
            self.__isMovingVerticalLeft = False
            self.__isVerticalLeft = False
            self.__isMovingVerticalRight = False
            self.__isVerticalRight = False
            
            self.__moveDiagonalUpLeft = False
            self.__isDiagonalUpLeft = False
            self.__moveDiagonalDownLeft = False
            self.__isDiagonalDownLeft = False
            
            self.__moveDiagonalUpRight = False
            self.__isDiagonalUpRight = False
            self.__moveDiagonalDownRight = False
            self.__isDiagonalDownRight= False
                    
            self.__isInside = False        
            self.__moveLocation = []

              
        
    def mouseMoveEvent(self, pEvent):
        if self.__isDefining:
            self.__parent._beamLocation = [self.__parent._beamLocation[0], self.__parent._beamLocation[1], pEvent.x(), pEvent.y()]  
            Qt.QObject.emit(self.__brickWidget, Qt.SIGNAL("refreshSampleChangerFrame()"))
            
        elif self.__isMovingAll:
            self.__parent._beamLocation = [pEvent.x() - self.__moveLocation[0], pEvent.y() - self.__moveLocation[1], pEvent.x() + self.__moveLocation[2], pEvent.y() + self.__moveLocation[3]]
            Qt.QObject.emit(self.__brickWidget, Qt.SIGNAL("refreshSampleChangerFrame()"))            
            
        elif self.__isMovingHorizontalUp:
            self.__parent._beamLocation = [self.__parent._beamLocation[0], pEvent.y(), self.__parent._beamLocation[2], self.__parent._beamLocation[3]]            
            Qt.QObject.emit(self.__brickWidget, Qt.SIGNAL("refreshSampleChangerFrame()"))

        elif self.__isMovingHorizontalDown:
            self.__parent._beamLocation = [self.__parent._beamLocation[0], self.__parent._beamLocation[1], self.__parent._beamLocation[2], pEvent.y()]            
            Qt.QObject.emit(self.__brickWidget, Qt.SIGNAL("refreshSampleChangerFrame()"))

        elif self.__isMovingVerticalLeft:
            self.__parent._beamLocation = [pEvent.x(), self.__parent._beamLocation[1], self.__parent._beamLocation[2], self.__parent._beamLocation[3]]
            Qt.QObject.emit(self.__brickWidget, Qt.SIGNAL("refreshSampleChangerFrame()"))

        elif self.__isMovingVerticalRight:
            self.__parent._beamLocation = [self.__parent._beamLocation[0], self.__parent._beamLocation[1], pEvent.x(), self.__parent._beamLocation[3]]
            Qt.QObject.emit(self.__brickWidget, Qt.SIGNAL("refreshSampleChangerFrame()"))
                            
        elif self.__parent._beamLocation is not None:
            if self.__parent._beamLocation[0] > self.__parent._beamLocation[2]:
                drawBeginX  = self.__parent._beamLocation[2]
                drawEndX  = self.__parent._beamLocation[0]
            else:
                drawBeginX  = self.__parent._beamLocation[0]
                drawEndX  = self.__parent._beamLocation[2]
            if self.__parent._beamLocation[1] > self.__parent._beamLocation[3]:
                drawBeginY  = self.__parent._beamLocation[3]
                drawEndY  = self.__parent._beamLocation[1]
            else:
                drawBeginY  = self.__parent._beamLocation[1]
                drawEndY  = self.__parent._beamLocation[3]
            
            self.__isInside = (pEvent.x() > drawBeginX and pEvent.x() < drawEndX and pEvent.y() > drawBeginY and pEvent.y() < drawEndY)
            self.__isHorizontalUp = (pEvent.y() == drawBeginY)
            self.__isHorizontalDown = (pEvent.y() == drawEndY)
            self.__isVerticalLeft = (pEvent.x() == drawBeginX)
            self.__isVerticalRight = (pEvent.x() == drawEndX)
            self.__isDiagonalUpLeft = (self.__isHorizontalUp and self.__isVerticalLeft)
            self.__isDiagonalDownLeft = (self.__isHorizontalDown and self.__isVerticalLeft)
            self.__isDiagonalUpRight = (self.__isHorizontalUp and self.__isVerticalRight)
            self.__isDiagonalDownRight = (self.__isHorizontalDown and self.__isVerticalRight)
             
            if self.__isInside:
                self.setCursor(Qt.Qt.SizeAllCursor)
            elif self.__isDiagonalUpLeft or self.__isDiagonalDownRight:
                self.setCursor(Qt.Qt.SizeFDiagCursor)
            elif self.__isDiagonalUpRight or self.__isDiagonalDownLeft:
                self.setCursor(Qt.Qt.SizeBDiagCursor)
            elif self.__isHorizontalUp or self.__isHorizontalDown:
                self.setCursor(Qt.Qt.SizeVerCursor)
            elif self.__isVerticalLeft or self.__isVerticalRight:
                self.setCursor(Qt.Qt.SizeHorCursor)
            else:  
                #self.setCursor(Qt.Qt.ArrowCursor)
                self.unsetCursor()
       
                
                
    def mousePressEvent(self, pEvent):
        if pEvent.button() == 1:
            if self.__isInside:
                self.__moveLocation = [pEvent.x() - self.__parent._beamLocation[0], pEvent.y() - self.__parent._beamLocation[1], self.__parent._beamLocation[2] - pEvent.x(), self.__parent._beamLocation[3] - pEvent.y()]
                self.__isMovingAll = True            
                self.__parent._isDrawing = True
            elif self.__isDiagonalUpLeft:
                self.__isMovingDiagonalUpLeft = True            
                self.__parent._isDrawing = True
            elif self.__isDiagonalDownRight:
                self.__isMovingDiagonalDownRight = True            
                self.__parent._isDrawing = True                
            elif self.__isDiagonalUpRight:
                self.__isMovingDiagonalUpRight = True
                self.__parent._isDrawing = True
            elif self.__isDiagonalDownLeft:
                self.__isMovingDiagonalDownLeft = True
                self.__parent._isDrawing = True                
            elif self.__isHorizontalUp:
                self.__isMovingHorizontalUp = True            
                self.__parent._isDrawing = True
            elif self.__isHorizontalDown:
                self.__isMovingHorizontalDown = True            
                self.__parent._isDrawing = True
            elif self.__isVerticalLeft:
                self.__isMovingVerticalLeft = True            
                self.__parent._isDrawing = True
            elif self.__isVerticalRight:
                self.__isMovingVerticalRight = True            
                self.__parent._isDrawing = True                                                
            else:
                self.unsetCursor()
        
                        
            
    def mouseReleaseEvent(self, pEvent):
        if self.__isDefining or self.__isMovingAll or self.__isMovingHorizontalUp or self.__isMovingHorizontalDown or self.__isMovingVerticalLeft or self.__isMovingVerticalRight:
            if self.__parent._beamLocation[0] != self.__parent._beamLocation[2] or self.__parent._beamLocation[1] != self.__parent._beamLocation[3]:
                self.setCursor(Qt.Qt.ArrowCursor)
                if Qt.QMessageBox.question(self, "Info", "Do you accept this position as where the beam is located?", Qt.QMessageBox.Yes, Qt.QMessageBox.No, Qt.QMessageBox.NoButton) == Qt.QMessageBox.Yes:
                    if self.__parent._beamLocation[0] > self.__parent._beamLocation[2]:
                        x = self.__parent._beamLocation[0]
                        self.__parent._beamLocation[0] = self.__parent._beamLocation[2]
                        self.__parent._beamLocation[2] = x 
                    
                    if self.__parent._beamLocation[1] > self.__parent._beamLocation[3]:
                        y = self.__parent._beamLocation[1] 
                        self.__parent._beamLocation[1] = self.__parent._beamLocation[3]
                        self.__parent._beamLocation[3] = y 
                    self.__parent._sampleChanger.setBeamLocation(self.__parent._beamLocation[0], self.__parent._beamLocation[1], self.__parent._beamLocation[2], self.__parent._beamLocation[3])
                self.__parent._isDrawing = False
                self.__isDefining = False
            self.__isMovingAll = False
            self.__isMovingHorizontalUp = False
            self.__isMovingHorizontalDown = False
            self.__isMovingVerticalLeft = False
            self.__isMovingVerticalRight = False
