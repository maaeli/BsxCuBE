import sys, os, time, logging, exceptions

from Framework4.GUI      import Core
from Framework4.GUI.Core import Property, PropertyGroup, Connection, Signal, Slot

from CollectRobotDialog  import CollectRobotDialog
from CollectRobotObject  import CollectRobotObject

from PyQt4               import QtCore, QtGui, Qt, Qwt5 as qwt
from LeadingZeroSpinBox  import LeadingZeroSpinBox

from Samples             import CollectPars

from SPEC    import SPEC
from PyTango import DevState

__category__ = "BsxCuBE"

#
#  Class to get out graphics out of the DisplayCurve thread.
#
class DisplayCurve:
        lastFilename = ""
        
        def __init__(self, parent, timer, curve_filename, timeout):
            self.t0           = time.time()
            self.timeout      = timeout
            self.filename     = curve_filename
            self.parent       = parent
            self.timer        = timer
            self.lastFilename = ""
            self.do_display   = False
            
        def display_curve(self):
            self.parent.emitDisplayItemChanged(self.filename)
                        
        def __call__(self):
            if time.time() - self.t0 > self.timeout:
                logging.error("Could not get .dat file within the %d seconds timeout: %s", self.timeout, self.filename)
                self.timer.stop()
                del self.parent._curveList[self.parent._curveList.index(self.timer)]
                return

            if self.do_display:
                try:
                    self.display_curve()
                finally:
                    self.timer.stop()
                    del self.parent._curveList[self.parent._curveList.index(self.timer)]
            else:
                if os.path.exists(self.filename):
                    # =============================================
                    #  CLEAR DISPLAY IF CURVE DON'T BELONG TO PREVIOUS GROUP
                    # =============================================                                             
                    prefix0, run0, frame0, extra0, extension0 = self.parent.getFilenameDetails(DisplayCurve.lastFilename)
                    DisplayCurve.lastFilename = os.path.basename(self.filename)
                    prefix1, run1, frame1, extra1, extension1 = self.parent.getFilenameDetails(DisplayCurve.lastFilename)
                    if prefix0 != prefix1 or run0 != run1:
                        self.parent.displayReset()

                    # this is just for adding 1 s. more before really trying to open the file
                    self.do_display = True
                    
class CollectBrick(Core.BaseBrick):
    properties = {}
    connections = {"collect": Connection("Collect object",
                                             [Signal("collectDirectoryChanged",     "collectDirectoryChanged"),
                                              Signal("collectPrefixChanged",        "collectPrefixChanged"),
                                              Signal("collectRunNumberChanged",     "collectRunNumberChanged"),
                                              Signal("collectNumberFramesChanged",  "collectNumberFramesChanged"),
                                              Signal("collectTimePerFrameChanged",  "collectTimePerFrameChanged"),
                                              Signal("collectConcentrationChanged", "collectConcentrationChanged"),
                                              Signal("collectCommentsChanged",      "collectCommentsChanged"),
                                              Signal("collectCodeChanged",          "collectCodeChanged"),
                                              Signal("collectMaskFileChanged",      "collectMaskFileChanged"),
                                              Signal("collectDetectorDistanceChanged", "collectDetectorDistanceChanged"),
                                              Signal("collectWaveLengthChanged",    "collectWaveLengthChanged"),
                                              Signal("collectPixelSizeXChanged",    "collectPixelSizeXChanged"),
                                              Signal("collectPixelSizeYChanged",    "collectPixelSizeYChanged"),
                                              Signal("collectBeamCenterXChanged",   "collectBeamCenterXChanged"),
                                              Signal("collectBeamCenterYChanged",   "collectBeamCenterYChanged"),
                                              Signal("collectNormalisationChanged", "collectNormalisationChanged"),
                                              Signal("collectProcessDataChanged",   "collectProcessDataChanged"),
                                              Signal("collectNewFrameChanged",      "collectNewFrameChanged"),
                                              Signal("checkBeamChanged",            "checkBeamChanged"),
                                              Signal("beamLostChanged",             "beamLostChanged")],
                                            [Slot("testCollect"),
                                             Slot("collect"),
                                             Slot("collectAbort")],
                                            "collectObjectConnected"),
                    "login": Connection("Login object",
                                            [Signal("expertModeChanged", "expertModeChanged")],
                                             [],
                                             "connectionStatusChanged"),
                    "motoralignment": Connection("MotorAlignment object",
                                            [Signal("executeTestCollect", "executeTestCollect")],
                                             [],
                                             "connectionStatusChanged"),
                    "sample_changer": Connection("SampleChanger object",
                                             [],
                                             [],
                                             'sample_changer_connected'),
                    "image_proxy": Connection("image proxy",
                                             [Signal('new_curves_data', 'y_curves_data'), Signal('erase_curve', 'erase_curve')],
                                             [],
                                             "image_proxy_connected"),
                    #"spec_exp":    Connection("spec exp hutch",
                                             #[Signal("specStatusChanged","specStatusChanged")],
                                             #[Slot('abort'), Slot('abort')],
                                             #"exp_spec_connected")
                    }
                                             

    
    # =============================================
    #  SIGNALS/SLOTS DEFINITION
    # =============================================
    signals = [Signal("displayResetChanged"),
               Signal("displayItemChanged"),
               Signal("transmissionChanged")]    
    slots = []

    def image_proxy_connected(self, image_proxy):
        self.image_proxy = image_proxy

    def exp_spec_connected(self, spec):
        if spec != None:
           self.spec = spec

    def collectDirectoryChanged(self, pValue):
        self.directoryLineEdit.setText(pValue)

    def collectPrefixChanged(self, pValue):
        self.prefixLineEdit.setText(pValue)

    def collectRunNumberChanged(self, pValue):
        self.runNumberSpinBox.setValue(int(pValue))

    def collectNumberFramesChanged(self, pValue):
        self.frameNumberSpinBox.setValue(int(pValue))

    def collectTimePerFrameChanged(self, pValue):
        self.timePerFrameSpinBox.setValue(int(pValue))

    def collectConcentrationChanged(self, pValue):
        self.concentrationDoubleSpinBox.setValue(float(pValue))

    def collectCommentsChanged(self, pValue):
        self.commentsLineEdit.setText(pValue)

    def collectCodeChanged(self, pValue):
        self.codeLineEdit.setText(pValue)

    def collectMaskFileChanged(self, pValue):
        self.maskLineEdit.setText(pValue)

    def collectDetectorDistanceChanged(self, pValue):
        self.detectorDistanceDoubleSpinBox.setValue(float(pValue))

    def collectWaveLengthChanged(self, pValue):
        self.waveLengthDoubleSpinBox.setValue(float(pValue))

    def collectPixelSizeXChanged(self, pValue):
        self.pixelSizeXDoubleSpinBox.setValue(float(pValue))

    def collectPixelSizeYChanged(self, pValue):
        self.pixelSizeYDoubleSpinBox.setValue(float(pValue))

    def collectBeamCenterXChanged(self, pValue):
        self.beamCenterXSpinBox.setValue(int(pValue))

    def collectBeamCenterYChanged(self, pValue):
        self.beamCenterYSpinBox.setValue(int(pValue))

    def collectNormalisationChanged(self, pValue):
        self.normalisationDoubleSpinBox.setValue(float(pValue))

    def collectProcessDataChanged(self, pValue):
        self.processCheckBox.setChecked(pValue == "1")

    def collectNewFrameChanged(self, pValue): 
        filename0 = pValue.split(",")[0]
        if os.path.dirname(filename0)[-4:] == "/raw":
            directory = os.path.dirname(filename0)[:-4] + "/1d/"
        else:
            directory = os.path.dirname(filename0) + "/1d/"
            

        if self.__lastFrame is None or self.__lastFrame != pValue:
            self.__lastFrame = pValue
            if self._isCollecting:
                
                message = "The frame '%s' was collected..." % filename0              
                logging.getLogger().info(message)
                if self.robotCheckBox.isChecked():
                    self._collectRobotDialog.addHistory(0, message)
                
                self._currentFrame += 1

                self.setCollectionStatus(status="running", progress=[ self._currentFrame, self._frameNumber ] )

                if not self.__isTesting:
                    if self.processCheckBox.isChecked():

                        def wait_data(datafile, timeout):
                            new_wait_curve_timer = Qt.QTimer(self.brick_widget)
                            self._curveList.append(new_wait_curve_timer)
                            new_wait_curve_timer.display_curve = DisplayCurve(self, new_wait_curve_timer, datafile, timeout)
                            QtCore.QObject.connect(new_wait_curve_timer, Qt.SIGNAL("timeout()"), new_wait_curve_timer.display_curve)
                            new_wait_curve_timer.start(1000)
                            
                        # have to wait for new .dat file, and display it when possible
                        wait_data(directory + os.path.basename(filename0).split(".")[0] + ".dat", 30)
                        
                        if self._currentFrame == self._frameNumber:
                            splitList = os.path.basename(filename0).split("_")                    
                            for i in range(0, len(splitList) - 1):
                                if i == 0:
                                    filename1 = splitList[i]
                                else:
                                    filename1 += "_" + splitList[i]
                            wait_data(directory + filename1 + "_ave.dat", 30)
                        
                self.emitDisplayItemChanged(filename0)        
            else:
                if os.path.exists(filename0):
                    if filename0.split(".")[-1] != "dat":
                        filename1 = directory + os.path.basename(filename0).split(".")[0] + ".dat"    
                        if os.path.exists(filename1):
                            filename0 += "," + filename1                    
                    self.emitDisplayItemChanged(filename0)
                         
            if self._currentFrame == self._frameNumber:
                if self._isCollecting:
                    if self.__isTesting:
                        if self.SPECBusyTimer.isActive():
                            self.SPECBusyTimerTimeOut()
                        logging.getLogger().info("The data collection is done!")
                    else:
                        feedBackFlag = self._feedBackFlag
                        if self.robotCheckBox.isChecked():
                            self.setCollectionStatus("done")
                            self._feedBackFlag = False
                            self.__isTesting = False
                        else:
                            if self.SPECBusyTimer.isActive():
                                self.SPECBusyTimerTimeOut()
                        if feedBackFlag:                
                            time.sleep(3)
                            logging.getLogger().info("The data collection is done!")
                            if self.notifyCheckBox.isChecked():
                                Qt.QMessageBox.information(self.brick_widget, "Info", "\n                       The data collection is done!                                       \n")
    
    def beamLostChanged(self, pValue):
        if pValue != None and pValue != "":
            logging.getLogger().error("BEAM LOST: %s" % pValue)

    def checkBeamChanged(self, pValue):
        if pValue == 1:
             self.checkBeamBox.setChecked(True) 
        else:
             self.checkBeamBox.setChecked(False) 

    # When a macro in spec changes the value of SPEC_STATUS variable to busy
    def specStatusChanged(self, pValue):
        if pValue == "busy":
           setCollectionStatus(self, "busy", progress=None)
        else:
           setCollectionStatus(self, "ready",   progress=None)

    def expertModeChanged(self, pValue):
        self.__expertMode = pValue
        self.setWidgetState()

    def executeTestCollect(self):
        self.testPushButtonClicked()

    def emitDisplayItemChanged(self, pValue):
        self.emit("displayItemChanged", str(pValue))

        if self.image_proxy is None:
          return
        try:
            logging.info(str(pValue))
            self.image_proxy.load_files(str(pValue))
        except Exception, e:
            logging.exception(e)
        
    def y_curves_data(self,pPeer):
        pass 
    def erase_curve(self,pPeer):
        pass 
    def connectionStatusChanged(self, pPeer):
        pass

    # =============================================
    #  CONSTRUCTOR
    # =============================================                    
    def __init__(self, *args, **kargs):
        Core.BaseBrick.__init__(self, *args, **kargs)

    # =============================================
    #  WIDGET DEFINITION
    # =============================================
    def init(self):

        self.nbPlates       = 0
        self.platesIDs      = []
        self.plateInfos     = []

        self._feedBackFlag       = False
        self._abortFlag          = False
        self._frameNumber        = 0
        self._currentFrame       = 0
        self._currentCurve       = 0

        self._collectRobotDialog = CollectRobotDialog(self)
        self.__lastFrame  = None        
        self.__currentConcentration = None        
        self.__isTesting  = False
        self.__expertMode = False

        self.__validParameters = [False, False, False]
        self._curveList = []
        self.image_proxy = None 
                
        self.brick_widget.setLayout(Qt.QVBoxLayout())
        
        self.readOnlyCheckBox = Qt.QCheckBox("Read only", self.brick_widget)
        Qt.QObject.connect(self.readOnlyCheckBox, Qt.SIGNAL("toggled(bool)"), self.readOnlyCheckBoxToggled)
        self.brick_widget.layout().addWidget(self.readOnlyCheckBox)
        
        self.hBoxLayout0 = Qt.QHBoxLayout()
        self.directoryLabel = Qt.QLabel("Directory", self.brick_widget)
        self.directoryLabel.setFixedWidth(130)
        self.hBoxLayout0.addWidget(self.directoryLabel)
        self.directoryLineEdit = Qt.QLineEdit(self.brick_widget)
        self.directoryLineEdit.setMaxLength(100)
        self.hBoxLayout0.addWidget(self.directoryLineEdit)
        Qt.QObject.connect(self.directoryLineEdit, Qt.SIGNAL("textChanged(const QString &)"), self.directoryLineEditChanged)        
        self.directoryPushButton = Qt.QPushButton("...", self.brick_widget)        
        self.directoryPushButton.setFixedWidth(25)
        Qt.QObject.connect(self.directoryPushButton, Qt.SIGNAL("clicked()"), self.directoryPushButtonClicked)
        self.hBoxLayout0.addWidget(self.directoryPushButton)
        self.brick_widget.layout().addLayout(self.hBoxLayout0)
                
        self.hBoxLayout1 = Qt.QHBoxLayout()
        self.prefixLabel = Qt.QLabel("Prefix", self.brick_widget)
        self.prefixLabel.setFixedWidth(130)
        self.hBoxLayout1.addWidget(self.prefixLabel)
        self.prefixLineEdit = Qt.QLineEdit(self.brick_widget)
        self.prefixLineEdit.setMaxLength(30)
        self.prefixLineEdit.setValidator(Qt.QRegExpValidator(Qt.QRegExp("^[a-zA-Z][a-zA-Z0-9_]*"), self.prefixLineEdit))        
        Qt.QObject.connect(self.prefixLineEdit, Qt.SIGNAL("textChanged(const QString &)"), self.prefixLineEditChanged)
        self.hBoxLayout1.addWidget(self.prefixLineEdit)
        self.brick_widget.layout().addLayout(self.hBoxLayout1)
        
        self.hBoxLayout2 = Qt.QHBoxLayout()
        self.runNumberLabel = Qt.QLabel("Run #", self.brick_widget)
        self.runNumberLabel.setFixedWidth(130)
        self.hBoxLayout2.addWidget(self.runNumberLabel)        
        self.runNumberSpinBox = LeadingZeroSpinBox(self.brick_widget, 3)
        self.runNumberSpinBox.setRange(1, 999)
        self.hBoxLayout2.addWidget(self.runNumberSpinBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout2)                                

        self.hBoxLayout3 = Qt.QHBoxLayout()
        self.frameNumberLabel = Qt.QLabel("Frame #", self.brick_widget)
        self.frameNumberLabel.setFixedWidth(130)
        self.hBoxLayout3.addWidget(self.frameNumberLabel)        
        self.frameNumberSpinBox = LeadingZeroSpinBox(self.brick_widget, 2)
        self.frameNumberSpinBox.setRange(1, 99)
        self.hBoxLayout3.addWidget(self.frameNumberSpinBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout3)                                
                                
        self.hBoxLayout4 = Qt.QHBoxLayout()
        self.timePerFrameLabel = Qt.QLabel("Time per frame", self.brick_widget)
        self.timePerFrameLabel.setFixedWidth(130)
        self.hBoxLayout4.addWidget(self.timePerFrameLabel)        
        self.timePerFrameSpinBox = Qt.QSpinBox(self.brick_widget)
        self.timePerFrameSpinBox.setSuffix(" s")
        self.timePerFrameSpinBox.setRange(1, 99)
        self.hBoxLayout4.addWidget(self.timePerFrameSpinBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout4)

        self.hBoxLayout5 = Qt.QHBoxLayout()
        self.concentrationLabel = Qt.QLabel("Concentration", self.brick_widget)
        self.concentrationLabel.setFixedWidth(130)
        self.hBoxLayout5.addWidget(self.concentrationLabel)
        self.concentrationDoubleSpinBox = Qt.QDoubleSpinBox(self.brick_widget)
        self.concentrationDoubleSpinBox.setSuffix(" mg/ml")
        self.concentrationDoubleSpinBox.setDecimals(2)        
        self.concentrationDoubleSpinBox.setRange(0, 100)
        self.hBoxLayout5.addWidget(self.concentrationDoubleSpinBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout5)

        self.hBoxLayout6 = Qt.QHBoxLayout()
        self.commentsLabel = Qt.QLabel("Comments", self.brick_widget)
        self.commentsLabel.setFixedWidth(130)
        self.hBoxLayout6.addWidget(self.commentsLabel)
        self.commentsLineEdit = Qt.QLineEdit(self.brick_widget)
        self.commentsLineEdit.setMaxLength(100)
        self.commentsLineEdit.setValidator(Qt.QRegExpValidator(Qt.QRegExp("[a-zA-Z0-9\\%/()=+*^:.\-_ ]*"), self.commentsLineEdit))        
        self.hBoxLayout6.addWidget(self.commentsLineEdit)
        self.brick_widget.layout().addLayout(self.hBoxLayout6)


        self.hBoxLayout7 = Qt.QHBoxLayout()
        self.codeLabel = Qt.QLabel("Code", self.brick_widget)
        self.codeLabel.setFixedWidth(130)
        self.hBoxLayout7.addWidget(self.codeLabel)                
        self.codeLineEdit = Qt.QLineEdit(self.brick_widget)
        self.codeLineEdit.setMaxLength(30)
        self.codeLineEdit.setValidator(Qt.QRegExpValidator(Qt.QRegExp("^[a-zA-Z][a-zA-Z0-9_]*"), self.codeLineEdit))        
        self.hBoxLayout7.addWidget(self.codeLineEdit)
        self.brick_widget.layout().addLayout(self.hBoxLayout7)

        self.hBoxLayout61 = Qt.QHBoxLayout()
        self.blParamsButton = Qt.QPushButton("Show Beamline Parameters", self.brick_widget)
        self.blParamsButton.setFixedWidth(230)
        self.hBoxLayout61.addWidget(self.blParamsButton)
        self.brick_widget.layout().addLayout(self.hBoxLayout61)
        Qt.QObject.connect(self.blParamsButton, Qt.SIGNAL("clicked()"), self.showHideBeamlineParams)

        self.hBoxLayout8 = Qt.QHBoxLayout()
        self.maskLabel = Qt.QLabel("Mask", self.brick_widget)
        self.maskLabel.setFixedWidth(130)
        self.hBoxLayout8.addWidget(self.maskLabel)
        self.maskLineEdit = Qt.QLineEdit(self.brick_widget)
        self.maskLineEdit.setMaxLength(100)
        Qt.QObject.connect(self.maskLineEdit, Qt.SIGNAL("textChanged(const QString &)"), self.maskLineEditChanged)
        self.hBoxLayout8.addWidget(self.maskLineEdit)
        self.maskDirectoryPushButton = Qt.QPushButton("...", self.brick_widget)
        self.maskDirectoryPushButton.setFixedWidth(25)        
        Qt.QObject.connect(self.maskDirectoryPushButton, Qt.SIGNAL("clicked()"), self.maskDirectoryPushButtonClicked)
        self.hBoxLayout8.addWidget(self.maskDirectoryPushButton)
        self.maskDisplayPushButton = Qt.QPushButton("Display", self.brick_widget)
        self.maskDisplayPushButton.setFixedWidth(55)        
        Qt.QObject.connect(self.maskDisplayPushButton, Qt.SIGNAL("clicked()"), self.maskDisplayPushButtonClicked)
        self.hBoxLayout8.addWidget(self.maskDisplayPushButton)        
        self.brick_widget.layout().addLayout(self.hBoxLayout8)
        
        self.hBoxLayout9 = Qt.QHBoxLayout()
        self.detectorDistanceLabel = Qt.QLabel("Detector distance", self.brick_widget)
        self.detectorDistanceLabel.setFixedWidth(130)
        self.hBoxLayout9.addWidget(self.detectorDistanceLabel)
        self.detectorDistanceDoubleSpinBox = Qt.QDoubleSpinBox(self.brick_widget)
        self.detectorDistanceDoubleSpinBox.setSuffix(" m")
        self.detectorDistanceDoubleSpinBox.setDecimals(3)
        self.detectorDistanceDoubleSpinBox.setRange(0.1, 10)
        self.hBoxLayout9.addWidget(self.detectorDistanceDoubleSpinBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout9)
        
        self.hBoxLayout10 = Qt.QHBoxLayout()
        self.waveLengthLabel = Qt.QLabel("Wave length", self.brick_widget)
        self.waveLengthLabel.setFixedWidth(130)
        self.hBoxLayout10.addWidget(self.waveLengthLabel)
        self.waveLengthDoubleSpinBox = Qt.QDoubleSpinBox(self.brick_widget)
        self.waveLengthDoubleSpinBox.setSuffix(" nm")
        self.waveLengthDoubleSpinBox.setDecimals(4)
        self.waveLengthDoubleSpinBox.setRange(0.01, 1)
        self.hBoxLayout10.addWidget(self.waveLengthDoubleSpinBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout10)
               
        self.hBoxLayout11 = Qt.QHBoxLayout()
        self.pixelSizeLabel = Qt.QLabel("Pixel size (x, y)", self.brick_widget)
        self.pixelSizeLabel.setFixedWidth(130)
        self.hBoxLayout11.addWidget(self.pixelSizeLabel)        
        self.pixelSizeXDoubleSpinBox = Qt.QDoubleSpinBox(self.brick_widget)
        self.pixelSizeXDoubleSpinBox.setSuffix(" um")
        self.pixelSizeXDoubleSpinBox.setDecimals(1)        
        self.pixelSizeXDoubleSpinBox.setRange(10, 500)
        self.hBoxLayout11.addWidget(self.pixelSizeXDoubleSpinBox)
        self.pixelSizeYDoubleSpinBox = Qt.QDoubleSpinBox(self.brick_widget)
        self.pixelSizeYDoubleSpinBox.setSuffix(" um")
        self.pixelSizeYDoubleSpinBox.setDecimals(1)
        self.pixelSizeYDoubleSpinBox.setRange(10, 500)
        self.hBoxLayout11.addWidget(self.pixelSizeYDoubleSpinBox)        
        self.brick_widget.layout().addLayout(self.hBoxLayout11)                               

        self.hBoxLayout12 = Qt.QHBoxLayout()
        self.beamCenterLabel = Qt.QLabel("Beam center (x, y)", self.brick_widget)
        self.beamCenterLabel.setFixedWidth(130)
        self.hBoxLayout12.addWidget(self.beamCenterLabel)        
        self.beamCenterXSpinBox = Qt.QSpinBox(self.brick_widget)
        self.beamCenterXSpinBox.setSuffix(" px")
        self.beamCenterXSpinBox.setRange(1, 9999)
        self.hBoxLayout12.addWidget(self.beamCenterXSpinBox)
        self.beamCenterYSpinBox = Qt.QSpinBox(self.brick_widget)
        self.beamCenterYSpinBox.setSuffix(" px")
        self.beamCenterYSpinBox.setRange(1, 9999)
        self.hBoxLayout12.addWidget(self.beamCenterYSpinBox)        
        self.brick_widget.layout().addLayout(self.hBoxLayout12)

        self.hBoxLayout13 = Qt.QHBoxLayout()
        self.normalisationLabel = Qt.QLabel("Normalisation", self.brick_widget)
        self.normalisationLabel.setFixedWidth(130)
        self.hBoxLayout13.addWidget(self.normalisationLabel)
        self.normalisationDoubleSpinBox = Qt.QDoubleSpinBox(self.brick_widget)
        self.normalisationDoubleSpinBox.setDecimals(7)
        self.normalisationDoubleSpinBox.setRange(0.0001, 10000)
        self.hBoxLayout13.addWidget(self.normalisationDoubleSpinBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout13)
        
        self.vBoxLayout0 = Qt.QVBoxLayout()
        self.vBoxLayout0.addSpacing(15)
        self.brick_widget.layout().addLayout(self.vBoxLayout0)        
                       
        self.hBoxLayout16 = Qt.QHBoxLayout()
        self.processCheckBox = Qt.QCheckBox("Process after collect", self.brick_widget)
        self.hBoxLayout16.addWidget(self.processCheckBox)        
        self.robotCheckBox = Qt.QCheckBox("Collect using robot", self.brick_widget)
        Qt.QObject.connect(self.robotCheckBox, Qt.SIGNAL("toggled(bool)"), self.robotCheckBoxToggled)
        self.hBoxLayout16.addWidget(self.robotCheckBox)        
        self.brick_widget.layout().addLayout(self.hBoxLayout16)
        
        self.hBoxLayout17 = Qt.QHBoxLayout()
        self.notifyCheckBox = Qt.QCheckBox("Notify when done", self.brick_widget)
        self.notifyCheckBox.setChecked(True)
        self.hBoxLayout17.addWidget(self.notifyCheckBox)        
        self.hdfCheckBox = Qt.QCheckBox("Save to HDF file", self.brick_widget)        
        self.hBoxLayout17.addWidget(self.hdfCheckBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout17)
        
        self.hBoxLayout171 = Qt.QHBoxLayout()
        self.checkBeamBox = Qt.QCheckBox("Check beam", self.brick_widget)
        self.checkBeamBox.setChecked(True)
        Qt.QObject.connect(self.checkBeamBox, Qt.SIGNAL("toggled(bool)"), self.checkBeamBoxToggled)
        self.hBoxLayout171.addWidget(self.checkBeamBox)        
        self.brick_widget.layout().addLayout(self.hBoxLayout171)
        
        self.hBoxLayout18 = Qt.QHBoxLayout()
        self.testPushButton = Qt.QPushButton("Test", self.brick_widget)
        self.testPushButton.setToolTip("Collect test frame (during 1 second) with the specified parameters")
        self.hBoxLayout18.addWidget(self.testPushButton)
        Qt.QObject.connect(self.testPushButton, Qt.SIGNAL("clicked()"), self.testPushButtonClicked)
        self.collectPushButton = Qt.QPushButton("Collect", self.brick_widget)
        self.collectPushButton.setToolTip("Start collecting frame(s) with the specified parameters")
        self.hBoxLayout18.addWidget(self.collectPushButton)
        Qt.QObject.connect(self.collectPushButton, Qt.SIGNAL("clicked()"), self.collectPushButtonClicked)
        self.brick_widget.layout().addLayout(self.hBoxLayout18)

        self.hBoxLayout19 = Qt.QHBoxLayout()
        self.abortPushButton = Qt.QPushButton("Abort", self.brick_widget)
        self.abortPushButton.setToolTip("Abort ongoing data collection")
        self.abortPushButton.setObjectName("abortbutton")
        self.hBoxLayout19.addWidget(self.abortPushButton)
        Qt.QObject.connect(self.abortPushButton, Qt.SIGNAL("clicked()"), self.abortPushButtonClicked)
        self.brick_widget.layout().addLayout(self.hBoxLayout19)                
        
        self.hBoxLayout20 = Qt.QHBoxLayout()
        self.collectStatusLabel = Qt.QLabel("Collection status:")
        self.collectStatusLabel.setAlignment(QtCore.Qt.AlignRight)
        self.collectStatus      = Qt.QLabel("")
        self.collectStatus.setAlignment(QtCore.Qt.AlignCenter)
        self.collectStatus.setObjectName("collect")
        self.hBoxLayout20.addWidget(self.collectStatusLabel)
        self.hBoxLayout20.addWidget(self.collectStatus)
        self.brick_widget.layout().addLayout(self.hBoxLayout20)                
        
        #
        # validation colors
        #
        self.brick_widget.setStyleSheet('*[valid="true"]  {background-color: white}\
                            *[valid="false"] {background-color: #faa}\
                            #abortbutton[abortactive="true"]  {background-color: red;color: white}\
                            #abortbutton[abortactive="false"] {background-color: #fff;color: black}\
                            #collect[status="ready"]   {background-color: #0f0;color: black;font-weight: bold; alignment: center}\
                            #collect[status="done"]    {background-color: #0f0;color: black;font-weight: bold; alignment: center}\
                            #collect[status="busy"]    {background-color: yellow;color: black;font-weight: bold;alignment: center}\
                            #collect[status="aborting"]  {background-color: magenta;color: black;font-weight: bold;alignment: center}\
                            #collect[status="running"] {background-color: yellow;color: black;font-weight: bold;alignment: center}')

        self.setCollectionStatus("ready")

        self.showingBLParams = 1
        self.showHideBeamlineParams(None)

        self.directoryLineEditChanged(None)
        self.prefixLineEditChanged(None)
        self.maskLineEditChanged(None)
    
        self.SPECBusyTimer = Qt.QTimer(self.brick_widget)
        Qt.QObject.connect(self.SPECBusyTimer, Qt.SIGNAL("timeout()"), self.SPECBusyTimerTimeOut)
                
        self._sampleChangerDisplayFlag = False
        self._sampleChangerDisplayMessage = ""        
        
        self._collectRobot = CollectRobotObject(self, self.brick_widget)

        QtCore.QObject.connect(self._collectRobot.proxySampleChanger ,QtCore.SIGNAL("doSampleChangerAction"), self.doSampleChangerAction, Qt.Qt.BlockingQueuedConnection)
        QtCore.QObject.connect(self._collectRobot.proxyRobot         ,QtCore.SIGNAL("robotCollect"),          self.doRobotCollect,        Qt.Qt.BlockingQueuedConnection)
        QtCore.QObject.connect(self._collectRobot.proxyRobot         ,QtCore.SIGNAL("robotCollectEnd"),       self.doRobotCollectEnd,     Qt.Qt.BlockingQueuedConnection)
        QtCore.QObject.connect(self._collectRobot.proxyRobot         ,QtCore.SIGNAL("getCollectPars"),        self.doGetCollectPars,      Qt.Qt.BlockingQueuedConnection)
        QtCore.QObject.connect(self._collectRobot.proxyRobot         ,QtCore.SIGNAL("getFileInfo"),           self.doGetFileInfo,         Qt.Qt.BlockingQueuedConnection)
        QtCore.QObject.connect(self._collectRobot.proxyRobot         ,QtCore.SIGNAL("showMessage"),           self.doShowMessage,         Qt.Qt.BlockingQueuedConnection)

        QtCore.QObject.connect(self._collectRobot, QtCore.SIGNAL("displayReset"),   self.displayReset,   Qt.Qt.BlockingQueuedConnection)

        # start robot thread
        self._collectRobot.start()
            
        self.setWidgetState()
        self.setButtonState(0)

    # Proxy actions
    def doSampleChangerAction(self, action_name, argdict=None):
        method = getattr( self._sampleChanger, action_name )
        try:
            r=method(*argdict['args'])
        except:
            logging.warning("Lost connection with Sample Changer. Please abort data collection")
            argdict['returned'] = None
        else:
            argdict['returned'] = r
        
    def doRobotCollect(self,argdict=None):
        self.startCollection(mode="robot")

        r = self.collect(*argdict['args'])
        argdict['returned'] = r

    def doRobotCollectEnd(self,argdict=None):
        logging.info("doRobotCollectEnd")
        self.setCollectionStatus("done")
        r = self.setButtonState(0)                
        argdict['returned'] = r

    def doGetCollectPars(self,ret):
        r = self.getCollectPars(robot=1)
        ret['returned'] = r

    def doGetFileInfo(self,ret):
        r = self.getFileInfo()
        ret['returned'] = r

    def doShowMessage(self, argdict=None):
        r = self.showMessage(*argdict['args']) 
        argdict['returned'] = r

    def collectObjectConnected(self, collect_obj):
        self.collectObj = collect_obj
        if self.collectObj is not None:
          self.collectObj.updateChannels() 

    #
    #  Other
    #
    def sample_changer_connected(self, sc):

        #  How to read an attribute?
        self._sampleChanger = sc
        if sc is None:
            return
        self.nbPlates       = 3
        self.plateInfos     = [sc.getPlateInfo(i) for i in range(1,self.nbPlates+1)]
        
    def validParameters(self):

        # This routine checks:
        #   - that there is at least one sample defined and active
        #   - that there are not two buffers with same name
        #   - that the buffer assigned to a sample is existing
        #

        pars  = self.getCollectPars(robot=1)
        valid = True 

        if len(pars.sampleList) == 0:
            valid = False 
            Qt.QMessageBox.information(self.brick_widget, "Warning", "No sample to collect in robot!")
        else:
            buffernames = []

            for buffer in pars.bufferList:
                # NOW buffers of same name are allowed.  But we should do something about it during collect

                if buffer not in buffernames:
                    buffernames.append(buffer.buffername) 

            for sample in pars.sampleList:
                if sample.buffername not in buffernames:
                    Qt.QMessageBox.information(self.brick_widget, "Warning", "Sample with no buffer assignment or buffer name does not exist")
                    valid = False 
                    break

        return valid

    def getFileInfo(self, all=0):
         generalParsWidget = self
         filepars = CollectPars()
         filepars.prefix               = generalParsWidget.prefixLineEdit.text()
         filepars.runNumber            = generalParsWidget.runNumberSpinBox.value()
         filepars.frameNumber          = generalParsWidget.frameNumberSpinBox.value()
         return filepars

    def getCollectPars(self, robot=1):
         
         #
         # First of all. Collect collection values
         #
         collectpars = CollectPars()

         logging.info("   - reading collection parameters")
         #
         #  I should actually separate values so that each widget represents a certain data in a clear way
         #
         generalParsWidget = self
         robotParsWidget   = self._collectRobotDialog

         collectpars.directory            = generalParsWidget.directoryLineEdit.text()
         collectpars.prefix               = generalParsWidget.prefixLineEdit.text()
         collectpars.runNumber            = generalParsWidget.runNumberSpinBox.value()
         collectpars.frameNumber          = generalParsWidget.frameNumberSpinBox.value()
         collectpars.timePerFrame         = generalParsWidget.timePerFrameSpinBox.value()
         collectpars.currentConcentration = generalParsWidget.concentrationDoubleSpinBox.value()
         collectpars.currentComments      = generalParsWidget.commentsLineEdit.text()
         collectpars.currentCode          = generalParsWidget.codeLineEdit.text()

         collectpars.doProcess            = generalParsWidget.processCheckBox.isChecked()

         collectpars.mask                 = generalParsWidget.maskLineEdit.text()
         collectpars.detectorDistance     = generalParsWidget.detectorDistanceDoubleSpinBox.value()
         collectpars.waveLength           = generalParsWidget.waveLengthDoubleSpinBox.value()
         collectpars.pixelSizeX           = generalParsWidget.pixelSizeXDoubleSpinBox.value()
         collectpars.pixelSizeY           = generalParsWidget.pixelSizeYDoubleSpinBox.value()
         collectpars.beamCenterX          = generalParsWidget.beamCenterXSpinBox.value()
         collectpars.beamCenterY          = generalParsWidget.beamCenterYSpinBox.value()
         collectpars.normalisation        = generalParsWidget.normalisationDoubleSpinBox.value()

         if robot:
             logging.info("   - getting robot parameters") 
             # merge all parameters 
             robotpars    = robotParsWidget.getCollectRobotPars()   
             collectpars.__dict__.update( robotpars.__dict__ )
             logging.info("sample type is %s" , collectpars.sampleType)
             logging.info("number of samples is %s" , len(collectpars.sampleList))

         #=================================================
         # Correct value for processData 
         #=================================================
         if collectpars.doProcess:  # in principle this is not necessary as True and False values should work.  TODO:  check this
              collectpars.processData = 1
         else:
              collectpars.processData = 0

         #=================================================
         #  Calculate total flow time
         #=================================================
         collectpars.flowTime = collectpars.timePerFrame * collectpars.frameNumber + collectpars.extraFlowTime

         return collectpars         

    # =============================================
    #  DESTRUCTOR
    # =============================================        
    def delete(self):
        self._collectRobot.terminate()

    # =============================================
    #  HANDLE PROPERTIES CHANGES
    # =============================================

    # =============================================
    #  HANDLE SIGNALS
    # =============================================            
    def showHideBeamlineParams(self, pValue=None):

        if self.showingBLParams:
             self.showingBLParams = 0
             self.blParamsButton.setText("Show Beamline Parameters")
             self.maskLineEdit.hide()
             self.maskDirectoryPushButton.hide()
             self.maskDisplayPushButton.hide()
             self.detectorDistanceDoubleSpinBox.hide()
             self.waveLengthDoubleSpinBox.hide()
             self.pixelSizeXDoubleSpinBox.hide()
             self.pixelSizeYDoubleSpinBox.hide()
             self.beamCenterXSpinBox.hide()
             self.beamCenterYSpinBox.hide()
             self.normalisationDoubleSpinBox.hide()
             self.maskLabel.hide()
             self.detectorDistanceLabel.hide()
             self.pixelSizeLabel.hide()
             self.waveLengthLabel.hide()
             self.beamCenterLabel.hide()
             self.normalisationLabel.hide()
        else:
             self.blParamsButton.setText("Hide Beamline Parameters")
             self.showingBLParams = 1
             self.maskLineEdit.show()
             self.maskDirectoryPushButton.show()
             self.maskDisplayPushButton.show()
             self.detectorDistanceDoubleSpinBox.show()
             self.waveLengthDoubleSpinBox.show()
             self.pixelSizeXDoubleSpinBox.show()
             self.pixelSizeYDoubleSpinBox.show()
             self.beamCenterXSpinBox.show()
             self.beamCenterYSpinBox.show()
             self.normalisationDoubleSpinBox.show()
             self.maskLabel.show()
             self.detectorDistanceLabel.show()
             self.pixelSizeLabel.show()
             self.waveLengthLabel.show()
             self.beamCenterLabel.show()
             self.normalisationLabel.show()

    def readOnlyCheckBoxToggled(self, pValue):

        self.directoryLineEdit.setEnabled             (not pValue)
        self.directoryPushButton.setEnabled           (not pValue)
        self.prefixLineEdit.setEnabled                (not pValue)
        self.runNumberSpinBox.setEnabled              (not pValue)        
        self.frameNumberSpinBox.setEnabled            (not pValue)
        self.timePerFrameSpinBox.setEnabled           (not pValue)
        self.maskLineEdit.setEnabled                  (not pValue and self.__expertMode)
        self.maskDirectoryPushButton.setEnabled       (not pValue and self.__expertMode)
        self.maskDisplayPushButton.setEnabled         (not pValue and self.__expertMode)
        self.detectorDistanceDoubleSpinBox.setEnabled (not pValue and self.__expertMode)
        self.waveLengthDoubleSpinBox.setEnabled       (not pValue and self.__expertMode)                        
        self.pixelSizeXDoubleSpinBox.setEnabled       (not pValue and self.__expertMode)
        self.pixelSizeYDoubleSpinBox.setEnabled       (not pValue and self.__expertMode)            
        self.beamCenterXSpinBox.setEnabled            (not pValue and self.__expertMode)
        self.beamCenterYSpinBox.setEnabled            (not pValue and self.__expertMode)
        self.normalisationDoubleSpinBox.setEnabled    (not pValue and self.__expertMode)

    def directoryLineEditChanged(self, pValue):
        if self._isCollecting:
            return

        self.__validParameters[0] = pValue is not None and os.path.exists(pValue) and not os.path.isfile(pValue)

        if self.__validParameters[0]:
            self.directoryLineEdit.setProperty("valid","true")
        else:
            self.directoryLineEdit.setProperty("valid","false")

        self.testPushButton.setEnabled(False not in self.__validParameters)
        self.collectPushButton.setEnabled(False not in self.__validParameters)

        self.brick_widget.setStyleSheet(self.brick_widget.styleSheet())

    def directoryPushButtonClicked(self):
        directory = QtGui.QFileDialog.getExistingDirectory(self.brick_widget, "Choose a directory", self.directoryLineEdit.text())
        if directory != "":
            self.directoryLineEdit.setText(directory)

    def prefixLineEditChanged(self, pValue):
        if self._isCollecting:
             return 

        self.__validParameters[1] = pValue is not None and self.prefixLineEdit.hasAcceptableInput()
        if self.__validParameters[1]:            
           self.prefixLineEdit.setProperty("valid","true")
        else:
           self.prefixLineEdit.setProperty("valid","false")

        self.testPushButton.setEnabled   (False not in self.__validParameters)
        self.collectPushButton.setEnabled(False not in self.__validParameters)

        self.brick_widget.setStyleSheet(self.brick_widget.styleSheet())

    def maskLineEditChanged(self, pValue):
        if self._isCollecting:
            return

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
            self.__validParameters[2] = True
            self.maskLineEdit.setProperty("valid","true")
        elif flag == 1:
            self.__validParameters[2] = True
            self.maskLineEdit.setProperty("valid","true")
        else:
            self.__validParameters[2] = False
            self.maskLineEdit.setProperty("valid","false")

        self.maskDisplayPushButton.setEnabled(self.__validParameters[2] and self.__expertMode)            
        self.testPushButton.setEnabled(False not in self.__validParameters)
        self.collectPushButton.setEnabled(False not in self.__validParameters)

        self.brick_widget.setStyleSheet(self.brick_widget.styleSheet())


    def maskDirectoryPushButtonClicked(self):
        qFileDialog = QtGui.QFileDialog(self.brick_widget, "Choose a mask file", self.maskLineEdit.text())
        qFileDialog.setAcceptMode(QtGui.QFileDialog.AcceptOpen)
        qFileDialog.setFilters(["ESRF Data Format (*.edf)"])
        if qFileDialog.exec_():
            self.maskLineEdit.setText(str(qFileDialog.selectedFiles()[0]))          


    def maskDisplayPushButtonClicked(self):
        self.emitDisplayItemChanged(str(self.maskLineEdit.text()))
                
    def robotCheckBoxToggled(self, pValue):
        if pValue:
            if self._collectRobotDialog.isVisible():
                self._collectRobotDialog.activateWindow()
                self._collectRobotDialog.raise_()            
            else:   
                self._collectRobotDialog.show()
        else:
            self._collectRobotDialog.hide()

    def checkBeamBoxToggled(self, pValue):
        self.getObject("collect").setCheckBeam(pValue)
        #self.getObject("collect").toggleCheckBeam()

    def testPushButtonClicked(self):

        self.setButtonState(1)
        self.SPECBusyTimer.start(15000)

        self.startCollection(mode='test')

        self._feedBackFlag = False
        self._abortFlag    = False
        self._frameNumber  = 1
        self._currentFrame = 0        

        self.getObject("collect").testCollect(self.directoryLineEdit.text(),
                                               self.prefixLineEdit.text(),
                                               self.runNumberSpinBox.value(),
                                               self.concentrationDoubleSpinBox.value(),
                                               self.commentsLineEdit.text(),
                                               self.codeLineEdit.text(),
                                               self.maskLineEdit.text(),
                                               self.detectorDistanceDoubleSpinBox.value(),
                                               self.waveLengthDoubleSpinBox.value(),
                                               self.pixelSizeXDoubleSpinBox.value(),
                                               self.pixelSizeYDoubleSpinBox.value(),                                   
                                               self.beamCenterXSpinBox.value(),
                                               self.beamCenterYSpinBox.value(),
                                               self.normalisationDoubleSpinBox.value())

    def collectPushButtonClicked(self):
        
        if not self.robotCheckBox.isChecked() or self.validParameters():
            directory = str(self.directoryLineEdit.text()) + "/raw"
            runNumber = "%03d" % self.runNumberSpinBox.value()
            flag = True
                    
            if os.path.isdir(directory):        
                for filename in os.listdir(directory):
                    if os.path.isfile(directory + "/" + filename):
                        if filename.startswith(str(self.prefixLineEdit.text()) + "_" + runNumber) and not filename.startswith(str(self.prefixLineEdit.text()) + "_" + runNumber + "_tst"):
                            flag = False
                            break
    
            if not flag:
                flag = (Qt.QMessageBox.question(self.brick_widget, "Warning", "The run '%s' with prefix '%s' already exists in the directory '%s'. Overwrite it?" % (runNumber, self.prefixLineEdit.text(), self.directoryLineEdit.text()), Qt.QMessageBox.Yes, Qt.QMessageBox.No, Qt.QMessageBox.NoButton) == Qt.QMessageBox.Yes)
            
            if not flag:                        
                return 

            if self.robotCheckBox.isChecked():
                self.startCollectWithRobot()
            else:                
                if not self.__expertMode: 

                        if self.__currentConcentration is not None and self.__currentConcentration == self.concentrationDoubleSpinBox.value():
                            flag = (Qt.QMessageBox.question(self.brick_widget, \
                                    "Warning", "The value of the concentration '%s' is the same than the previous collection. Continue?" % \
                                                  self.concentrationDoubleSpinBox.value(), \
                                                  Qt.QMessageBox.Yes, \
                                                  Qt.QMessageBox.No, Qt.QMessageBox.NoButton) == Qt.QMessageBox.Yes)
                            
                if flag:
                   self.startCollectWithoutRobot()

    def setCollectionStatus(self, status, progress=None):
        if status == "running":
           self._isCollecting = True
           self.abortPushButton.setEnabled(True)
           self.abortPushButton.setProperty("abortactive","true")
        else:
           self._isCollecting = False
           self.abortPushButton.setEnabled(False)
           self.abortPushButton.setProperty("abortactive","false")

        self.brick_widget.setStyleSheet(self.brick_widget.styleSheet())
        self.collectStatus.setText( status )
        self.collectStatus.setProperty("status", status)

        self.brick_widget.setStyleSheet(self.brick_widget.styleSheet())

    def startCollectWithRobot(self): 

        # starts a series of individual collections
        #  blocks widget or whatever during the time of the collection
        self.setButtonState(1)
        self._abortFlag = False                
        self._collectRobotDialog.clearHistory()
        self._collectRobot.robotStartCollection()

    def endCollectWithRobot(self): 
        # should unblock things here at the end
        pass
    
    def startCollectWithoutRobot(self): 
        # starts a single collection 
        self.setButtonState(1)
        self._abortFlag = False                    
        self.displayReset()

        if self.processCheckBox.isChecked():
            processData = 1
        else:
            processData = 0

        self.startCollection(mode="no robot")

        self.collect(1,
                      self.directoryLineEdit.text(),
                      self.prefixLineEdit.text(),
                      self.runNumberSpinBox.value(),
                      self.frameNumberSpinBox.value(),
                      self.timePerFrameSpinBox.value(),
                      self.concentrationDoubleSpinBox.value(),
                      self.commentsLineEdit.text(),
                      self.codeLineEdit.text(),
                      self.maskLineEdit.text(),
                      self.detectorDistanceDoubleSpinBox.value(),
                      self.waveLengthDoubleSpinBox.value(),
                      self.pixelSizeXDoubleSpinBox.value(),
                      self.pixelSizeYDoubleSpinBox.value(),                                   
                      self.beamCenterXSpinBox.value(),
                      self.beamCenterYSpinBox.value(),
                      self.normalisationDoubleSpinBox.value(),
                      processData)                    

        self.__currentConcentration = self.concentrationDoubleSpinBox.value()

                
    def startCollection(self,mode="normal"):

        self.setCollectionStatus("running")

        if mode == "test":
           self.__isTesting = True        

        logging.info("   - collection started (mode: %s)" % mode)
        
    def collect(self, pFeedBackFlag, pDirectory, pPrefix, pRunNumber, pFrameNumber, pTimePerFrame, pConcentration, pComments, pCode, pMaskFile, pDetectorDistance, pWaveLength, pPixelSizeX, pPixelSizeY, pBeamCenterX, pBeamCenterY, pNormalisation, pProcessData):

        if not self.robotCheckBox.isChecked():
            self.SPECBusyTimer.start(pFrameNumber * (pTimePerFrame + 5) * 1000  + 12000)

        self.__isTesting = False
        self._feedBackFlag = (pFeedBackFlag == 1)
        self._frameNumber = pFrameNumber
        self._currentFrame = 0
        self._currentCurve = 0    
        self.getObject("collect").collect(pDirectory,
                                          pPrefix,
                                          pRunNumber,
                                          pFrameNumber,
                                          pTimePerFrame,
                                          pConcentration,
                                          pComments,
                                          pCode,
                                          pMaskFile,
                                          pDetectorDistance,
                                          pWaveLength,
                                          pPixelSizeX,
                                          pPixelSizeY,                                               
                                          pBeamCenterX,
                                          pBeamCenterY,
                                          pNormalisation,                                               
                                          pProcessData)
    
    
    def displayReset(self):
        self.emit("displayResetChanged")
        if self.image_proxy is None:
          return
        try:
            self.image_proxy.erase_curves()
        except Exception, e:
            logging.exception(e)

    def showMessage(self,pLevel,pMessage, notify=0):
        if pLevel == 0:
            logging.info(pMessage)
        elif pLevel == 1:
            logging.warning(pMessage)
        elif pLevel == 2:
            logging.error(pMessage)

        self._collectRobotDialog.addHistory(pLevel, pMessage) 
        if notify: 
             self.messageDialog(pLevel,pMessage)

    def messageDialog(self, pType, pMessage):
        if pType == 0:
            Qt.QMessageBox.information(self.brick_widget, "Info", pMessage)
        else:
            Qt.QMessageBox.critical(self.brick_widget, "Error", pMessage)

    def abortPushButtonClicked(self):

        if self.robotCheckBox.isChecked():
            answer = Qt.QMessageBox.question(self.brick_widget, "Info", "Do you want to abort the ongoing data collection?", Qt.QMessageBox.Yes, Qt.QMessageBox.No, Qt.QMessageBox.NoButton)
            if answer == Qt.QMessageBox.No:
                 return
                
        logging.getLogger().info("Aborting!")
        logging.getLogger().warning("Wait for current action to finish...")

        self._abortFlag = True                

        if self.__isTesting:
            self.getObject("collect").testCollectAbort()
        else:
            self.getObject("collect").collectAbort()

        if self.robotCheckBox.isChecked():
           self._collectRobot.abort()

        #
        # Stop all timers 
        #
        if self.SPECBusyTimer.isActive():
            self.SPECBusyTimerTimeOut()

        for timer in self._curveList:
           timer.stop()

        self.setCollectionStatus("aborting")
        self._curveList = []

        answer = Qt.QMessageBox.question(self.brick_widget, "Info", "Please wait for current action to finish", Qt.QMessageBox.Yes, Qt.QMessageBox.No, Qt.QMessageBox.NoButton)
                
    def setWidgetState(self):

        enabled = self.__expertMode and not self.readOnlyCheckBox.isChecked()

        self.maskLineEdit.setEnabled                   (enabled)
        self.maskDirectoryPushButton.setEnabled        (enabled)
        self.maskDisplayPushButton.setEnabled          (enabled and self.__validParameters[2])        
        self.detectorDistanceDoubleSpinBox.setEnabled  (enabled)
        self.waveLengthDoubleSpinBox.setEnabled        (enabled)
        self.pixelSizeXDoubleSpinBox.setEnabled        (enabled)
        self.pixelSizeYDoubleSpinBox.setEnabled        (enabled)
        self.beamCenterXSpinBox.setEnabled             (enabled)
        self.beamCenterYSpinBox.setEnabled             (enabled)
        self.normalisationDoubleSpinBox.setEnabled     (enabled)

    def setButtonState(self, pOption):
        if pOption == 0:     # normal            
            self.processCheckBox.setEnabled   (True)
            self.notifyCheckBox.setEnabled    (True)
            self.robotCheckBox.setEnabled     (True)
            self.hdfCheckBox.setEnabled       (True)
            self.testPushButton.setEnabled    (True)
            self.collectPushButton.setEnabled (True)
            self.abortPushButton.setEnabled   (False)
        elif pOption == 1:   # collecting
            self.processCheckBox.setEnabled   (False)
            self.notifyCheckBox.setEnabled    (False)
            self.robotCheckBox.setEnabled     (False)
            self.hdfCheckBox.setEnabled       (False)                        
            self.testPushButton.setEnabled    (False)
            self.collectPushButton.setEnabled (False)
            self.abortPushButton.setEnabled   (True)
        elif pOption == 2:   # invalid parameters 
            self.processCheckBox.setEnabled   (True)
            self.notifyCheckBox.setEnabled    (True)
            self.robotCheckBox.setEnabled     (True)
            self.hdfCheckBox.setEnabled       (True)            
            self.testPushButton.setEnabled    (False)
            self.collectPushButton.setEnabled (False)
            self.abortPushButton.setEnabled   (False)        

        if self.abortPushButton.isEnabled():
            self.abortPushButton.setProperty("abortactive","true")
        else:            
            self.abortPushButton.setProperty("abortactive","false")

        self.brick_widget.setStyleSheet(self.brick_widget.styleSheet())

    def SPECBusyTimerTimeOut(self):
        #
        # this should be done otherwise.  Checking the status of the spec ready channel
        #
        self.SPECBusyTimer.stop()
        self.setCollectionStatus("done")

        self._feedBackFlag = False
        self.__isTesting = False
        self.setButtonState(0)

        if not self._abortFlag and self._currentFrame < self._frameNumber:
            logging.getLogger().warning("The frame was not collected or didn't appear on time! (%d,%d)" % (self._currentFrame,self._frameNumber))     

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

if __name__ == '__main__':
   print "nada"

