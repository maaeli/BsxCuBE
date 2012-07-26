import logging
from Framework4.GUI import Core
from Framework4.GUI.Core import Property, PropertyGroup, Connection, Signal, Slot
from PyQt4 import QtCore, QtGui, Qt

__category__ = "General"

class CalibrationDiamondBrick(Core.BaseBrick):
    properties = {"caption": Property("string", "Caption", "", "captionChanged"),
                  "parameter": Property("string", "Parameter", "", "parameterChanged"),
                  "toolTip": Property("string", "Tool tip", "", "toolTipChanged"),
                  "expertModeOnly": Property("boolean", "Expert mode only", "", "expertModeOnlyChanged", False)}


    connections = {"calibration": Connection("Calibration object",
                                            [],
                                            [],
                                            "calibrationObjectConnected")}

    signals = []
    slots = []

    def __init__(self, *args, **kargs):
        Core.BaseBrick.__init__(self, *args, **kargs)


    def init(self):
        self.__parameter = ""
        self.__toolTip = ""
        self.__expertModeOnly = False
        self.__expertMode = False
        self.__setPosition = False
        self.__newPosition = 0
        self.calibration_object = None

        self.brick_widget.setLayout(Qt.QVBoxLayout())
        self.commandPushButton = Qt.QPushButton(self.brick_widget)
        Qt.QObject.connect(self.commandPushButton, Qt.SIGNAL("clicked()"), self.commandPushButtonClicked)
        self.brick_widget.layout().addWidget(self.commandPushButton)


    def captionChanged(self, pValue):
        self.commandPushButton.setText(pValue)


    def parameterChanged(self, pValue):
        self.__parameter = pValue


    def toolTipChanged(self, pValue):
        self.__toolTip = pValue
        self.commandPushButton.setToolTip(self.__toolTip)


    def expertModeOnlyChanged(self, pValue):
        self.__expertModeOnly = pValue
        self.expert_mode(self.__expertMode)


    def commandPushButtonClicked(self):
        self.__setPosition = True




    def expert_mode(self, expert):
        self.__expertMode = expert
        self.commandPushButton.setEnabled(not self.__expertModeOnly or self.__expertMode)


    def calibrationObjectConnected(self, peer):
        self.calibration_object = peer
        if self.calibration_object is None:
            self.brick_widget.setEnabled(False)
        else:
            self.brick_widget.setEnabled(True)


