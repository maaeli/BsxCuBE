import os, logging, pprint, time

from Framework4.GUI      import Core
from Framework4.GUI.Core import Property, Connection, Signal, Slot

from CollectRobotDialog  import CollectRobotDialog
#from CollectRobotObject  import CollectRobotObject

from PyQt4               import QtCore, QtGui, Qt
from LeadingZeroSpinBox  import LeadingZeroSpinBox

from Samples             import CollectPars

# TODO : DEBUG
from XSDataCommon import XSDataString, XSDataImage, XSDataBoolean, \
        XSDataInteger, XSDataDouble, XSDataFile, XSDataStatus, \
        XSDataLength, XSDataWavelength, XSDataDouble, XSDataTime
from XSDataBioSaxsv1_0 import XSDataInputBioSaxsProcessOneFilev1_0, \
        XSDataResultBioSaxsProcessOneFilev1_0, XSDataBioSaxsSample, \
        XSDataBioSaxsExperimentSetup, XSDataInputBioSaxsSmartMergev1_0, XSDataResultBioSaxsSmartMergev1_0
from XSDataSAS import XSDataInputSolutionScattering
import PyTango
import threading
import numpy


__category__ = "BsxCuBE"

# Compare outside class
def cmpSEUtemp(a, b):
    return cmp(a["SEUtemperature"], b["SEUtemperature"])
def cmpCode(a, b):
    return cmp(a["code"], b["code"])
def cmpCodeAndSEU(a, b):
    if a["code"] == b["code"]:
        return cmpSEUtemp(a, b)
    else:
        return cmpCode(a, b)

class CollectBrick(Core.BaseBrick):
    properties = {"expertModeOnly": Property("boolean", "Expert mode only", "", "expertModeOnlyChanged", False)}

    connections = {"collect": Connection("Collect object",
                                            [Signal("collectDirectoryChanged", "collectDirectoryChanged"),
                                             Signal("collectPrefixChanged", "collectPrefixChanged"),
                                             Signal("collectRunNumberChanged", "collectRunNumberChanged"),
                                             Signal("collectNumberFramesChanged", "collectNumberFramesChanged"),
                                             Signal("collectTimePerFrameChanged", "collectTimePerFrameChanged"),
                                             Signal("collectConcentrationChanged", "collectConcentrationChanged"),
                                             Signal("collectCommentsChanged", "collectCommentsChanged"),
                                             Signal("collectCodeChanged", "collectCodeChanged"),
                                             Signal("collectMaskFileChanged", "collectMaskFileChanged"),
                                             Signal("collectDetectorDistanceChanged", "collectDetectorDistanceChanged"),
                                             Signal("collectWaveLengthChanged", "collectWaveLengthChanged"),
                                             Signal("collectPixelSizeXChanged", "collectPixelSizeXChanged"),
                                             Signal("collectPixelSizeYChanged", "collectPixelSizeYChanged"),
                                             Signal("collectBeamCenterXChanged", "collectBeamCenterXChanged"),
                                             Signal("collectBeamCenterYChanged", "collectBeamCenterYChanged"),
                                             Signal("collectNormalisationChanged", "collectNormalisationChanged"),
                                             Signal("collectProcessDataChanged", "collectProcessDataChanged"),
                                             Signal("collectNewFrameChanged", "collectNewFrameChanged"),
                                             Signal("checkBeamChanged", "checkBeamChanged"),
                                             Signal("beamLostChanged", "beamLostChanged"),
                                             Signal("collectProcessingDone", "collectProcessingDone"),
                                             Signal("collectProcessingLog", "collectProcessingLog"),
                                             Signal("collectDone", "collectDone"),
                                             Signal("specCollectDone", "specCollectDone"),
                                             Signal("sendProcessParams", "sendProcessParams"),
                                             Signal("sendBeamStopDiodeAndCurrent", "sendBeamStopDiodeAndCurrent") ],
                                            [Slot("testCollect"),
                                             Slot("collect"),
                                             Slot("collectAbort"),
                                             Slot("triggerEDNA")],
                                            "collectObjectConnected"),
                    "motoralignment": Connection("MotorAlignment object",
                                            [Signal("executeTestCollect", "executeTestCollect")],
                                            []),
                    "energy": Connection("Energy object",
                                            [Signal("energyChanged", "energyChanged")],
                                            [Slot("setEnergy"), Slot("getEnergy"), Slot("pilatusReady")],
                                            "connectedToEnergy"),
                    "samplechanger": Connection("Sample Changer object",
                                            [Signal('seuTemperatureChanged', 'seu_temperature_changed'),
                                             Signal('storageTemperatureChanged', 'storage_temperature_changed'),
                                             Signal('stateChanged', 'state_changed'), ],
                                            [],
                                            "sample_changer_connected"),
                    "image_proxy": Connection("image proxy",
                                            [Signal('new_curves_data', 'y_curves_data'), Signal('erase_curve', 'erase_curve')],
                                            [],
                                            "image_proxy_connected"),
                    "login": Connection("Login object",
                                            [Signal("loggedIn", "loggedIn")],
                                            [],
                                            "connectionToLogin")}



    signals = [Signal("displayResetChanged"),
               Signal("displayItemChanged"),
               Signal("transmissionChanged")]
    slots = []

    def __init__(self, *args, **kargs):
        Core.BaseBrick.__init__(self, *args, **kargs)
        self._curveList = []
        self.lastCollectProcessingLog = None


    def init(self):
        # The keV to Angstrom calc
        self.hcOverE = 12.3984
        self.nbPlates = 0
        self.platesIDs = []
        self.plateInfos = []
        self._frameNumber = 0
        self._feedBackFlag = False
        self._abortFlag = False
        self._currentFrame = 0
        self._currentCurve = 0
        self._waveLengthStr = "0.0"
        self._collectRobotDialog = CollectRobotDialog(self)
        self.__lastFrame = None
        self.__currentConcentration = None
        self.__isTesting = False
        self.__expertModeOnly = False
        self.__expertMode = False


        self.__validParameters = [False, False, False]

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

        self.hBoxLayout71 = Qt.QHBoxLayout()
        self.blParamsButton = Qt.QPushButton("Show Beamline Parameters", self.brick_widget)
        self.blParamsButton.setFixedWidth(230)
        self.hBoxLayout71.addWidget(self.blParamsButton)
        self.brick_widget.layout().addLayout(self.hBoxLayout71)
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

        # Radiation Damage 
        self.hBoxLayout15 = Qt.QHBoxLayout()
        self.radiationCheckBox = Qt.QCheckBox("Radiation damage", self.brick_widget)
        self.radiationCheckBox.setFixedWidth(130)
        Qt.QObject.connect(self.radiationCheckBox, Qt.SIGNAL("toggled(bool)"), self.radiationCheckBoxToggled)
        self.hBoxLayout15.addWidget(self.radiationCheckBox)
        self.radiationRelativeDoubleSpinBox = Qt.QDoubleSpinBox(self.brick_widget)
        self.radiationRelativeDoubleSpinBox.setRange(0.0, 1.0)
        self.radiationRelativeDoubleSpinBox.setDecimals(10)
        self.radiationRelativeDoubleSpinBox.setToolTip("Relative Similarity")
        self.hBoxLayout15.addWidget(self.radiationRelativeDoubleSpinBox)
        self.radiationAbsoluteDoubleSpinBox = Qt.QDoubleSpinBox(self.brick_widget)
        self.radiationAbsoluteDoubleSpinBox.setRange(0.0, 1.0)
        self.radiationAbsoluteDoubleSpinBox.setDecimals(10)
        self.radiationAbsoluteDoubleSpinBox.setToolTip("Absolute Similarity")
        self.hBoxLayout15.addWidget(self.radiationAbsoluteDoubleSpinBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout15)

        # Spectro Online
        #TODO: MOVE to Collect box
#        self.hBoxLayout151 = Qt.QHBoxLayout()
#        self.spectroCheckBox = Qt.QCheckBox("Spectro online", self.brick_widget)
#        self.spectroCheckBox.setFixedWidth(130)
#        Qt.QObject.connect(self.spectroCheckBox, Qt.SIGNAL("toggled(bool)"), self.spectroCheckBoxToggled)
#        self.hBoxLayout151.addWidget(self.spectroCheckBox)
#        self.extinctionCoefficentDoubleSpinBox = Qt.QDoubleSpinBox(self.brick_widget)
#        self.extinctionCoefficentDoubleSpinBox.setRange(0.001, 99.998)
#        self.extinctionCoefficentDoubleSpinBox.setDecimals(3)
#        #TODO: - Change by reading from SPEC/File
#        self.extinctionCoefficentDoubleSpinBox.setValue(1.000)
#        self.extinctionCoefficentDoubleSpinBox.setSuffix(" (ml)*(1/mg)*(1/cm)")
#        self.extinctionCoefficentDoubleSpinBox.setToolTip("Extinction Coefficient")
#        self.hBoxLayout151.addWidget(self.extinctionCoefficentDoubleSpinBox)
#        self.brick_widget.layout().addLayout(self.hBoxLayout151)


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
        self.checkBeamBox = Qt.QCheckBox("Check beam", self.brick_widget)
        self.checkBeamBox.setChecked(True)
        Qt.QObject.connect(self.checkBeamBox, Qt.SIGNAL("toggled(bool)"), self.checkBeamBoxToggled)
        self.hBoxLayout17.addWidget(self.checkBeamBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout17)

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
        self.collectStatus = Qt.QLabel("")
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
        self.radiationCheckBoxToggled(False)
        # TODO : DEBUG
#        self.spectroCheckBoxToggled(False)
        self.dat_filenames = {}
        self.strTangoDevice1 = "DAU/edna/1"
        self.ednaDeviceProxy1 = PyTango.DeviceProxy(self.strTangoDevice1)
        self.ednaTangoCallbackThread = EdnaTangoCallbackThread(self.strTangoDevice1, self.ednaTangoSuccess1)
        self.ednaTangoCallbackThread.start()
        self.pluginIntegrate = "EDPluginBioSaxsProcessOneFilev1_1"
        self.pluginMerge = "EDPluginBioSaxsSmartMergev1_3"
        self.pluginSAS = "EDPluginControlSolutionScatteringv0_3"
        self.xsdin = None
        self.beamStopDiode = None
        self.machineCurrent = None
        self.xsdAverage = None
        self.seuTemperature = None
        self.storageTemperature = None


        self.SPECBusyTimer = Qt.QTimer(self.brick_widget)
        Qt.QObject.connect(self.SPECBusyTimer, Qt.SIGNAL("timeout()"), self.SPECBusyTimerTimeOut)

        self._sampleChangerDisplayFlag = False
        self._sampleChangerDisplayMessage = ""

        self.setWidgetState()
        self.setButtonState(0)

    # When connected to Login, then block the brick
    def connectionToLogin(self, pPeer):
        if pPeer is not None:
            self.brick_widget.setEnabled(False)


    # Logged In : True or False 
    def loggedIn(self, pValue):
        self.brick_widget.setEnabled(pValue)

    def sample_changer_connected(self, pPeer):
        if pPeer is not None:
            self.scObject = pPeer
            self.nbPlates = 3
            self.plateInfos = [self.scObject.getPlateInfo(i) for i in range(1, self.nbPlates + 1)]
            print "sample changer connected in CollectBrick>>>> %r" % self.plateInfos

    def seu_temperature_changed(self, seuTemperature):
        self.seuTemperature = seuTemperature

    def storage_temperature_changed(self, storageTemperature):
        self.storageTemperature = storageTemperature

    def state_changed(self, state, status):
        # not used, so we do not care
        pass

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
        self._waveLengthStr = pValue

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

    def collectProcessingDone(self, dat_filename):
        logging.info("processing done, file is %r", dat_filename)
        self.emitDisplayItemChanged(dat_filename)

    def collectProcessingLog(self, level, logmsg, notify):
        # Level 0 = info, Level 1 = 
        if level == 0:
            logmethod = logging.info
        elif level == 2:
            logmethod = logging.error

        if logmsg != self.lastCollectProcessingLog:
            for line in logmsg.split(os.linesep):
                logmethod(line.rstrip())

        self.lastCollectProcessingLog = logmsg
        self._collectRobotDialog.addHistory(level, logmsg)

        if notify:
            self.messageDialog(level, logmsg)

    def collectNewFrameChanged(self, pValue):
        # TODO: DEBUG
        #logging.getLogger().info("In collectNewFrameChanged, pValue = %r" % pValue)
        filename0 = pValue.split(",")[0]
        #if os.path.dirname(filename0)[-4:] == "/raw":
        if os.path.dirname(filename0).endswith("/raw"):
            directory = os.path.join(os.path.dirname(filename0)[:-4], "1d")
        else:
            directory = os.path.join(os.path.dirname(filename0), "1d")

        if self.__lastFrame is None or self.__lastFrame != pValue:
            self.__lastFrame = pValue
            if self._isCollecting:
                # TODO: DEBUG
                logging.getLogger().info("Is collecting")
                #self.getObject("collect").triggerEDNA(filename0, oneway = True)
                #self.collectObj.triggerEDNA(filename0, oneway = True)
                self.localTriggerEDNA(filename0)
                message = "The frame '%s' was collected..." % filename0
                logging.getLogger().info(message)
                if self.robotCheckBox.isChecked():
                    self._collectRobotDialog.addHistory(0, message)

                self._currentFrame += 1

                self.setCollectionStatus(status = "running", progress = [ self._currentFrame, self._frameNumber ])

                if not self.__isTesting:
                    if self._currentFrame == self._frameNumber:
                        splitList = os.path.basename(filename0).split("_")
                        # Take away last _ piece
                        filename1 = "_".join(splitList[:-1])
                        ave_filename = directory + filename1 + "_ave.dat"
                self.emitDisplayItemChanged(filename0)
            else:
                if os.path.exists(filename0):
                    #if filename0.split(".")[-1] != "dat":
                    if os.path.splitext(filename0)[1] != ".dat":
                        #filename1 = directory + os.path.basename(filename0).split(".")[0] + ".dat"
                        fileBaseName = os.path.splitext(os.path.basename(filename0))[0]
                        filename1 = os.path.join(directory, fileBaseName + ".dat")
                        if os.path.exists(filename1):
                            filename0 += "," + filename1
                    # TODO: DEBUG
                    logging.getLogger().info("emitDisplayItemChanged: %r" % filename0)
                    self.emitDisplayItemChanged(filename0)

#           TODO: This is how put in a breakpoint 
#           import pdb; pdb.set_trace()
            if self._currentFrame == self._frameNumber:
                # data collection done = Last frame
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
                            logging.getLogger().info("The data collection is done!")
                        else:
                            if self.SPECBusyTimer.isActive():
                                self.SPECBusyTimerTimeOut()
                        if feedBackFlag:
                            if self.notifyCheckBox.isChecked():
                                Qt.QMessageBox.information(self.brick_widget, "Info", "\n                       The data collection is done!                                       \n")

    # TODO: DEBUG
    def sendProcessParams(self, processParamsXml):
        #logging.info("In sendProcessParams")
        self.xsdin = XSDataInputBioSaxsProcessOneFilev1_0().parseString(processParamsXml)

    # TODO: DEBUG
    def sendBeamStopDiodeAndCurrent(self, beamStopDiodeAndCurrent):
        #logging.info("In sendBeamStopDiodeAndCurrent: %r" % beamStopDiodeAndCurrent)
        self.beamStopDiode = beamStopDiodeAndCurrent[0]
        self.machineCurrent = beamStopDiodeAndCurrent[1]

    # TODO: DEBUG
    def ednaTangoSuccess1(self, event):
        if event.attr_value is not None:
            jobId = event.attr_value.value
            if jobId in self.dat_filenames:
                filename = self.dat_filenames.pop(jobId)
                logging.info("Processing Done from EDNA: %s -> %s", jobId, filename)
                self.collectProcessingDone(filename)
                if jobId.startswith(self.pluginMerge):
                    strXsdout = self.ednaDeviceProxy1.getJobOutput(jobId)
                    try:
                        xsd = XSDataResultBioSaxsSmartMergev1_0.parseString(strXsdout)
                    except:
                        logging.error("Unable to parse string from Tango/EDNA")
                    else:
                        log = xsd.status.executiveSummary.value
                        logging.info(log)
                        # If autoRG has been used, launch the SAS pipeline (very time consuming)
                        if xsd.autoRg is None:
                            logging.info("SAS pipeline not executed")
                        else:
                            rgOut = xsd.autoRg
                            filename = rgOut.filename.path.value
                            logging.info("filename as input for SAS %s", filename)
                            datapoint = numpy.loadtxt(filename)
                            startPoint = rgOut.firstPointUsed.value
                            q = datapoint[:, 0][startPoint:]
                            I = datapoint[:, 1][startPoint:]
                            s = datapoint[:, 2][startPoint:]
                            mask = (q < 3)
                            xsdin = XSDataInputSolutionScattering(title = XSDataString(os.path.basename(filename)))
                            #NbThreads=XSDataInteger(4))
                            xsdin.experimentalDataQ = [ XSDataDouble(i / 10.0) for i in q[mask]] #pipeline expect A-1 not nm-1
                            xsdin.experimentalDataValues = [ XSDataDouble(i) for i in I[mask]]
                            xsdin.experimentalDataStdDev = [ XSDataDouble(i) for i in s[mask]]
                            logging.info("Starting SAS pipeline for file %s", filename)
                            sasJobId = self.ednaDeviceProxy1.startJob([self.pluginSAS, xsdin.marshal()])
                            # self.dat_filenames[sasJobId] = filename
#            else:
#                logging.warning("processing Done from EDNA: %s -X-> None", jobId)

    # TODO: DEBUG
    def localTriggerEDNA(self, raw_filename):
        """This is a local version of Collect.triggerEdna as a workaround for the Framework 4 communication problem"""
        logging.info("Prepare EDNA input")
        pars = self.getCollectPars(1)
        if self.xsdin != None:
            xsdin = self.xsdin.copy()
            if self.storageTemperature is None:
                logging.warning("No storage temperature reading, using default value 20")
                storageTemperature = 20.0
            else:
                storageTemperature = self.storageTemperature
            if self.exposureTemperature is None:
                logging.warning("No exposure temperature reading, using default value 20")
                storageTemperature = 20.0
            else:
                exposureTemperature = self.seuTemperature
            if self.beamStopDiode is None:
                logging.warning("No beamstop diode reading, using default value 0.0001")
                collectBeamStopDiode = 0.0001
            else:
                collectBeamStopDiode = self.beamStopDiode
            if self.machineCurrent is None:
                logging.warning("No machine current reading, using default value 200.0")
                machineCurrent = 200.0
            else:
                machineCurrent = self.machineCurrent

            logging.info("Local trigger EDNA with filename %s", raw_filename)
            raw_filename = str(raw_filename)
            tmp, suffix = os.path.splitext(raw_filename)
            tmp, base = os.path.split(tmp)
            directory, local = os.path.split(tmp)
            frame = ""
            for c in base[-1::-1]:
                if c.isdigit():
                    frame = c + frame
                else:
                    break

            xsdin.experimentSetup.storageTemperature = XSDataDouble(storageTemperature)
            xsdin.experimentSetup.exposureTemperature = XSDataDouble(exposureTemperature)
            xsdin.experimentSetup.frameNumber = XSDataInteger(int(frame))
            #xsdin.experimentSetup.beamStopDiode = XSDataDouble(float(self.channels["collectBeamStopDiode"].value()))
            xsdin.experimentSetup.beamStopDiode = XSDataDouble(float(collectBeamStopDiode))
            # self.machineCurrent is already float
            xsdin.experimentSetup.machineCurrent = XSDataDouble(machineCurrent)

            xsdin.rawImage = XSDataImage(path = XSDataString(raw_filename))
            xsdin.logFile = XSDataFile(path = XSDataString(os.path.join(directory, "misc", base + ".log")))
            xsdin.normalizedImage = XSDataImage(path = XSDataString(os.path.join(directory, "2d", base + ".edf")))
            xsdin.integratedImage = XSDataImage(path = XSDataString(os.path.join(directory, "misc", base + ".ang")))
            xsdin.integratedCurve = XSDataFile(path = XSDataString(os.path.join(directory, "1d", base + ".dat")))
            # TODO : DEBUG
    #        jobId = self.commands["startJob_sparta"]([self.pluginIntegrate, xsdin.marshal()])
            jobId = self.ednaDeviceProxy1.startJob([self.pluginIntegrate, xsdin.marshal()])
            self.dat_filenames[jobId] = xsdin.integratedCurve.path.value
            logging.info("Processing job %s started", jobId)
            #For debugging
            xmlFilename = os.path.splitext(raw_filename)[0] + ".xml"
            logging.info("Saving XML data to %s", xmlFilename)
            xsdin.exportToFile(xmlFilename)
            # Prepare input to SaxsSmartAverage
#            sPrefix = pars["prefix"]
#            pRunNumber = pars["runNumber"]
#            pNumberFrames = pars["frameNumber"]
#            pRadiationChecked = pars["radiationChecked"]
#            pRadiationAbsolute = pars["radiationAbsolute"]
#            pRadiationRelative = pars["radiationRelative"]
#            ave_filename = os.path.join(directory, "1d", "%s_%03d_ave.dat" % (sPrefix, pRunNumber))
#            sub_filename = os.path.join(directory, "ednaSub", "%s_%03d_sub.dat" % (sPrefix, pRunNumber))
#            self.xsdAverage = XSDataInputBioSaxsSmartMergev1_0(\
#                                    inputCurves = [XSDataFile(path = XSDataString(os.path.join(directory, "1d", "%s_%03d_%02d.dat" % (sPrefix, pRunNumber, i)))) for i in range(1, pNumberFrames + 1)],
#                                    mergedCurve = XSDataFile(path = XSDataString(ave_filename)),
#                                    subtractedCurve = XSDataFile(path = XSDataString(sub_filename)))
#            if pRadiationChecked:
#                self.xsdAverage.absoluteFidelity = XSDataDouble(float(pRadiationAbsolute))
#                self.xsdAverage.relativeFidelity = XSDataDouble(float(pRadiationRelative))


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
            self.setCollectionStatus("busy", progress = None)
        else:
            self.setCollectionStatus("ready", progress = None)

    def expertModeOnlyChanged(self, pValue):
        self.__expertModeOnly = pValue
        self.expert_mode(self.__expertMode)

    def expert_mode(self, expert):
        self.__expertMode = expert
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
            logging.error("Could not read file " + str(pValue))
            logging.exception(e)

    def y_curves_data(self, pPeer):
        pass

    def erase_curve(self, pPeer):
        pass



    def collectObjectConnected(self, collect_obj):
        if collect_obj is not None:
            self.collectObj = collect_obj
            self.collectObj.updateChannels(oneway = True)


    def connectedToEnergy(self, pPeer):
        if pPeer is not None:
            self.energyControlObject = pPeer
            # read energy when getting contact with CO Object
            self.__energy = float(self.energyControlObject.getEnergy())
            wavelength = self.hcOverE / self.__energy
            wavelengthStr = "%.4f" % wavelength
            self._waveLengthStr = wavelengthStr

    def energyChanged(self, pValue):
        if pValue is not None:
            self.__energy = float(pValue)
            wavelength = self.hcOverE / self.__energy
            wavelengthStr = "%.4f" % wavelength
            self._waveLengthStr = wavelengthStr


    def validParameters(self):

        # This routine checks:
        #   - that there is at least one sample defined and active
        #   - that there are not two buffers with same name
        #   - that the buffer assigned to a sample is existing
        #

        pars = self.getCollectPars(robot = 1)
        valid = True

        if len(pars["sampleList"]) == 0:
            valid = False
            Qt.QMessageBox.information(self.brick_widget, "Warning", "No sample to collect in robot!")
        else:
            buffernames = []

            for myBuffer in pars["bufferList"]:
                # NOW myBuffers of same name are allowed.  But we should do something about it during collect

                if myBuffer not in buffernames:
                    buffernames.append(myBuffer["buffername"])

            for sample in pars["sampleList"]:
                if sample["buffername"] not in buffernames:
                    Qt.QMessageBox.information(self.brick_widget, "Warning", "Sample with no buffer assignment or buffer name does not exist")
                    valid = False
                    break

        return valid

    def getFileInfo(self):
        generalParsWidget = self
        filepars = CollectPars()
        filepars.prefix = generalParsWidget.prefixLineEdit.text()
        filepars.runNumber = generalParsWidget.runNumberSpinBox.value()
        filepars.frameNumber = generalParsWidget.frameNumberSpinBox.value()
        return filepars

    def getCollectPars(self, robot = 1):
        if robot:
            # return a dictionary
            collectpars = { "directory": str(self.directoryLineEdit.text()),
                            "prefix": str(self.prefixLineEdit.text()),
                            "runNumber": int(self.runNumberSpinBox.value()),
                            "frameNumber": int(self.frameNumberSpinBox.value()),
                            "timePerFrame": int(self.timePerFrameSpinBox.value()),
                            "currentConcentration": float(self.concentrationDoubleSpinBox.value()),
                            "currentComments":str(self.commentsLineEdit.text()),
                            "currentCode": str(self.codeLineEdit.text()),
                            "doProcess":self.processCheckBox.isChecked(),
                            "mask":str(self.maskLineEdit.text()),
                            "detectorDistance": float(self.detectorDistanceDoubleSpinBox.value()),
                            "waveLength": float(self._waveLengthStr),
                            "pixelSizeX":float(self.pixelSizeXDoubleSpinBox.value()),
                            "pixelSizeY":float(self.pixelSizeYDoubleSpinBox.value()),
                            "beamCenterX": int(self.beamCenterXSpinBox.value()),
                            "beamCenterY": int(self.beamCenterYSpinBox.value()),
                            "normalisation": float(self.normalisationDoubleSpinBox.value()),
                            "radiationChecked":self.radiationCheckBox.isChecked(),
                            "radiationRelative": float(self.radiationRelativeDoubleSpinBox.value()),
                            "radiationAbsolute": float(self.radiationAbsoluteDoubleSpinBox.value()),
                            "SEUTemperature": self._sampleChanger.getSEUTemperature(),
                            "storageTemperature": self._sampleChanger.getSampleStorageTemperature() }

            robotpars = { "sampleType": str(self._collectRobotDialog.sampleTypeComboBox.currentText()),
                          "storageTemperature": float(self._collectRobotDialog.storageTemperatureDoubleSpinBox.value()),
                          "extraFlowTime": int(self._collectRobotDialog.extraFlowTimeSpinBox.value()),
                          "optimization": str(self._collectRobotDialog.optimizationComboBox.currentIndex()),
                          "optimizationText": str(self._collectRobotDialog.optimizationComboBox.currentText()),
                          "initialCleaning": self._collectRobotDialog.initialCleaningCheckBox.isChecked(),
                          "bufferMode": str(self._collectRobotDialog.bufferModeComboBox.currentIndex()),
                          "bufferFirst": False,
                          "bufferBefore": False,
                          "bufferAfter": False }

            filepars = { "runNumber": self.runNumberSpinBox.value(),
                         "frameNumber": self.frameNumberSpinBox.value() }
            collectpars.update(filepars)

            if robotpars["bufferMode"] == '0':
                robotpars.update({ "bufferFirst":True, "bufferAfter": True })
            elif robotpars["bufferMode"] == '1':
                robotpars["bufferBefore"] = True
            elif robotpars["bufferMode"] == '2':
                robotpars["bufferAfter"] = True

            robotpars["optimSEUtemp"] = False
            robotpars["optimCodeAndSEU"] = False
            if robotpars["optimization"] == 1:
                robotpars["optimSEUtemp"] = True
            elif robotpars["optimization"] == 2:
                robotpars["optimCodeAndSEU"] = True

            bufferList = []
            sampleList = []
            robotpars.update({ "bufferList": bufferList, "sampleList": sampleList })
            for i in range(0, self._collectRobotDialog.tableWidget.rowCount()):
                sample = self._collectRobotDialog.getSampleRow(i)

                if sample.enable:
                    if sample.isBuffer():
                        bufferList.append(sample.__dict__)
                    else:
                        sampleList.append(sample.__dict__)

            for sample in sampleList:
                sample["buffer"] = []
                if len(bufferList) == 1:   # if there is one and only one buffer defined dont look at name. assign
                    sample["buffer"].append(bufferList[0])
                else:
                    for bufferEntry in bufferList:
                        if buffer["buffername"] == sample["buffername"]:
                            sample["buffer"].append(bufferEntry)

            if robotpars["optimSEUtemp"]:
                sampleList.sort(cmpSEUtemp)
            elif robotpars["optimCodeAndSEU"]:
                sampleList.sort(cmpCodeAndSEU)

            collectpars.update(robotpars)

            collectpars["flowTime"] = collectpars["timePerFrame"] * collectpars["frameNumber"] + collectpars["extraFlowTime"]
            collectpars["processData"] = 1 if collectpars["doProcess"] else 0

            logging.info("sample type is %s" , collectpars["sampleType"])
            logging.info("number of samples is %s" , len(collectpars["sampleList"]))
        else:
            collectpars = CollectPars()

            logging.info("   - reading collection parameters")
            #
            #  I should actually separate values so that each widget represents a certain data in a clear way
            #
            collectpars.directory = self.directoryLineEdit.text()
            collectpars.prefix = self.prefixLineEdit.text()
            collectpars.runNumber = self.runNumberSpinBox.value()
            collectpars.frameNumber = self.frameNumberSpinBox.value()
            collectpars.timePerFrame = self.timePerFrameSpinBox.value()
            collectpars.currentConcentration = self.concentrationDoubleSpinBox.value()
            collectpars.currentComments = self.commentsLineEdit.text()
            collectpars.currentCode = self.codeLineEdit.text()

            collectpars.doProcess = self.processCheckBox.isChecked()

            collectpars.mask = self.maskLineEdit.text()
            collectpars.detectorDistance = self.detectorDistanceDoubleSpinBox.value()
            collectpars.waveLength = self._waveLengthStr
            collectpars.pixelSizeX = self.pixelSizeXDoubleSpinBox.value()
            collectpars.pixelSizeY = self.pixelSizeYDoubleSpinBox.value()
            collectpars.beamCenterX = self.beamCenterXSpinBox.value()
            collectpars.beamCenterY = self.beamCenterYSpinBox.value()
            collectpars.normalisation = self.normalisationDoubleSpinBox.value()
            collectpars.radiationChecked = self.radiationCheckBox.isChecked()
            collectpars.radiationRelative = self.radiationRelativeDoubleSpinBox.value()
            collectpars.radiationAbsolute = self.radiationAbsoluteDoubleSpinBox.value()
            collectpars.SEUTemperature = self._sampleChanger.getSEUTemperature()
            collectpars.storageTemperature = self._sampleChanger.getSampleStorageTemperature()


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

    #def delete(self):
    #    self._collectRobot.terminate()

    def showHideBeamlineParams(self, pValue = None):

        if self.showingBLParams:
            self.showingBLParams = 0
            self.blParamsButton.setText("Show Beamline Parameters")
            self.maskLineEdit.hide()
            self.maskDirectoryPushButton.hide()
            self.maskDisplayPushButton.hide()
            self.detectorDistanceDoubleSpinBox.hide()
            self.pixelSizeXDoubleSpinBox.hide()
            self.pixelSizeYDoubleSpinBox.hide()
            self.beamCenterXSpinBox.hide()
            self.beamCenterYSpinBox.hide()
            self.normalisationDoubleSpinBox.hide()
            self.maskLabel.hide()
            self.detectorDistanceLabel.hide()
            self.pixelSizeLabel.hide()
            self.beamCenterLabel.hide()
            self.normalisationLabel.hide()
        else:
            self.blParamsButton.setText("Hide Beamline Parameters")
            self.showingBLParams = 1
            self.maskLineEdit.show()
            self.maskDirectoryPushButton.show()
            self.maskDisplayPushButton.show()
            self.detectorDistanceDoubleSpinBox.show()
            self.pixelSizeXDoubleSpinBox.show()
            self.pixelSizeYDoubleSpinBox.show()
            self.beamCenterXSpinBox.show()
            self.beamCenterYSpinBox.show()
            self.normalisationDoubleSpinBox.show()
            self.maskLabel.show()
            self.detectorDistanceLabel.show()
            self.pixelSizeLabel.show()
            self.beamCenterLabel.show()
            self.normalisationLabel.show()

    def readOnlyCheckBoxToggled(self, pValue):

        self.directoryLineEdit.setEnabled(not pValue)
        self.directoryPushButton.setEnabled(not pValue)
        self.prefixLineEdit.setEnabled(not pValue)
        self.runNumberSpinBox.setEnabled(not pValue)
        self.frameNumberSpinBox.setEnabled(not pValue)
        self.timePerFrameSpinBox.setEnabled(not pValue)
        self.maskLineEdit.setEnabled(not pValue and (not self.__expertModeOnly or self.__expertMode))
        self.maskDirectoryPushButton.setEnabled(not pValue and (not self.__expertModeOnly or self.__expertMode))
        self.maskDisplayPushButton.setEnabled(not pValue and (not self.__expertModeOnly or self.__expertMode))
        self.detectorDistanceDoubleSpinBox.setEnabled(not pValue and (not self.__expertModeOnly or self.__expertMode))
        self.pixelSizeXDoubleSpinBox.setEnabled(not pValue and (not self.__expertModeOnly or self.__expertMode))
        self.pixelSizeYDoubleSpinBox.setEnabled(not pValue and (not self.__expertModeOnly or self.__expertMode))
        self.beamCenterXSpinBox.setEnabled(not pValue and (not self.__expertModeOnly or self.__expertMode))
        self.beamCenterYSpinBox.setEnabled(not pValue and (not self.__expertModeOnly or self.__expertMode))
        self.normalisationDoubleSpinBox.setEnabled(not pValue and (not self.__expertModeOnly or self.__expertMode))
        self.radiationCheckBox.setEnabled(not pValue)
        self.radiationRelativeDoubleSpinBox.setEnabled(not pValue and self.radiationCheckBox.isChecked())
        self.radiationAbsoluteDoubleSpinBox.setEnabled(not pValue and self.radiationCheckBox.isChecked())

    def directoryLineEditChanged(self, pValue):
        if self._isCollecting:
            return

        self.__validParameters[0] = pValue is not None and os.path.exists(pValue) and not os.path.isfile(pValue)

        if self.__validParameters[0]:
            self.directoryLineEdit.setProperty("valid", "true")
        else:
            self.directoryLineEdit.setProperty("valid", "false")

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
            self.prefixLineEdit.setProperty("valid", "true")
        else:
            self.prefixLineEdit.setProperty("valid", "false")

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
            self.maskLineEdit.setProperty("valid", "true")
        elif flag == 1:
            self.__validParameters[2] = True
            self.maskLineEdit.setProperty("valid", "true")
        else:
            self.__validParameters[2] = False
            self.maskLineEdit.setProperty("valid", "false")

        self.maskDisplayPushButton.setEnabled(self.__validParameters[2] and (not self.__expertModeOnly or self.__expertMode))
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

    def radiationCheckBoxToggled(self, pValue):
        self.radiationRelativeDoubleSpinBox.setEnabled(pValue)
        self.radiationAbsoluteDoubleSpinBox.setEnabled(pValue)

# TODO: DEBUG
#    def spectroCheckBoxToggled(self, pValue):
#        self.extinctionCoefficentDoubleSpinBox.setEnabled(pValue)

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
        self.collectObj.setCheckBeam(pValue)

    def testPushButtonClicked(self):

        self.setButtonState(1)
        # For test allow 30s
        self.SPECBusyTimer.start(30000)

        self.startCollection(mode = 'test')

        self._feedBackFlag = False
        self._abortFlag = False
        self._frameNumber = 1
        self._currentFrame = 0

        self.getObject("collect").testCollect(str(self.directoryLineEdit.text()),
                                               str(self.prefixLineEdit.text()),
                                               self.runNumberSpinBox.value(),
                                               self.concentrationDoubleSpinBox.value(),
                                               str(self.commentsLineEdit.text()),
                                               str(self.codeLineEdit.text()),
                                               str(self.maskLineEdit.text()),
                                               self.detectorDistanceDoubleSpinBox.value(),
                                               self._waveLengthStr,
                                               self.pixelSizeXDoubleSpinBox.value(),
                                               self.pixelSizeYDoubleSpinBox.value(),
                                               self.beamCenterXSpinBox.value(),
                                               self.beamCenterYSpinBox.value(),
                                               self.normalisationDoubleSpinBox.value())


    def collectPushButtonClicked(self):
        # Check if pilatus is ready
        if not self.energyControlObject.pilatusReady():
            Qt.QMessageBox.critical(self.brick_widget, "Error", "Pilatus detector is busy.. Try later", Qt.QMessageBox.Ok)
            return
        if not self.robotCheckBox.isChecked() or self.validParameters():
            directory = str(self.directoryLineEdit.text()) + "/raw"
            runNumber = "%03d" % self.runNumberSpinBox.value()
            flag = True

            if os.path.isdir(directory):
                for filename in os.listdir(directory):
                    if os.path.isfile(directory + "/" + filename):
                        if filename.startswith(str(self.prefixLineEdit.text()) + "_" + runNumber) and not filename.startswith(str(self.prefixLineEdit.text()) + "_" + runNumber + "_00"):
                            flag = False
                            break

            if not flag:
                flag = (Qt.QMessageBox.question(self.brick_widget, "Warning", "The run '%s' with prefix '%s' already exists in the directory '%s'. Overwrite it?" % (runNumber, self.prefixLineEdit.text(), self.directoryLineEdit.text()), Qt.QMessageBox.Yes, Qt.QMessageBox.No, Qt.QMessageBox.NoButton) == Qt.QMessageBox.Yes)

            if not flag:
                return

            if self.robotCheckBox.isChecked():
                self.startCollectWithRobot()
            else:
                if not (not self.__expertModeOnly or self.__expertMode):

                    if self.__currentConcentration is not None and self.__currentConcentration == self.concentrationDoubleSpinBox.value():
                        flag = (Qt.QMessageBox.question(self.brick_widget, \
                                    "Warning", "The value of the concentration '%s' is the same than the previous collection. Continue?" % \
                                                  self.concentrationDoubleSpinBox.value(), \
                                                  Qt.QMessageBox.Yes, \
                                                  Qt.QMessageBox.No, Qt.QMessageBox.NoButton) == Qt.QMessageBox.Yes)

                if flag:
                    self.startCollectWithoutRobot()

    def setCollectionStatus(self, status, progress = None):
        if status == "running":
            self._isCollecting = True
            self.abortPushButton.setEnabled(True)
            self.abortPushButton.setProperty("abortactive", "true")
        else:
            self._isCollecting = False
            self.abortPushButton.setEnabled(False)
            self.abortPushButton.setProperty("abortactive", "false")

        self.brick_widget.setStyleSheet(self.brick_widget.styleSheet())
        self.collectStatus.setText(status)
        self.collectStatus.setProperty("status", status)

        self.brick_widget.setStyleSheet(self.brick_widget.styleSheet())

    def startCollectWithRobot(self):
        # starts a series of individual collections
        #  blocks widget or whatever during the time of the collection
        self.setButtonState(1)
        self._abortFlag = False
        self.startCollection(mode = "with robot")
        self._collectRobotDialog.clearHistory()
        self.getObject("collect").collectWithRobot(self.getCollectPars(), oneway = True)


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

        self.startCollection(mode = "no robot")

        self.collect(1,
                      str(self.directoryLineEdit.text()),
                      str(self.prefixLineEdit.text()),
                      self.runNumberSpinBox.value(),
                      self.frameNumberSpinBox.value(),
                      self.timePerFrameSpinBox.value(),
                      self.concentrationDoubleSpinBox.value(),
                      str(self.commentsLineEdit.text()),
                      str(self.codeLineEdit.text()),
                      str(self.maskLineEdit.text()),
                      self.detectorDistanceDoubleSpinBox.value(),
                      self._waveLengthStr,
                      self.pixelSizeXDoubleSpinBox.value(),
                      self.pixelSizeYDoubleSpinBox.value(),
                      self.beamCenterXSpinBox.value(),
                      self.beamCenterYSpinBox.value(),
                      self.normalisationDoubleSpinBox.value(),
                      self.radiationCheckBox.isChecked(),
                      self.radiationAbsoluteDoubleSpinBox.value(),
                      self.radiationRelativeDoubleSpinBox.value(),
                      processData,
                      self._sampleChanger.getSEUTemperature(),
                      self._sampleChanger.getSampleStorageTemperature())

        self.__currentConcentration = self.concentrationDoubleSpinBox.value()

    def startCollection(self, mode = "normal"):

        self.setCollectionStatus("running")

        if mode == "test":
            self.__isTesting = True

        logging.info("   - collection started (mode: %s)" % mode)

    def specCollectDone(self, xmlXsdAverage):
        # Start smart averaging
        logging.info("Spec collect done - starting averaging")
        #logging.info(xmlXsdAverage)
        xsdAverage = XSDataInputBioSaxsSmartMergev1_0().parseString(xmlXsdAverage)
        jobId = self.ednaDeviceProxy1.startJob([self.pluginMerge, xmlXsdAverage])
        self.dat_filenames[jobId] = xsdAverage.mergedCurve.path.value


    def collectDone(self):
        self.setCollectionStatus("done")
        self.setButtonState(0)
        if self._feedBackFlag:
            if self.notifyCheckBox.isChecked():
                Qt.QMessageBox.information(self.brick_widget, "Info", "\n                       The data collection is done!                                       \n")


    def collect(self, pFeedBackFlag, pDirectory, pPrefix, pRunNumber, pFrameNumber , pTimePerFrame, pConcentration, pComments, pCode, pMaskFile, pDetectorDistance, pWaveLength, pPixelSizeX, pPixelSizeY, pBeamCenterX, pBeamCenterY, pNormalisation, pRadiationChecked, pRadiationAbsolute, pRadiationRelative, pProcessData, pSEUTemperature, pStorageTemperature):
        if not self.robotCheckBox.isChecked():
            self.SPECBusyTimer.start(pFrameNumber * (pTimePerFrame + 5) * 1000 + 12000)

        self.__isTesting = False
        self._feedBackFlag = (pFeedBackFlag == 1)
        self._frameNumber = pFrameNumber
        self._currentFrame = 0
        self._currentCurve = 0
        self.getObject("collect").collect(str(pDirectory),
                                          str(pPrefix),
                                          pRunNumber,
                                          pFrameNumber,
                                          pTimePerFrame,
                                          pConcentration,
                                          str(pComments),
                                          str(pCode),
                                          str(pMaskFile),
                                          pDetectorDistance,
                                          pWaveLength,
                                          pPixelSizeX,
                                          pPixelSizeY,
                                          pBeamCenterX,
                                          pBeamCenterY,
                                          pNormalisation,
                                          pRadiationChecked,
                                          pRadiationAbsolute,
                                          pRadiationRelative,
                                          pProcessData,
                                          pSEUTemperature,
                                          pStorageTemperature)


    def displayReset(self):
        self.emit("displayResetChanged")
        if self.image_proxy is None:
            return
        try:
            self.image_proxy.erase_curves()
        except Exception, e:
            logging.exception(e)

    def messageDialog(self, pType, pMessage):
        if pType == 0:
            Qt.QMessageBox.information(self.brick_widget, "Info", pMessage)
        else:
            Qt.QMessageBox.critical(self.brick_widget, "Error", pMessage)

    def showMessage(self, pLevel, pMessage, notify = 0):
        if pLevel == 0:
            logging.info(pMessage)
        elif pLevel == 1:
            logging.warning(pMessage)
        elif pLevel == 2:
            logging.error(pMessage)

        self._collectRobotDialog.addHistory(pLevel, pMessage)
        if notify:
            self.messageDialog(pLevel, pMessage)


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

        #if self.robotCheckBox.isChecked():
        #   self._collectRobot.abort()

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

        enabled = (not self.__expertModeOnly or self.__expertMode) and (not self.readOnlyCheckBox.isChecked())


        self.maskLineEdit.setEnabled(enabled)
        self.maskDirectoryPushButton.setEnabled(enabled)
        self.maskDisplayPushButton.setEnabled(enabled and self.__validParameters[2])
        self.detectorDistanceDoubleSpinBox.setEnabled(enabled)
        self.pixelSizeXDoubleSpinBox.setEnabled(enabled)
        self.pixelSizeYDoubleSpinBox.setEnabled(enabled)
        self.beamCenterXSpinBox.setEnabled(enabled)
        self.beamCenterYSpinBox.setEnabled(enabled)
        self.normalisationDoubleSpinBox.setEnabled(enabled)

    def setButtonState(self, pOption):
        # TODO : DEBUG
#        buttons = (self.processCheckBox,
#                   self.notifyCheckBox, self.robotCheckBox, self.spectroCheckBox, self.testPushButton, self.collectPushButton, self.abortPushButton)
        buttons = (self.processCheckBox,
                   self.notifyCheckBox, self.robotCheckBox, self.testPushButton, self.collectPushButton, self.abortPushButton)
        def enable_buttons(*args):
            if len(args) == 1:
                for button in buttons:
                    button.setEnabled(args[0])
            else:
                for i in range(len(buttons)):
                    buttons[i].setEnabled(args[i])
        if pOption == 0:     # normal      
            enable_buttons(True)
            self.abortPushButton.setEnabled(False)
        elif pOption == 1:   # collecting
            enable_buttons(False)
            self.abortPushButton.setEnabled(True)
        elif pOption == 2:   # invalid parameters
            enable_buttons(True, True, True, True, False, False, False)

        if self.abortPushButton.isEnabled():
            self.abortPushButton.setProperty("abortactive", "true")
        else:
            self.abortPushButton.setProperty("abortactive", "false")

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
            logging.getLogger().warning("The frame was not collected or didn't appear on time! (%d,%d)" % (self._currentFrame, self._frameNumber))

    def getFilenameDetails(self, pFilename):
        pFilename = str(pFilename)
        i = pFilename.rfind(".")
        if i == -1:
            myFile = pFilename
            extension = ""
        else:
            myFile = pFilename[:i]
            extension = pFilename[i + 1:]
        items = myFile.split("_")
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


# TODO : DEBUG
class EdnaTangoCallbackThread(threading.Thread):

    def __init__(self, _deviceProxy, _successCallback = None, _failureCallback = None):
        threading.Thread.__init__(self)
        self._dev = PyTango.DeviceProxy(_deviceProxy)
        if _successCallback != None:
            self._dev.subscribe_event("jobSuccess", PyTango.EventType.CHANGE_EVENT, _successCallback, [])
        if _failureCallback != None:
            self._dev.subscribe_event("jobSuccess", PyTango.EventType.CHANGE_EVENT, _failureCallback, [])

    def run(self):
        bContinue = True
        while bContinue:
            time.sleep(1)
