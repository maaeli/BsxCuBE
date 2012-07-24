import logging
import sip
from Framework4.GUI import Core
from Framework4.GUI.Core import Property, Connection, Signal, Slot
from PyQt4 import QtGui, Qt


__category__ = "General"


class AttenuatorsBrick(Core.BaseBrick):


    properties = {"maskFormat": Property("string", "Mask format", "", "maskFormatChanged"),
                  "suffix": Property("string", "Suffix", "", "suffixChanged"),
                  "maximumHistory": Property("integer", "Maximum history", "", "maximumHistoryChanged"),
                  "minimumValue": Property("float", "Minimum value", "", "minimumValueChanged"),
                  "maximumValue": Property("float", "Maximum value", "", "maximumValueChanged"),
                  "orientation": Property("combo", "Orientation", description = "Layout of widgets", onchange_cb = "orientationChanged", default = "Portrait", choices = ["Portrait", "Landscape"])}


    connections = {"attenuators": Connection("Attenuators object",
                                            [Signal("attenuatorsStateChanged", "attenuatorsStateChanged"),
                                             Signal("attenuatorsFactorChanged", "attenuatorsFactorChanged")],
                                            [],
                                            "connectionStatusChanged"),
                    "collect": Connection("Collect object",
                                            [Signal("collectProcessingDone", "collectProcessingDone"),
                                             Signal("collectProcessingLog", "collectProcessingLog"),
                                             Signal("collectDone", "collectDone"),
                                             Signal("clearCurve", "clearCurve"),
                                             Signal("grayOut", "grayOut"),
                                             Signal("transmissionChanged", "transmissionChanged")],
                                            [Slot("testCollect"),
                                             Slot("collect"),
                                             Slot("collectAbort"),
                                             Slot("setCheckBeam"),
                                             Slot("triggerEDNA"),
                                             Slot("blockGUI"),
                                             Slot("blockEnergyAdjust")],
                                            "collectObjectConnected"),
                    "login": Connection("Login object",
                                            [Signal("loggedIn", "loggedIn")],
                                             [],
                                             "connectionToLogin")}

    signals = []
    slots = []


    def __init__(self, *args, **kargs):
        Core.BaseBrick.__init__(self, *args, **kargs)


    def init(self):
        self.__filtersDialog = None
        self.__maskFormat = ""
        self.__suffix = ""
        self.__minimumValue = 0
        self.__maximumValue = 100

        self.hBoxLayout = Qt.QHBoxLayout()

        self.transmissionLabel = Qt.QLabel("Transmission (current, new)", self.brick_widget)
        self.hBoxLayout.addWidget(self.transmissionLabel)

        self.currentTransmissionLineEdit = Qt.QLineEdit(self.brick_widget)
        self.currentTransmissionLineEdit.setEnabled(False)
        self.currentTransmissionLineEdit.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.currentTransmissionLineEdit.setToolTip("Current transmission")
        self.hBoxLayout.addWidget(self.currentTransmissionLineEdit)

        self.newTransmissionComboBox = Qt.QComboBox(self.brick_widget)
        self.newTransmissionComboBox.setEditable(True)
        self.newTransmissionComboBox.lineEdit().setMaxLength(10)
        self.newTransmissionComboBox.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.newTransmissionComboBox.setToolTip("New transmission")
        Qt.QObject.connect(self.newTransmissionComboBox, Qt.SIGNAL("editTextChanged(const QString &)"), self.newTransmissionComboBoxChanged)
        Qt.QObject.connect(self.newTransmissionComboBox.lineEdit(), Qt.SIGNAL("returnPressed()"), self.newTransmissionComboBoxReturnPressed)
        self.hBoxLayout.addWidget(self.newTransmissionComboBox)

        self.filtersPushButton = Qt.QPushButton("Filters", self.brick_widget)
        self.filtersPushButton.setToolTip("Enable/disable transmission filters")
        Qt.QObject.connect(self.filtersPushButton, Qt.SIGNAL("clicked()"), self.filtersPushButtonClicked)

        self.newTransmissionComboBoxChanged(None)

    # When connected to Login, then block the brick
    def connectionToLogin(self, pPeer):
        if pPeer is not None:
            self.brick_widget.setEnabled(False)


    # Logged In : True or False 
    def loggedIn(self, pValue):
        self.brick_widget.setEnabled(pValue)


    def maskFormatChanged(self, pValue):
        self.__maskFormat = pValue
        self.attenuatorsFactorChanged(self.currentTransmissionLineEdit.text())


    def suffixChanged(self, pValue):
        self.__suffix = pValue
        #self.attenuatorsFactorChanged(self.currentTransmissionLineEdit.text())        


    def maximumHistoryChanged(self, pValue):
        self.newTransmissionComboBox.setMaxCount(pValue)


    def minimumValueChanged(self, pValue):
        self.__minimumValue = pValue
        self.newTransmissionComboBox.lineEdit().setValidator(Qt.QDoubleValidator(self.__minimumValue, self.__maximumValue, 10, self.newTransmissionComboBox.lineEdit()))


    def maximumValueChanged(self, pValue):
        self.__maximumValue = pValue
        self.newTransmissionComboBox.lineEdit().setValidator(Qt.QDoubleValidator(self.__minimumValue, self.__maximumValue, 10, self.newTransmissionComboBox.lineEdit()))


    def orientationChanged(self, pValue):
        if self.brick_widget.layout() is not None:
            self.hBoxLayout.setParent(None)
            self.brick_widget.layout().removeWidget(self.filtersPushButton)
            sip.transferback(self.brick_widget.layout())
        if pValue == "Landscape":
            self.brick_widget.setLayout(Qt.QHBoxLayout())
            self.filtersPushButton.setSizePolicy(Qt.QSizePolicy.Fixed, Qt.QSizePolicy.Expanding)
        else:
            self.brick_widget.setLayout(Qt.QVBoxLayout())
            self.filtersPushButton.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.brick_widget.layout().addLayout(self.hBoxLayout)
        self.brick_widget.layout().addWidget(self.filtersPushButton)


    def attenuatorsStateChanged(self, pValue):
        if self.__filtersDialog is not None:
            self.__filtersDialog.filtersChanged(pValue)


    def attenuatorsFactorChanged(self, pValue):
        if pValue == "":
            self.currentTransmissionLineEdit.setText(self.__suffix)
        else:
            if self.__maskFormat == "":
                self.currentTransmissionLineEdit.setText(str(float(pValue)) + self.__suffix)
            else:
                self.currentTransmissionLineEdit.setText(self.__maskFormat % float(pValue) + self.__suffix)

    # connected to Collect
    def collectObjectConnected(self, pValue):
        pass

    def collectProcessingDone(self, filename):
        pass

    def collectProcessingLog(self, level, logmsg, notify):
        pass

    def collectDone(self):
        pass

    def clearCurve(self):
        pass

    def grayOut(self, grayout):
        if grayout is not None:
            if grayout:
                self.newTransmissionComboBox.setEditable(False)
                self.filtersPushButton.setEnabled(False)
            else:
                self.newTransmissionComboBox.setEditable(True)
                self.filtersPushButton.setEnabled(True)


    def transmissionChanged(self, pValue):
        print ">> Set Transmission to %r " % pValue
        self.getObject("attenuators").setTransmission(float(pValue))


    def connectionStatusChanged(self, pPeer):
        pass


    def newTransmissionComboBoxChanged(self, pValue):
        if pValue is None or pValue == "":
            self.newTransmissionComboBox.lineEdit().palette().setColor(QtGui.QPalette.Base, QtGui.QColor(255, 255, 0))
        else:
            if self.newTransmissionComboBox.lineEdit().hasAcceptableInput():
                self.newTransmissionComboBox.lineEdit().palette().setColor(QtGui.QPalette.Base, QtGui.QColor(255, 255, 255))
            else:
                self.newTransmissionComboBox.lineEdit().palette().setColor(QtGui.QPalette.Base, QtGui.QColor(255, 0, 0))
        self.newTransmissionComboBox.lineEdit().update()


    def newTransmissionComboBoxReturnPressed(self):
        if self.newTransmissionComboBox.lineEdit().hasAcceptableInput():
            logging.getLogger().info("Setting transmission to " + self.newTransmissionComboBox.currentText() + " %...")
            self.getObject("attenuators").setTransmission(float(self.newTransmissionComboBox.currentText()))
            self.newTransmissionComboBox.clearEditText()


    def toggleFilter(self, pFilter, pChecked, pValue):
        if pChecked:
            logging.getLogger().info("Enabling filter '" + pFilter + "'...")
        else:
            logging.getLogger().info("Disabling filter '" + pFilter + "'...")
        self.getObject("attenuators").toggleFilter(pValue)


    def filtersPushButtonClicked(self):
        if self.__filtersDialog is not None and self.__filtersDialog.isVisible():
            self.__filtersDialog.activateWindow()
            self.__filtersDialog.raise_()
        else:
            attenuatorsList = self.getObject("attenuators").getAttenuatorsList()
            if attenuatorsList is None:
                Qt.QMessageBox.information(self.brick_widget, "Info", "There are no attenuators specified!")
            else:
                self.__filtersDialog = FiltersDialog(self, attenuatorsList)
                self.__filtersDialog.filtersChanged(self.getObject("attenuators").getAttenuatorsState())
                self.__filtersDialog.show()


# =============================================
#  OTHER CLASSES
# =============================================
class FiltersDialog(Qt.QDialog):


    def __init__(self, pParent, pAttenuatorsList):
        self.__parent = pParent
        self.__attenuatorsList = pAttenuatorsList
        self.__attenuatorsCheckBoxList = []

        Qt.QDialog.__init__(self, self.__parent.brick_widget)
        self.setWindowTitle("Transmission")
        self.setLayout(Qt.QVBoxLayout())
        self.filtersGroupBox = Qt.QGroupBox("Filters", self)
        self.filtersGroupBox.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.filtersVBoxLayout = Qt.QVBoxLayout(self.filtersGroupBox)
        self.layout().addWidget(self.filtersGroupBox)
        self.closePushButton = Qt.QPushButton("Close", self)
        self.closePushButton.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Fixed)
        self.closePushButton.setToolTip("Close window")
        self.layout().addWidget(self.closePushButton)
        Qt.QObject.connect(self.closePushButton, Qt.SIGNAL("clicked()"), self.closePushButtonClicked)

        for i in range(0, len(self.__attenuatorsList)):
            attenuatorsCheckBox = AttenuatorCheckBox(self.__parent, self.__attenuatorsList[i][0], i)
            self.filtersVBoxLayout.addWidget(attenuatorsCheckBox)
            self.__attenuatorsCheckBoxList.append(attenuatorsCheckBox)



    def filtersChanged(self, pValue):
        if pValue is not None:
            try:
                for i in range(0, len(self.__attenuatorsCheckBoxList)):
                    self.__attenuatorsCheckBoxList[i].blockSignals(True)
                    self.__attenuatorsCheckBoxList[i].setChecked(pValue & self.__attenuatorsList[i][1])
                    self.__attenuatorsCheckBoxList[i].blockSignals(False)
            except Exception, e:
                logging.getLogger().error("Error reading filter status '" + str(pValue) + "'!")
                logging.getLogger().error("Full Exception: " + str(e))



    def closePushButtonClicked(self):
        self.accept()


class AttenuatorCheckBox(Qt.QCheckBox):


    def __init__(self, pParent, pLabel, pIndex):
        self.__parent = pParent
        self.__label = pLabel
        self.__index = pIndex
        Qt.QCheckBox.__init__(self, pLabel)
        Qt.QObject.connect(self, Qt.SIGNAL("toggled(bool)"), self.attenuatorCheckBoxToggled)


    def attenuatorCheckBoxToggled(self, pValue):
        self.__parent.toggleFilter(self.__label, pValue, self.__index + 1)


