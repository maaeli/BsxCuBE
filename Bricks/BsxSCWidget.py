import sys, os, time
import logging

from PyQt4  import QtCore, QtGui, Qt
import WellPicker , TimeDialog, TemperatureSelector

logger = logging.getLogger("BsxSCWidget")

class BsxSCWidget(Qt.QWidget):

    def __init__(self, parent):

        self.__robotMoveState = 0
        self.plateGeometry = []
        self.lastWell = [1, 1, 1]

        Qt.QWidget.__init__(self, parent)

        self.vBoxLayout = Qt.QVBoxLayout()

        self.topHBox = Qt.QHBoxLayout()
        self.syringeGroup = Qt.QGroupBox("Syringe", self)
        self.actionGroup = Qt.QGroupBox("Actions", self)
        self.tempGroup = Qt.QGroupBox("Temperature", self)
        self.bottomBox = Qt.QHBoxLayout()

        self.vBoxLayout.addLayout(self.topHBox)
        self.vBoxLayout.addWidget(self.actionGroup)
        self.vBoxLayout.addLayout(self.bottomBox)

        #  Top Line
        self.syringeLayout = Qt.QHBoxLayout()
        self.robotMoveBackwardPushButton = Qt.QPushButton("<<", self)
        self.robotMoveBackwardPushButton.setFixedWidth(150)
        self.robotMoveBackwardPushButton.setToolTip("Move liquid backward")
        Qt.QObject.connect(self.robotMoveBackwardPushButton, Qt.SIGNAL("pressed()"), self.robotMoveBackwardPushButtonPressed)
        Qt.QObject.connect(self.robotMoveBackwardPushButton, Qt.SIGNAL("released()"), self.robotMoveBackwardPushButtonReleased)
        self.syringeLayout.addWidget(self.robotMoveBackwardPushButton)

        self.robotFixLiquidPositionPushButton = Qt.QPushButton(">|<", self)
        self.robotFixLiquidPositionPushButton.setFixedWidth(150)
        self.robotFixLiquidPositionPushButton.setToolTip("Fix liquid position")
        Qt.QObject.connect(self.robotFixLiquidPositionPushButton, Qt.SIGNAL("clicked()"), self.robotFixLiquidPositionPushButtonClicked)
        self.syringeLayout.addWidget(self.robotFixLiquidPositionPushButton)

        self.robotMoveForwardPushButton = Qt.QPushButton(">>", self)
        self.robotMoveForwardPushButton.setFixedWidth(150)
        self.robotMoveForwardPushButton.setToolTip("Move liquid forward")
        Qt.QObject.connect(self.robotMoveForwardPushButton, Qt.SIGNAL("pressed()"), self.robotMoveForwardPushButtonPressed)
        Qt.QObject.connect(self.robotMoveForwardPushButton, Qt.SIGNAL("released()"), self.robotMoveForwardPushButtonReleased)
        self.syringeLayout.addWidget(self.robotMoveForwardPushButton)

        self.syringeGroup.setLayout(self.syringeLayout)

        self.topHBox.addWidget(self.syringeGroup)
        self.topHBox.addWidget(self.tempGroup)

        #  Action group
        self.actionLayout = Qt.QHBoxLayout()

        self.robotFillPushButton = Qt.QPushButton("Fill", self)
        Qt.QObject.connect(self.robotFillPushButton, Qt.SIGNAL("clicked()"), self.robotFillPushButtonClicked)
        self.actionLayout.addWidget(self.robotFillPushButton)

        self.robotRecuperatePushButton = Qt.QPushButton("Recuperate", self)
        Qt.QObject.connect(self.robotRecuperatePushButton, Qt.SIGNAL("clicked()"), self.robotRecuperatePushButtonClicked)
        self.actionLayout.addWidget(self.robotRecuperatePushButton)

        self.robotCleanPushButton = Qt.QPushButton("Clean", self)
        Qt.QObject.connect(self.robotCleanPushButton, Qt.SIGNAL("clicked()"), self.robotCleanPushButtonClicked)
        self.actionLayout.addWidget(self.robotCleanPushButton)

        self.robotDryPushButton = Qt.QPushButton("Dry", self)
        Qt.QObject.connect(self.robotDryPushButton, Qt.SIGNAL("clicked()"), self.robotDryPushButtonClicked)
        self.actionLayout.addWidget(self.robotDryPushButton)

        self.robotFlowPushButton = Qt.QPushButton("Flow", self)
        Qt.QObject.connect(self.robotFlowPushButton, Qt.SIGNAL("clicked()"), self.robotFlowPushButtonClicked)
        self.actionLayout.addWidget(self.robotFlowPushButton)

        self.robotMixPushButton = Qt.QPushButton("Mix", self)
        Qt.QObject.connect(self.robotMixPushButton, Qt.SIGNAL("clicked()"), self.robotMixPushButtonClicked)
        self.actionLayout.addWidget(self.robotMixPushButton)

        self.robotTransferPushButton = Qt.QPushButton("Transfer", self)
        Qt.QObject.connect(self.robotTransferPushButton, Qt.SIGNAL("clicked()"), self.robotTransferPushButtonClicked)
        self.actionLayout.addWidget(self.robotTransferPushButton)

        self.robotAbortPushButton = Qt.QPushButton("Abort", self)
        Qt.QObject.connect(self.robotAbortPushButton, Qt.SIGNAL("clicked()"), self.robotAbortPushButtonClicked)
        self.robotAbortPushButton.setDisabled(True)
        self.robotAbortPushButton.setObjectName("abortbutton")
        self.robotAbortPushButton.setProperty("abortactive", "false")

        self.actionLayout.addWidget(self.robotAbortPushButton)

        self.actionGroup.setLayout(self.actionLayout)

        #  Temperature settings

        self.tempLayout = Qt.QHBoxLayout()

        self.robotStorageTemperatureLabel = Qt.QLabel("Storage Temp.", self)
        self.tempLayout.addWidget(self.robotStorageTemperatureLabel)

        self.robotStorageTemperatureLineEdit = Qt.QLineEdit(self)
        self.robotStorageTemperatureLineEdit.setDisabled(True)
        self.robotStorageTemperatureLineEdit.setFixedWidth(80)
        self.tempLayout.addWidget(self.robotStorageTemperatureLineEdit)

        self.robotStorageTemperaturePushButton = Qt.QPushButton("Set", self)
        Qt.QObject.connect(self.robotStorageTemperaturePushButton, Qt.SIGNAL("clicked()"), self.robotStorageTemperaturePushButtonClicked)
        self.tempLayout.addWidget(self.robotStorageTemperaturePushButton)

        self.robotSEUTemperatureLabel = Qt.QLabel("SEU Temp.", self)
        self.tempLayout.addWidget(self.robotSEUTemperatureLabel)

        self.robotSEUTemperatureLineEdit = Qt.QLineEdit(self)
        self.robotSEUTemperatureLineEdit.setDisabled(True)
        self.robotSEUTemperatureLineEdit.setFixedWidth(80)
        self.tempLayout.addWidget(self.robotSEUTemperatureLineEdit)

        self.robotSEUTemperaturePushButton = Qt.QPushButton("Set", self)
        Qt.QObject.connect(self.robotSEUTemperaturePushButton, Qt.SIGNAL("clicked()"), self.robotSEUTemperaturePushButtonClicked)
        self.tempLayout.addWidget(self.robotSEUTemperaturePushButton)

        self.tempGroup.setLayout(self.tempLayout)

        #  Bottom Line
        self.robotSampleStateLabel = Qt.QLabel("State: ", self)
        self.robotSampleStateLabel.setFixedWidth(70)
        self.bottomBox.addWidget(self.robotSampleStateLabel)

        self.robotSampleChangerStatus = Qt.QLabel()
        self.robotSampleChangerStatus.setObjectName("statuslabel")
        self.robotSampleChangerStatus.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.bottomBox.addWidget(self.robotSampleChangerStatus)

        self.robotRestartPushButton = Qt.QPushButton("Restart", self)
        self.robotRestartPushButton.setFixedWidth(150)
        self.robotRestartMenu = Qt.QMenu(self.robotRestartPushButton)
        self.robotRestartWithHomingAction = Qt.QAction("With homing", self.robotRestartMenu)
        self.robotRestartWithoutHomingAction = Qt.QAction("Without homing", self.robotRestartMenu)
        self.robotRestartMenu.addAction(self.robotRestartWithHomingAction)
        self.robotRestartMenu.addAction(self.robotRestartWithoutHomingAction)
        Qt.QObject.connect(self.robotRestartWithHomingAction, Qt.SIGNAL("triggered(bool)"), self.robotRestartWithHomingActionTriggered)
        Qt.QObject.connect(self.robotRestartWithoutHomingAction, Qt.SIGNAL("triggered(bool)"), self.robotRestartWithoutHomingActionTriggered)
        self.robotRestartPushButton.setMenu(self.robotRestartMenu)
        self.bottomBox.addWidget(self.robotRestartPushButton)

        self.setStyleSheet(' #abortbutton[abortactive="true"]  {background-color: red;color: white}\
                             #abortbutton[abortactive="false"] {background-color: #fff;color: black}\
                             #statuslabel[state="running"] {background-color: #ff0;color: black}\
                             #statuslabel[state="standby"] {background-color: #0f0;color: black}\
                             #statuslabel[state="disconnected"] {background-color: #f0f;color: black}\
                             #statuslabel[state="alarm"] {background-color: #f0f;color: black}')

        self.setLayout(self.vBoxLayout)
        self.__sampleChangerDisplayFlag = False
        self.__sampleChangerDisplayMessage = ""

    # 
    # BUTTON Callbacks
    #
    #
    # syringe callbacks
    #
    def robotFixLiquidPositionPushButtonClicked(self):
        logger.info("Fixing liquid position...")
        self.__sampleChangerDisplayFlag = True
        self.__sampleChangerDisplayMessage = "Error when trying to fix liquid position!"
        self.setLiquidPositionFixed(True)

    def robotMoveForwardPushButtonPressed(self):
        self.__robotMoveState = 2
        self.__sampleChangerDisplayFlag = True
        self.__sampleChangerDisplayMessage = "Error when trying to move syringe forward!"
        self.startSyringeForward()

    def robotMoveBackwardPushButtonPressed(self):
        logger.info("Moving syringe backward...")
        self.__robotMoveState = 1
        self.__sampleChangerDisplayFlag = True
        self.__sampleChangerDisplayMessage = "Error when trying to move syringe backward!"
        self.startSyringeBackward()

    def robotMoveForwardPushButtonReleased(self):
        self.__robotMoveState = 0
        self.robotStopSyringe()

    def robotMoveBackwardPushButtonReleased(self):
        self.__robotMoveState = 0
        self.robotStopSyringe()

    def robotStopSyringe(self):
        logger.info("Stopping syringe...")
        self.__sampleChangerDisplayFlag = True
        self.__sampleChangerDisplayMessage = "Error when trying to stop syringe!"
        self.stopSyringe()

    #
    # action callbacks
    #
    def robotFillPushButtonClicked(self):
        well = WellPicker.getWellAndVolume(self.plateGeometry, "Select Well", default_well = self.lastWell)
        if well != None:
            logger.info('filling from [plate, row, column] = %s', well)
            self.lastWell = well[0:3]
            self.fill(*well)

    def robotDryPushButtonClicked(self):
        dryTime, buttonOk = Qt.QInputDialog.getInteger(self, "Dry", "\nPlease, insert time of drying (seconds):", 15, 1, 60, 2)
        if buttonOk:
            logger.info("Drying robot...")
            self.__sampleChangerDisplayFlag = True
            self.__sampleChangerDisplayMessage = "Error when trying to dry robot!"
            self.dry(dryTime)

    def robotFlowPushButtonClicked(self):
        flowtime = TimeDialog.getTime("Flowing Time")
        if flowtime != None:
           logger.info("Flowing '" + str(flowtime) + "' second(s)...")
           self.__sampleChangerDisplayFlag = True
           self.__sampleChangerDisplayMessage = "Error when trying to flow!"
           self.flow(flowtime)

    def robotRecuperatePushButtonClicked(self):
        well = WellPicker.getWell(self.plateGeometry, "Recuperate to:" , default_well = self.lastWell)
        if well != None:
            self.lastWell = well[0:3]
            logger.info('recuperating to [plate, row, column] = %s', well)
            self.recuperate(*well)

    def robotCleanPushButtonClicked(self):
        logger.info("Cleaning the robot...")
        self.__sampleChangerDisplayFlag = True
        self.__sampleChangerDisplayMessage = "Error when trying to clean the robot!"
        self.clean()

    def robotMixPushButtonClicked(self):
        values = WellPicker.getWellVolumeAndCycles(self.plateGeometry, "Select Well,Vol and Cycles", default_well = self.lastWell)
        if values != None:
            self.lastWell = values[0:3]
            logger.info("Mixing volume(%s) for %s cycles on %s" % (values[4], values[3], str(values[0:3])))
            self.mix(*values)

    def robotTransferPushButtonClicked(self):
        values = WellPicker.getTwoWellsAndVolume(self.plateGeometry, "From", "To", default_well = self.lastWell)
        if values != None :
            self.lastWell = values[0:3]
            logger.info("Transfering volume(%s) from %s to %s" % (values[-1], values[0:3], values[3:6]))
            self.transfer(*values)

    def robotAbortPushButtonClicked(self):
        logger.info("Aborting ongoing action in robot...")
        self.__sampleChangerDisplayFlag = False
        self.abort()

    #
    # Temperature callbacks
    #
    def robotStorageTemperaturePushButtonClicked(self):

        initvalue = self.robotStorageTemperatureLineEdit.text().split(" ")[0]
        if not str(initvalue).strip():
            initvalue = None
        temperature = TemperatureSelector.getTemperature("Storage temperature", initvalue)

        logger.info("Setting storage temperature to '" + str(temperature) + "'...")
        self.__sampleChangerDisplayFlag = True
        self.__sampleChangerDisplayMessage = "Error when trying to set storage temperature!"
        self.setStorageTemperature(temperature)

    def robotSEUTemperaturePushButtonClicked(self):
        initvalue = self.robotSEUTemperatureLineEdit.text().split(" ")[0]
        temperature = TemperatureSelector.getTemperature("SEU temperature", initvalue, minvalue = 4, maxvalue = 60)

        logger.info("Setting SEU temperature to '" + str(temperature) + "'...")
        self.__sampleChangerDisplayFlag = True
        self.__sampleChangerDisplayMessage = "Error when trying to set SEU temperature!"
        self.setSEUTemperature(temperature)

    #
    # other callbacks  (restart,)
    #

    def robotRestartWithHomingActionTriggered(self):
        logger.info("Restarting (with homing) the robot...")
        self.__sampleChangerDisplayFlag = True
        self.__sampleChangerDisplayMessage = "Error when trying to restart (with homing) the robot!"
        self.restart(True)

    def robotRestartWithoutHomingActionTriggered(self):
        logger.info("Restarting (without homing) the robot...")
        self.__sampleChangerDisplayFlag = True
        self.__sampleChangerDisplayMessage = "Error when trying to restart (without homing) the robot!"
        self.restart(False)

    #  
    # Slots .  Overload these for behaviour if needed
    #
    def setPlateGeometry(self, plateGeometry):
        #TODO: DEBUG
        print ">>> Set PlateGeometry to %r " % plateGeometry
        if self.plateGeometry == []:
            self.plateGeometry = plateGeometry
        else:
            # Workaround for bug in calling "Sample change connected" twice
            for geometryArray in  plateGeometry:
                if plateGeometry != '':
                    self.plateGeometry.append(geometryArray)
        print ">>> PlateGeometry is now %r " % self.plateGeometry

    def startSyringeForward(self):
        print "Starting syringe forward"
    def startSyringeBackward(self):
        print "Starting syringe backward"
    def stopSyringe(self):
        print "Stopping syringe "

    def setLiquidPositionFixed(self, yesno):
        print "Fixing liquid position (%s) " % yesno

    def fill(self, *selected_well):
        print "Filling from %s , volume=%s", selected_well[0:3], selected_well[3]
    def dry(self, drytime):
        print "Drying for ", drytime, " seconds"
    def flow(self, flowtime):
        print "Flowing for ", flowtime, " seconds"
    def recuperate(self, *selected_well):
        print "Recuperate to ", selected_well
    def clean(self):
        print "Cleaning "
    def abort(self):
        print "Aborting action "
    def mix(self, *selected_values):
        print "Mixing "
    def transfer(self, *selected_values):
        print "Transferring (volume=%s) from %s to %s " % (selected_values[-1], selected_values[0:3], selected_values[3, 6])

    def restart(self, flag):
        print "Restarting... (%s)" % flag

    # Overwritten in Brick
    def setStorageTemperature(self, temperature):
        print "Setting storage temperature to ", temperature

    # Overwritten in Brick
    def setSEUTemperature(self, temperature):
        print "Setting SEU temperature to ", temperature

    def setCurrentStorageTemperature(self, temperature):
        if temperature != None:
           self.robotStorageTemperatureLineEdit.setText("%02.2f C" % float(temperature))

    def setCurrentSEUTemperature(self, temperature):
        if temperature != None:
           self.robotSEUTemperatureLineEdit.setText("%02.2f C" % float(temperature))

    def setState(self, state, status = "", exception = None):

        if (state == "READY"):
            state = "STANDBY"

        stateLine = "%s (%s)" % (str(state), str(status))
        self.robotSampleChangerStatus.setText(stateLine)

        self.robotMoveBackwardPushButton.setEnabled       (state == "STANDBY" or self.__robotMoveState == 1)
        self.robotMoveForwardPushButton.setEnabled        (state == "STANDBY" or self.__robotMoveState == 2)
        self.robotFixLiquidPositionPushButton.setEnabled  (state == "STANDBY")

        self.robotStorageTemperaturePushButton.setEnabled (state == "STANDBY")
        self.robotSEUTemperaturePushButton.setEnabled     (state == "STANDBY")

        self.robotFillPushButton.setEnabled               (state == "STANDBY")
        self.robotRecuperatePushButton.setEnabled         (state == "STANDBY" and status.startswith("Loaded"))
        self.robotCleanPushButton.setEnabled              (state == "STANDBY")
        self.robotDryPushButton.setEnabled                (state == "STANDBY" and status == "Cleaned")
        self.robotFlowPushButton.setEnabled               (state == "STANDBY" and status.startswith("Loaded"))
        self.robotMixPushButton.setEnabled                (state == "STANDBY" and not status.startswith("Loaded"))
        self.robotTransferPushButton.setEnabled           (state == "STANDBY" and not status.startswith("Loaded"))

        self.robotRestartPushButton.setEnabled            (state not in ("MOVING", "RUNNING", "INIT", "DISCONNECTED"))

        if state in ("ALARM", "MOVING", "RUNNING"):
            self.robotAbortPushButton.setDisabled(False)
            self.robotAbortPushButton.setProperty("abortactive", "true")
        else:
            self.robotAbortPushButton.setDisabled(True)
            self.robotAbortPushButton.setProperty("abortactive", "false")

        if state in ("ALARM", "FAULT"):
            self.robotSampleChangerStatus.setProperty("state", "alarm")
        elif state in ("MOVING", "RUNNING"):
            self.robotSampleChangerStatus.setProperty("state", "running")
        elif state in ("STANDBY", "INIT"):
            self.robotSampleChangerStatus.setProperty("state", "standby")
        else:
            self.robotSampleChangerStatus.setProperty("state", "disconnected")

        if state == "STANDBY":
            if self.__sampleChangerDisplayFlag:
                 if self.__sampleChangerDisplayMessage != "":
                     message = self.__sampleChangerDisplayMessage
                     self.__sampleChangerDisplayMessage = ""
                     if exception is not None and exception != "":
                             Qt.QMessageBox.critical(self, "Error", message)
                 self.__sampleChangerDisplayFlag = False
        else:
           self.__sampleChangerDisplayFlag = True

        self.setStyleSheet(self.styleSheet())


if __name__ == '__main__':
    from PyTango import DeviceProxy
    import sys

    sc = DeviceProxy("nela:20000/bm29/bssc/1")
    geometry = [ sc.getPlateInfo(i) for i in range(1, 4) ]

    app = QtGui.QApplication(sys.argv)

    win = Qt.QMainWindow()
    wid = BsxSCWidget(win)
    wid.setPlateGeometry (geometry)
    win.setCentralWidget(wid)
    wid.setWindowTitle('Collect Robot')
    wid.setState("Disconnected", "SC GUI not running?")
    win.show()

    sys.exit(app.exec_())
