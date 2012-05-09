import os
import logging
from Framework4.GUI import Core
from Framework4.GUI.Core import Property, Connection, Signal, Slot
from PyQt4 import QtCore, QtGui, Qt


__category__ = "BsxCuBE"



class ReprocessBrick(Core.BaseBrick):


    properties = {}
    connections = {"reprocess": Connection("Reprocess object",
                                             [Signal("reprocessDirectoryChanged", "reprocessDirectoryChanged"),
                                              Signal("reprocessPrefixChanged", "reprocessPrefixChanged"),
                                              Signal("reprocessRunNumberChanged", "reprocessRunNumberChanged"),
                                              Signal("reprocessFrameFirstChanged", "reprocessFrameFirstChanged"),
                                              Signal("reprocessFrameLastChanged", "reprocessFrameLastChanged"),
                                              Signal("reprocessConcentrationChanged", "reprocessConcentrationChanged"),
                                              Signal("reprocessCommentsChanged", "reprocessCommentsChanged"),
                                              Signal("reprocessCodeChanged", "reprocessCodeChanged"),
                                              Signal("reprocessMaskFileChanged", "reprocessMaskFileChanged"),
                                              Signal("reprocessDetectorDistanceChanged", "reprocessDetectorDistanceChanged"),
                                              Signal("reprocessWaveLengthChanged", "reprocessWaveLengthChanged"),
                                              Signal("reprocessPixelSizeXChanged", "reprocessPixelSizeXChanged"),
                                              Signal("reprocessPixelSizeYChanged", "reprocessPixelSizeYChanged"),
                                              Signal("reprocessBeamCenterXChanged", "reprocessBeamCenterXChanged"),
                                              Signal("reprocessBeamCenterYChanged", "reprocessBeamCenterYChanged"),
                                              Signal("reprocessNormalisationChanged", "reprocessNormalisationChanged"),
                                              Signal("reprocessBeamStopDiodeChanged", "reprocessBeamStopDiodeChanged"),
                                              Signal("reprocessMachineCurrentChanged", "reprocessMachineCurrentChanged"),
                                              Signal("reprocessKeepOriginalChanged", "reprocessKeepOriginalChanged"),
                                              Signal("reprocessStatusChanged", "reprocessStatusChanged")],
                                            [Slot("reprocess")],
                                            "connectionStatusChanged")}



    signals = [Signal("displayResetChanged"),
               Signal("displayItemChanged")]
    slots = []

    def reprocessDirectoryChanged(self, pValue):
        self.directoryLineEdit.setText(pValue)


    def reprocessPrefixChanged(self, pValue):
        for i in range(0, self.prefixComboBox.count()):
            if pValue == self.prefixComboBox.itemText(i):
                self.prefixComboBox.setCurrentIndex(i)
                break
        self.populateRunNumberListWidget()
        self.populateFrameComboBox()
        self.__validParameters[1] = self.prefixComboBox.currentIndex() > 0


    def reprocessRunNumberChanged(self, pValue):
        pass


    def reprocessFrameFirstChanged(self, pValue):
        pass


    def reprocessFrameLastChanged(self, pValue):
        pass


    def reprocessConcentrationChanged(self, pValue):
        if pValue != "":
            self.concentrationDoubleSpinBox.setValue(float(pValue))


    def reprocessCommentsChanged(self, pValue):
        self.commentsLineEdit.setText(pValue)


    def reprocessCodeChanged(self, pValue):
        self.codeLineEdit.setText(pValue)


    def reprocessMaskFileChanged(self, pValue):
        self.maskLineEdit.setText(pValue)


    def reprocessDetectorDistanceChanged(self, pValue):
        if pValue != "":
            self.detectorDistanceDoubleSpinBox.setValue(float(pValue))


    def reprocessWaveLengthChanged(self, pValue):
        if pValue != "":
            self.waveLengthDoubleSpinBox.setValue(float(pValue))


    def reprocessPixelSizeXChanged(self, pValue):
        if pValue != "":
            self.pixelSizeXDoubleSpinBox.setValue(float(pValue))


    def reprocessPixelSizeYChanged(self, pValue):
        if pValue != "":
            self.pixelSizeYDoubleSpinBox.setValue(float(pValue))


    def reprocessBeamCenterXChanged(self, pValue):
            self.beamCenterXSpinBox.setValue(int(pValue))


    def reprocessBeamCenterYChanged(self, pValue):
        if pValue != "":
            self.beamCenterYSpinBox.setValue(int(pValue))


    def reprocessNormalisationChanged(self, pValue):
        if pValue != "":
            self.normalisationDoubleSpinBox.setValue(float(pValue))


    def reprocessBeamStopDiodeChanged(self, pValue):
        if pValue != "":
            self.beamStopDiodeDoubleSpinBox.setValue(float(pValue))


    def reprocessMachineCurrentChanged(self, pValue):
        if pValue != "":
            self.machineCurrentDoubleSpinBox.setValue(float(pValue))


    def reprocessKeepOriginalChanged(self, pValue):
        self.keepOriginalCheckBox.setChecked(pValue == "1")


    def reprocessStatusChanged(self, pValue):
        #TODO: Understand
        if self.__isReprocessing:
            messageList = pValue.split(",", 3)
            if messageList[0] == "0":   # reprocess done
                self.SPECBusyTimer.stop()
                self.__isReprocessing = False
                self.setButtonState(0)
                logging.getLogger().info(messageList[1])
                if self.notifyCheckBox.isChecked():
                    Qt.QMessageBox.information(self.brick_widget, "Info", "\n                       %s                                       \n" % messageList[1])
            elif messageList[0] == "1":     # reprocess info 
                self.SPECBusyTimer.start(25000)
                logging.getLogger().info(messageList[1])
            elif messageList[0] == "2":     # reprocess info with item to be displayed
                self.SPECBusyTimer.start(25000)
                logging.getLogger().info(messageList[1])
                self.emit("displayItemChanged", messageList[2])
            elif messageList[0] == "3":     # reprocess warning
                logging.getLogger().warning(messageList[1])
            elif messageList[0] == "4":     # reprocess error
                self.SPECBusyTimer.stop()
                self.__isReprocessing = False
                self.setButtonState(0)
                logging.getLogger().error(messageList[1])


    def connectionStatusChanged(self, pPeer):
        pass


    def __init__(self, *args, **kargs):
        Core.BaseBrick.__init__(self, *args, **kargs)


    def init(self):
        self.__expertMode = False
        self.__isReprocessing = False
        self.__validParameters = [False, False, False, False, False]

        self.brick_widget.setLayout(Qt.QVBoxLayout())

        self.hBoxLayout2 = Qt.QHBoxLayout()
        self.directoryLabel = Qt.QLabel("Directory", self.brick_widget)
        self.directoryLabel.setFixedWidth(130)
        self.hBoxLayout2.addWidget(self.directoryLabel)
        self.directoryLineEdit = Qt.QLineEdit(self.brick_widget)
        self.directoryLineEdit.setMaxLength(100)
        Qt.QObject.connect(self.directoryLineEdit, Qt.SIGNAL("textChanged(const QString &)"), self.directoryLineEditChanged)
        self.hBoxLayout2.addWidget(self.directoryLineEdit)
        self.directoryPushButton = Qt.QPushButton("...", self.brick_widget)
        self.directoryPushButton.setFixedWidth(25)
        Qt.QObject.connect(self.directoryPushButton, Qt.SIGNAL("clicked()"), self.directoryPushButtonClicked)
        self.hBoxLayout2.addWidget(self.directoryPushButton)
        self.brick_widget.layout().addLayout(self.hBoxLayout2)

        self.hBoxLayout3 = Qt.QHBoxLayout()
        self.directoryLabel = Qt.QLabel("Prefix", self.brick_widget)
        self.directoryLabel.setFixedWidth(130)
        self.hBoxLayout3.addWidget(self.directoryLabel)
        self.prefixComboBox = Qt.QComboBox(self.brick_widget)
        Qt.QObject.connect(self.prefixComboBox, Qt.SIGNAL("currentIndexChanged(int)"), self.prefixComboBoxChanged)
        self.hBoxLayout3.addWidget(self.prefixComboBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout3)

        self.hBoxLayout4 = Qt.QHBoxLayout()
        self.runNumberLabel = Qt.QLabel("Run #", self.brick_widget)
        self.runNumberLabel.setFixedWidth(130)
        self.hBoxLayout4.addWidget(self.runNumberLabel)
        self.runNumberListWidget = Qt.QListWidget(self.brick_widget)
        self.runNumberListWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        Qt.QObject.connect(self.runNumberListWidget, Qt.SIGNAL("itemSelectionChanged()"), self.runNumberListWidgetChanged)
        self.hBoxLayout4.addWidget(self.runNumberListWidget)
        self.brick_widget.layout().addLayout(self.hBoxLayout4)

        self.hBoxLayout5 = Qt.QHBoxLayout()
        self.frameLabel = Qt.QLabel("Frame (first, last)", self.brick_widget)
        self.frameLabel.setFixedWidth(130)
        self.hBoxLayout5.addWidget(self.frameLabel)
        self.frameFirstComboBox = Qt.QComboBox(self.brick_widget)
        Qt.QObject.connect(self.frameFirstComboBox, Qt.SIGNAL("currentIndexChanged(int)"), self.frameFirstComboBoxChanged)
        self.hBoxLayout5.addWidget(self.frameFirstComboBox)
        self.frameLastComboBox = Qt.QComboBox(self.brick_widget)
        Qt.QObject.connect(self.frameLastComboBox, Qt.SIGNAL("currentIndexChanged(int)"), self.frameLastComboBoxChanged)
        self.hBoxLayout5.addWidget(self.frameLastComboBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout5)

        self.hBoxLayout6 = Qt.QHBoxLayout()
        self.concentrationCheckBox = Qt.QCheckBox("Concentration", self.brick_widget)
        self.concentrationCheckBox.setFixedWidth(130)
        Qt.QObject.connect(self.concentrationCheckBox, Qt.SIGNAL("toggled(bool)"), self.concentrationCheckBoxToggled)
        self.hBoxLayout6.addWidget(self.concentrationCheckBox)
        self.concentrationDoubleSpinBox = Qt.QDoubleSpinBox(self.brick_widget)
        self.concentrationDoubleSpinBox.setSuffix(" mg/ml")
        self.concentrationDoubleSpinBox.setDecimals(2)
        self.concentrationDoubleSpinBox.setRange(0, 100)
        self.hBoxLayout6.addWidget(self.concentrationDoubleSpinBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout6)

        self.hBoxLayout7 = Qt.QHBoxLayout()
        self.commentsCheckBox = Qt.QCheckBox("Comments", self.brick_widget)
        self.commentsCheckBox.setFixedWidth(130)
        Qt.QObject.connect(self.commentsCheckBox, Qt.SIGNAL("toggled(bool)"), self.commentsCheckBoxToggled)
        self.hBoxLayout7.addWidget(self.commentsCheckBox)
        self.commentsLineEdit = Qt.QLineEdit(self.brick_widget)
        self.commentsLineEdit.setMaxLength(100)
        self.commentsLineEdit.setValidator(Qt.QRegExpValidator(Qt.QRegExp("[a-zA-Z0-9\\%/()=+*^:.\-_ ]*"), self.commentsLineEdit))
        self.hBoxLayout7.addWidget(self.commentsLineEdit)
        self.brick_widget.layout().addLayout(self.hBoxLayout7)

        self.hBoxLayout8 = Qt.QHBoxLayout()
        self.codeCheckBox = Qt.QCheckBox("Code", self.brick_widget)
        self.codeCheckBox.setFixedWidth(130)
        Qt.QObject.connect(self.codeCheckBox, Qt.SIGNAL("toggled(bool)"), self.codeCheckBoxToggled)
        self.hBoxLayout8.addWidget(self.codeCheckBox)
        self.codeLineEdit = Qt.QLineEdit(self.brick_widget)
        self.codeLineEdit.setMaxLength(30)
        self.codeLineEdit.setValidator(Qt.QRegExpValidator(Qt.QRegExp("^[a-zA-Z][a-zA-Z0-9_]*"), self.codeLineEdit))
        self.hBoxLayout8.addWidget(self.codeLineEdit)
        self.brick_widget.layout().addLayout(self.hBoxLayout8)

        self.hBoxLayout9 = Qt.QHBoxLayout()
        self.maskCheckBox = Qt.QCheckBox("Mask", self.brick_widget)
        self.maskCheckBox.setFixedWidth(130)
        Qt.QObject.connect(self.maskCheckBox, Qt.SIGNAL("toggled(bool)"), self.maskCheckBoxToggled)
        self.hBoxLayout9.addWidget(self.maskCheckBox)
        self.maskLineEdit = Qt.QLineEdit(self.brick_widget)
        self.maskLineEdit.setMaxLength(100)
        Qt.QObject.connect(self.maskLineEdit, Qt.SIGNAL("textChanged(const QString &)"), self.maskLineEditChanged)
        self.hBoxLayout9.addWidget(self.maskLineEdit)
        self.maskDirectoryPushButton = Qt.QPushButton("...", self.brick_widget)
        self.maskDirectoryPushButton.setFixedWidth(25)
        Qt.QObject.connect(self.maskDirectoryPushButton, Qt.SIGNAL("clicked()"), self.maskDirectoryPushButtonClicked)
        self.hBoxLayout9.addWidget(self.maskDirectoryPushButton)
        self.maskDisplayPushButton = Qt.QPushButton("Display", self.brick_widget)
        self.maskDisplayPushButton.setFixedWidth(55)
        Qt.QObject.connect(self.maskDisplayPushButton, Qt.SIGNAL("clicked()"), self.maskDisplayPushButtonClicked)
        self.hBoxLayout9.addWidget(self.maskDisplayPushButton)
        self.brick_widget.layout().addLayout(self.hBoxLayout9)

        self.hBoxLayout10 = Qt.QHBoxLayout()
        self.detectorDistanceCheckBox = Qt.QCheckBox("Detector distance", self.brick_widget)
        self.detectorDistanceCheckBox.setFixedWidth(130)
        Qt.QObject.connect(self.detectorDistanceCheckBox, Qt.SIGNAL("toggled(bool)"), self.detectorDistanceCheckBoxToggled)
        self.hBoxLayout10.addWidget(self.detectorDistanceCheckBox)
        self.detectorDistanceDoubleSpinBox = Qt.QDoubleSpinBox(self.brick_widget)
        self.detectorDistanceDoubleSpinBox.setSuffix(" m")
        self.detectorDistanceDoubleSpinBox.setDecimals(3)
        self.detectorDistanceDoubleSpinBox.setRange(0.1, 10)
        self.hBoxLayout10.addWidget(self.detectorDistanceDoubleSpinBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout10)

        self.hBoxLayout11 = Qt.QHBoxLayout()
        self.waveLengthCheckBox = Qt.QCheckBox("Wave length", self.brick_widget)
        self.waveLengthCheckBox.setFixedWidth(130)
        Qt.QObject.connect(self.waveLengthCheckBox, Qt.SIGNAL("toggled(bool)"), self.waveLengthCheckBoxToggled)
        self.hBoxLayout11.addWidget(self.waveLengthCheckBox)
        self.waveLengthDoubleSpinBox = Qt.QDoubleSpinBox(self.brick_widget)
        self.waveLengthDoubleSpinBox.setSuffix(" nm")
        self.waveLengthDoubleSpinBox.setDecimals(4)
        self.waveLengthDoubleSpinBox.setRange(0.01, 1)
        self.hBoxLayout11.addWidget(self.waveLengthDoubleSpinBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout11)

        self.hBoxLayout12 = Qt.QHBoxLayout()
        self.pixelSizeCheckBox = Qt.QCheckBox("Pixel size (x, y)", self.brick_widget)
        self.pixelSizeCheckBox.setFixedWidth(130)
        Qt.QObject.connect(self.pixelSizeCheckBox, Qt.SIGNAL("toggled(bool)"), self.pixelSizeCheckBoxToggled)
        self.hBoxLayout12.addWidget(self.pixelSizeCheckBox)
        self.pixelSizeXDoubleSpinBox = Qt.QDoubleSpinBox(self.brick_widget)
        self.pixelSizeXDoubleSpinBox.setSuffix(" um")
        self.pixelSizeXDoubleSpinBox.setDecimals(1)
        self.pixelSizeXDoubleSpinBox.setRange(10, 500)
        self.hBoxLayout12.addWidget(self.pixelSizeXDoubleSpinBox)
        self.pixelSizeYDoubleSpinBox = Qt.QDoubleSpinBox(self.brick_widget)
        self.pixelSizeYDoubleSpinBox.setSuffix(" um")
        self.pixelSizeYDoubleSpinBox.setDecimals(1)
        self.pixelSizeYDoubleSpinBox.setRange(10, 500)
        self.hBoxLayout12.addWidget(self.pixelSizeYDoubleSpinBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout12)

        self.hBoxLayout13 = Qt.QHBoxLayout()
        self.beamCenterCheckBox = Qt.QCheckBox("Beam center (x, y)", self.brick_widget)
        self.beamCenterCheckBox.setFixedWidth(130)
        Qt.QObject.connect(self.beamCenterCheckBox, Qt.SIGNAL("toggled(bool)"), self.beamCenterCheckBoxToggled)
        self.hBoxLayout13.addWidget(self.beamCenterCheckBox)
        self.beamCenterXSpinBox = Qt.QSpinBox(self.brick_widget)
        self.beamCenterXSpinBox.setSuffix(" px")
        self.beamCenterXSpinBox.setRange(1, 9999)
        self.hBoxLayout13.addWidget(self.beamCenterXSpinBox)
        self.beamCenterYSpinBox = Qt.QSpinBox(self.brick_widget)
        self.beamCenterYSpinBox.setSuffix(" px")
        self.beamCenterYSpinBox.setRange(1, 9999)
        self.hBoxLayout13.addWidget(self.beamCenterYSpinBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout13)

        self.hBoxLayout14 = Qt.QHBoxLayout()
        self.normalisationCheckBox = Qt.QCheckBox("Normalisation", self.brick_widget)
        self.normalisationCheckBox.setFixedWidth(130)
        Qt.QObject.connect(self.normalisationCheckBox, Qt.SIGNAL("toggled(bool)"), self.normalisationCheckBoxToggled)
        self.hBoxLayout14.addWidget(self.normalisationCheckBox)
        self.normalisationDoubleSpinBox = Qt.QDoubleSpinBox(self.brick_widget)
        self.normalisationDoubleSpinBox.setDecimals(7)
        self.normalisationDoubleSpinBox.setRange(0.0001, 10000)
        self.hBoxLayout14.addWidget(self.normalisationDoubleSpinBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout14)

        self.hBoxLayout15 = Qt.QHBoxLayout()
        self.beamStopDiodeCheckBox = Qt.QCheckBox("Beam stop diode", self.brick_widget)
        self.beamStopDiodeCheckBox.setFixedWidth(130)
        Qt.QObject.connect(self.beamStopDiodeCheckBox, Qt.SIGNAL("toggled(bool)"), self.beamStopDiodeCheckBoxToggled)
        self.hBoxLayout15.addWidget(self.beamStopDiodeCheckBox)
        self.beamStopDiodeDoubleSpinBox = Qt.QDoubleSpinBox(self.brick_widget)
        self.beamStopDiodeDoubleSpinBox.setDecimals(12)
        self.beamStopDiodeDoubleSpinBox.setRange(-1, 1)
        self.hBoxLayout15.addWidget(self.beamStopDiodeDoubleSpinBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout15)

        self.hBoxLayout16 = Qt.QHBoxLayout()
        self.machineCurrentCheckBox = Qt.QCheckBox("Machine current", self.brick_widget)
        self.machineCurrentCheckBox.setFixedWidth(130)
        Qt.QObject.connect(self.machineCurrentCheckBox, Qt.SIGNAL("toggled(bool)"), self.machineCurrentCheckBoxToggled)
        self.hBoxLayout16.addWidget(self.machineCurrentCheckBox)
        self.machineCurrentDoubleSpinBox = Qt.QDoubleSpinBox(self.brick_widget)
        self.machineCurrentDoubleSpinBox.setDecimals(2)
        self.machineCurrentDoubleSpinBox.setRange(0, 350)
        self.hBoxLayout16.addWidget(self.machineCurrentDoubleSpinBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout16)

        self.hBoxLayout17 = Qt.QHBoxLayout()
        self.keepOriginalCheckBox = Qt.QCheckBox("Keep original files", self.brick_widget)
        self.keepOriginalCheckBox.setChecked(True)
        self.hBoxLayout17.addWidget(self.keepOriginalCheckBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout17)

        self.hBoxLayout18 = Qt.QHBoxLayout()
        self.notifyCheckBox = Qt.QCheckBox("Notify when done", self.brick_widget)
        self.notifyCheckBox.setChecked(True)
        self.hBoxLayout18.addWidget(self.notifyCheckBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout18)

        self.vBoxLayout0 = Qt.QVBoxLayout()
        self.vBoxLayout0.addSpacing(15)
        self.brick_widget.layout().addLayout(self.vBoxLayout0)

        self.hBoxLayout18 = Qt.QHBoxLayout()
        self.reprocessPushButton = Qt.QPushButton("Reprocess", self.brick_widget)
        self.reprocessPushButton.setToolTip("Start reprocess with the specified parameters")
        self.hBoxLayout18.addWidget(self.reprocessPushButton)
        Qt.QObject.connect(self.reprocessPushButton, Qt.SIGNAL("clicked()"), self.reprocessPushButtonClicked)
        self.brick_widget.layout().addLayout(self.hBoxLayout18)

        self.hBoxLayout19 = Qt.QHBoxLayout()
        self.abortPushButton = Qt.QPushButton("Abort", self.brick_widget)
        self.abortPushButton.setToolTip("Abort ongoing data reprocessing")
        self.hBoxLayout19.addWidget(self.abortPushButton)
        Qt.QObject.connect(self.abortPushButton, Qt.SIGNAL("clicked()"), self.abortPushButtonClicked)
        self.brick_widget.layout().addLayout(self.hBoxLayout19)

        self.directoryLineEditChanged(None)
        self.concentrationCheckBoxToggled(False)
        self.commentsCheckBoxToggled(False)
        self.codeCheckBoxToggled(False)
        self.maskCheckBoxToggled(False)
        self.detectorDistanceCheckBoxToggled(False)
        self.waveLengthCheckBoxToggled(False)
        self.pixelSizeCheckBoxToggled(False)
        self.beamCenterCheckBoxToggled(False)
        self.normalisationCheckBoxToggled(False)
        self.beamStopDiodeCheckBoxToggled(False)
        self.machineCurrentCheckBoxToggled(False)

        self.SPECBusyTimer = Qt.QTimer(self.brick_widget)
        Qt.QObject.connect(self.SPECBusyTimer, Qt.SIGNAL("timeout()"), self.SPECBusyTimerTimeOut)

        self.setButtonState(0)



    def delete(self):
        pass



#TODO: replace
#    def detectorComboBoxChanged(self, pValue):
#        if not self.__isReprocessing:
#            self.populatePrefixComboBox()
#            self.populateRunNumberListWidget()
#            self.populateFrameComboBox()



#TODO: replace
#    def operationComboBoxChanged(self, pValue):
#        if not self.__isReprocessing:
#            self.concentrationCheckBox.setEnabled(pValue in (1, 3))
#            self.concentrationDoubleSpinBox.setEnabled(pValue in (1, 3) and self.concentrationCheckBox.isChecked())
#            self.commentsCheckBox.setEnabled(pValue in (1, 3))
#            self.commentsLineEdit.setEnabled(pValue in (1, 3) and self.commentsCheckBox.isChecked())
#            self.codeCheckBox.setEnabled(pValue in (1, 3))
#            self.codeLineEdit.setEnabled(pValue in (1, 3) and self.codeCheckBox.isChecked())
#            self.maskCheckBox.setEnabled(pValue in (1, 3))
#            self.maskLineEdit.setEnabled(pValue in (1, 3) and self.maskCheckBox.isChecked())
#            self.maskDirectoryPushButton.setEnabled(pValue in (1, 3) and self.maskCheckBox.isChecked())
#            self.maskDisplayPushButton.setEnabled(pValue in (1, 3) and self.maskCheckBox.isChecked())
#            self.detectorDistanceCheckBox.setEnabled(pValue in (1, 3))
#            self.detectorDistanceDoubleSpinBox.setEnabled(pValue in (1, 3) and self.detectorDistanceCheckBox.isChecked())
#            self.waveLengthCheckBox.setEnabled(pValue in (1, 3))
#            self.waveLengthDoubleSpinBox.setEnabled(pValue in (1, 3) and self.waveLengthCheckBox.isChecked())
#            self.pixelSizeCheckBox.setEnabled(pValue in (1, 3))
#            self.pixelSizeXDoubleSpinBox.setEnabled(pValue in (1, 3) and self.pixelSizeCheckBox.isChecked())
#            self.pixelSizeYDoubleSpinBox.setEnabled(pValue in (1, 3) and self.pixelSizeCheckBox.isChecked())
#            self.beamCenterCheckBox.setEnabled(pValue in (1, 3))
#            self.beamCenterXSpinBox.setEnabled(pValue in (1, 3) and self.beamCenterCheckBox.isChecked())
#            self.beamCenterYSpinBox.setEnabled(pValue in (1, 3) and self.beamCenterCheckBox.isChecked())
#            self.normalisationCheckBox.setEnabled(pValue in (0, 3))
#            self.normalisationDoubleSpinBox.setEnabled(pValue in (0, 3) and self.normalisationCheckBox.isChecked())
#            self.beamStopDiodeCheckBox.setEnabled(pValue in (0, 3))
#            self.beamStopDiodeDoubleSpinBox.setEnabled(pValue in (0, 3) and self.beamStopDiodeCheckBox.isChecked())
#            self.machineCurrentCheckBox.setEnabled(pValue in (1, 3))
#            self.machineCurrentDoubleSpinBox.setEnabled(pValue in (1, 3) and self.machineCurrentCheckBox.isChecked())



    def directoryLineEditChanged(self, pValue):
        if not self.__isReprocessing:
            self.__validParameters[0] = pValue is not None and os.path.exists(pValue) and not os.path.isfile(pValue)
            if self.__validParameters[0]:
                if str(pValue).find(" ") == -1:
                    self.directoryLineEdit.palette().setColor(QtGui.QPalette.Base, QtGui.QColor(255, 255, 255))
                else:
                    self.directoryLineEdit.palette().setColor(QtGui.QPalette.Base, QtGui.QColor(255, 255, 0))
            else:
                self.directoryLineEdit.palette().setColor(QtGui.QPalette.Base, QtGui.QColor(255, 0, 0))
            self.populatePrefixComboBox()
            self.populateRunNumberListWidget()
            self.populateFrameComboBox()
            self.reprocessPushButton.setEnabled(False not in self.__validParameters)



    def directoryPushButtonClicked(self):
        directory = QtGui.QFileDialog.getExistingDirectory(self.brick_widget, "Choose a directory", self.directoryLineEdit.text())
        if directory != "":
            self.directoryLineEdit.setText(directory)


    def prefixComboBoxChanged(self, pValue):
        if not self.__isReprocessing:
            self.__validParameters[1] = pValue > 0
            self.populateRunNumberListWidget()
            self.populateFrameComboBox()
            self.reprocessPushButton.setEnabled(False not in self.__validParameters)



    def runNumberListWidgetChanged(self):
        if not self.__isReprocessing:
            selectedItemsCount = len(self.runNumberListWidget.selectedItems())
            self.populateFrameComboBox()
            self.__validParameters[2] = (selectedItemsCount > 0)
            self.__validParameters[3] = (selectedItemsCount > 1)
            self.frameFirstComboBox.setEnabled(selectedItemsCount < 2)
            self.frameLastComboBox.setEnabled(selectedItemsCount < 2)
            self.reprocessPushButton.setEnabled(False not in self.__validParameters)



    def frameFirstComboBoxChanged(self, pValue):
        if not self.__isReprocessing:
            self.__validParameters[3] = (pValue > 0 and self.frameLastComboBox.currentIndex() > 0 and int(self.frameFirstComboBox.currentText()) <= int(self.frameLastComboBox.currentText()))
            self.reprocessPushButton.setEnabled(False not in self.__validParameters)



    def frameLastComboBoxChanged(self, pValue):
        if not self.__isReprocessing:
            self.__validParameters[3] = (self.frameFirstComboBox.currentIndex() > 0 and pValue > 0 and int(self.frameFirstComboBox.currentText()) <= int(self.frameLastComboBox.currentText()))
            self.reprocessPushButton.setEnabled(False not in self.__validParameters)



    def concentrationCheckBoxToggled(self, pValue):
        if not self.__isReprocessing:
            self.concentrationDoubleSpinBox.setEnabled(pValue)


    def commentsCheckBoxToggled(self, pValue):
        if not self.__isReprocessing:
            self.commentsLineEdit.setEnabled(pValue)


    def codeCheckBoxToggled(self, pValue):
        if not self.__isReprocessing:
            self.codeLineEdit.setEnabled(pValue)


    def maskCheckBoxToggled(self, pValue):
        if not self.__isReprocessing:
            self.maskLineEdit.setEnabled(pValue)
            self.maskDirectoryPushButton.setEnabled(pValue)
            self.maskDisplayPushButton.setEnabled(pValue)


    def detectorDistanceCheckBoxToggled(self, pValue):
        if not self.__isReprocessing:
            self.detectorDistanceDoubleSpinBox.setEnabled(pValue)


    def waveLengthCheckBoxToggled(self, pValue):
        if not self.__isReprocessing:
            self.waveLengthDoubleSpinBox.setEnabled(pValue)


    def pixelSizeCheckBoxToggled(self, pValue):
        if not self.__isReprocessing:
            self.pixelSizeXDoubleSpinBox.setEnabled(pValue)
            self.pixelSizeYDoubleSpinBox.setEnabled(pValue)


    def beamCenterCheckBoxToggled(self, pValue):
        if not self.__isReprocessing:
            self.beamCenterXSpinBox.setEnabled(pValue)
            self.beamCenterYSpinBox.setEnabled(pValue)


    def normalisationCheckBoxToggled(self, pValue):
        if not self.__isReprocessing:
            self.normalisationDoubleSpinBox.setEnabled(pValue)


    def beamStopDiodeCheckBoxToggled(self, pValue):
        if not self.__isReprocessing:
            self.beamStopDiodeDoubleSpinBox.setEnabled(pValue)


    def machineCurrentCheckBoxToggled(self, pValue):
        if not self.__isReprocessing:
            self.machineCurrentDoubleSpinBox.setEnabled(pValue)



    def maskLineEditChanged(self, pValue):
        if not self.__isReprocessing:
            if pValue is not None:
                pValue = str(pValue)
                if os.path.isfile(pValue):
                    i = pValue.rfind(".")
                    if i != -1 and pValue[i - 4:i] == "_msk" and pValue[i + 1:] == "edf" and pValue.find(" ") == -1:
                        flag = 0
                    else:
                        flag = 1
                else:
                    flag = 2
            else:
                flag = 2
            if flag == 0:
                self.__validParameters[4] = True
                self.maskLineEdit.palette().setColor(QtGui.QPalette.Base, QtGui.QColor(255, 255, 255))
            elif flag == 1:
                self.__validParameters[4] = True
                self.maskLineEdit.palette().setColor(QtGui.QPalette.Base, QtGui.QColor(255, 255, 0))
            else:
                self.__validParameters[4] = False
                self.maskLineEdit.palette().setColor(QtGui.QPalette.Base, QtGui.QColor(255, 0, 0))
            self.maskDisplayPushButton.setEnabled(self.__validParameters[4] and self.maskCheckBox.isChecked())
            self.reprocessPushButton.setEnabled(False not in self.__validParameters)



    def maskDirectoryPushButtonClicked(self):
        qFileDialog = QtGui.QFileDialog(self.brick_widget, "Choose a mask file", self.maskLineEdit.text())
        qFileDialog.setAcceptMode(QtGui.QFileDialog.AcceptOpen)
        qFileDialog.setFilters(["ESRF Data Format (*.edf)"])
        if qFileDialog.exec_():
            self.maskLineEdit.setText(str(qFileDialog.selectedFiles()[0]))



    def maskDisplayPushButtonClicked(self):
        self.emit("displayItemChanged", str(self.maskLineEdit.text()))



    def reprocessPushButtonClicked(self):
        if Qt.QMessageBox.question(self.brick_widget, "Warning", "Are you sure that you want to reprocess data collection '" + str(self.prefixComboBox.currentText()) + "'?", Qt.QMessageBox.Yes, Qt.QMessageBox.No, Qt.QMessageBox.NoButton) == Qt.QMessageBox.Yes:
            self.setButtonState(1)
            self.SPECBusyTimer.start(20000)
            logging.getLogger().info("Start reprocessing...")
            self.emit("displayResetChanged")
            self.__isReprocessing = True

            runNumber = ""
            for item in self.runNumberListWidget.selectedItems():
                if runNumber == "":
                    runNumber = str(item.text())
                else:
                    runNumber += "," + str(item.text())

            if len(self.runNumberListWidget.selectedItems()) == 1:
                frameFirst = str(self.frameFirstComboBox.currentText())
                frameLast = str(self.frameLastComboBox.currentText())
            else:
                frameFirst = None
                frameLast = None

            if self.concentrationCheckBox.isEnabled() and self.concentrationCheckBox.isChecked():
                concentration = self.concentrationDoubleSpinBox.value()
            else:
                concentration = None

            if self.commentsCheckBox.isEnabled() and self.commentsCheckBox.isChecked():
                comments = self.commentsLineEdit.text()
            else:
                comments = None

            if self.codeCheckBox.isEnabled() and self.codeCheckBox.isChecked():
                code = self.codeLineEdit.text()
            else:
                code = None

            if self.maskCheckBox.isEnabled() and self.maskCheckBox.isChecked():
                mask = self.maskLineEdit.text()
            else:
                mask = None

            if self.detectorDistanceCheckBox.isEnabled() and self.detectorDistanceCheckBox.isChecked():
                detectorDistance = self.detectorDistanceDoubleSpinBox.value()
            else:
                detectorDistance = None

            if self.waveLengthCheckBox.isEnabled() and self.waveLengthCheckBox.isChecked():
                waveLength = self.waveLengthDoubleSpinBox.value()
            else:
                waveLength = None

            if self.pixelSizeCheckBox.isEnabled() and self.pixelSizeCheckBox.isChecked():
                pixelSizeX = self.pixelSizeXDoubleSpinBox.value()
                pixelSizeY = self.pixelSizeYDoubleSpinBox.value()
            else:
                pixelSizeX = None
                pixelSizeY = None

            if self.beamCenterCheckBox.isEnabled() and self.beamCenterCheckBox.isChecked():
                beamCenterX = self.beamCenterXSpinBox.value()
                beamCenterY = self.beamCenterYSpinBox.value()
            else:
                beamCenterX = None
                beamCenterY = None

            if self.normalisationCheckBox.isEnabled() and self.normalisationCheckBox.isChecked():
                normalisation = self.normalisationDoubleSpinBox.value()
            else:
                normalisation = None

            if self.beamStopDiodeCheckBox.isEnabled() and self.beamStopDiodeCheckBox.isChecked():
                beamStopDiode = self.beamStopDiodeDoubleSpinBox.value()
            else:
                beamStopDiode = None

            if self.machineCurrentCheckBox.isEnabled() and self.machineCurrentCheckBox.isChecked():
                machineCurrent = self.machineCurrentDoubleSpinBox.value()
            else:
                machineCurrent = None

            if self.keepOriginalCheckBox.isChecked():
                keepOriginal = "1"
            else:
                keepOriginal = "0"

            self.getObject("reprocess").reprocess(self.directoryLineEdit.text(),
                                                  self.prefixComboBox.currentText(),
                                                  runNumber,
                                                  frameFirst,
                                                  frameLast,
                                                  concentration,
                                                  comments,
                                                  code,
                                                  mask,
                                                  detectorDistance,
                                                  waveLength,
                                                  pixelSizeX,
                                                  pixelSizeY,
                                                  beamCenterX,
                                                  beamCenterY,
                                                  normalisation,
                                                  beamStopDiode,
                                                  machineCurrent,
                                                  keepOriginal,
                                                  "20",
                                                  "1")



    def abortPushButtonClicked(self):
        self.SPECBusyTimer.stop()
        self.__isReprocessing = False
        self.setButtonState(0)
        logging.getLogger().info("Aborting data reprocess!")
        self.getObject("reprocess").reprocessAbort()



    def setButtonState(self, pOption):
        if pOption == 0:     # normal
            self.keepOriginalCheckBox.setEnabled(True)
            self.notifyCheckBox.setEnabled(True)
            self.reprocessPushButton.setEnabled(True)
            self.abortPushButton.setEnabled(False)
        elif pOption == 1:   # reprocessing
            self.keepOriginalCheckBox.setEnabled(False)
            self.notifyCheckBox.setEnabled(False)
            self.reprocessPushButton.setEnabled(False)
            self.abortPushButton.setEnabled(True)
        elif pOption == 2:   # invalid parameters
            self.keepOriginalCheckBox.setEnabled(True)
            self.notifyCheckBox.setEnabled(True)
            self.reprocessPushButton.setEnabled(False)
            self.abortPushButton.setEnabled(False)
        if self.abortPushButton.isEnabled():
            self.abortPushButton.palette().setColor(QtGui.QPalette.Button, QtGui.QColor(255, 0, 0))
        else:
            self.abortPushButton.palette().setColor(QtGui.QPalette.Button, QtGui.QColor(235, 235, 235))




    def SPECBusyTimerTimeOut(self):
        self.SPECBusyTimer.stop()
        self.__isReprocessing = False
        self.setButtonState(0)
        logging.getLogger().warning("The frame (or 1D curve) was not reprocessed or didn't appear on time!")




    def populatePrefixComboBox(self):
        if os.path.exists(self.directoryLineEdit.text() + "/raw/"):
            directory = self.directoryLineEdit.text() + "/raw/"
        else:
            directory = self.directoryLineEdit.text() + "/"
        items = []
        if os.path.isdir(directory):
            try:
                for filename in os.listdir(directory):
                    #TODO: Why is this check needed ? SO 14/3 12 
                    if os.path.isfile(directory + filename):
                        prefix, run, frame, extra, extension = self.getFilenameDetails(filename)
                        if frame != "":
                            if self.detectorComboBox.currentIndex() == 0 and extension == "edf" or self.detectorComboBox.currentIndex() == 1 and extension == "gfrm":
                                try:
                                    items.index(prefix)
                                except ValueError:
                                    items.append(prefix)
            except Exception, e:
                logging.getLogger().error("Full Exception: " + str(e))
        items.sort()
        items.insert(0, "Select")
        currentText = self.prefixComboBox.currentText()
        self.prefixComboBox.clear()
        self.prefixComboBox.addItems(items)
        try:
            self.prefixComboBox.setCurrentIndex(items.index(currentText))
        except ValueError:
            self.prefixComboBox.setCurrentIndex(0)



    def populateRunNumberListWidget(self):
        items = []
        if self.prefixComboBox.currentIndex() > 0:
            if os.path.exists(self.directoryLineEdit.text() + "/raw/"):
                directory = self.directoryLineEdit.text() + "/raw/"
            else:
                directory = self.directoryLineEdit.text() + "/"
            if os.path.isdir(directory):
                try:
                    for filename in os.listdir(directory):
                        #TODO: Why is this check needed ? SO 14/3 12 
                        if os.path.isfile(directory + "/" + filename):
                            prefix, run, frame, extra, extension = self.getFilenameDetails(filename)
                            if self.detectorComboBox.currentIndex() == 0 and extension == "edf" or self.detectorComboBox.currentIndex() == 1 and extension == "gfrm":
                                if prefix == self.prefixComboBox.currentText():
                                    try:
                                        items.index(run)
                                    except ValueError:
                                        items.append(run)
                except Exception, e:
                    logging.getLogger().error("Full Exception: " + str(e))

        items.sort()
        itemsSelect = []
        for i in range(0, self.runNumberListWidget.count()):
            if self.runNumberListWidget.item(i).isSelected():
                itemsSelect.append(self.runNumberListWidget.item(i).text())

        self.runNumberListWidget.clear()
        self.runNumberListWidget.addItems(items)

        for i in range(0, self.runNumberListWidget.count()):
            if self.runNumberListWidget.item(i).text() in itemsSelect:
                self.runNumberListWidget.item(i).setSelected(True)



    def populateFrameComboBox(self):
        items = []
        if len(self.runNumberListWidget.selectedItems()) == 1:
            if self.prefixComboBox.currentIndex() > 0:
                if os.path.exists(self.directoryLineEdit.text() + "/raw/"):
                    directory = self.directoryLineEdit.text() + "/raw/"
                else:
                    directory = self.directoryLineEdit.text() + "/"
                if os.path.isdir(directory):
                    try:
                        for filename in os.listdir(directory):
                            #TODO: Why is this check needed ? SO 14/3 12 
                            if os.path.isfile(directory + "/" + filename):
                                prefix, run, frame, extra, extension = self.getFilenameDetails(filename)
                                if self.detectorComboBox.currentIndex() == 0 and extension == "edf" or self.detectorComboBox.currentIndex() == 1 and extension == "gfrm":
                                    if prefix == self.prefixComboBox.currentText():
                                        if frame != "":
                                            try:
                                                items.index(frame)
                                            except ValueError:
                                                items.append(frame)
                    except Exception, e:
                        logging.getLogger().error("Full Exception: " + str(e))
        items.sort()
        items.insert(0, "Select")
        self.frameFirstComboBox.clear()
        self.frameLastComboBox.clear()
        self.frameFirstComboBox.addItems(items)
        self.frameLastComboBox.addItems(items)



    def getFilenameDetails(self, pFilename):
        pFilename = str(pFilename)
        i = pFilename.rfind(".")
        if i == -1:
            file = pFilename
            extension = ""
        else:
            file = pFilename[:i]
            extension = pFilename[i + 1:]
        items = file.split("_")
        prefix = items[0]
        run = ""
        frame = ""
        extra = ""
        i = len(items)
        j = 1
        while j < i:
            if items[j].isdigit():
                run = items[j]
                j += 1
                break
            else:
                prefix.join("_".join(items[j]))
                j += 1
        if j < i:
            if items[j].isdigit():
                frame = items[j]
                j += 1
            while j < i:
                if extra == "":
                    extra = items[j]
                else:
                    extra.join("_".join(items[j]))
                j += 1

        return prefix, run, frame, extra, extension

