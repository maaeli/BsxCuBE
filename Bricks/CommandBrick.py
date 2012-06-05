import logging
from Framework4.GUI import Core
from Framework4.GUI.Core import Property, Connection, Signal, Slot
from PyQt4 import Qt


__category__ = "General"


class CommandBrick(Core.BaseBrick):
    # =============================================
    #  PROPERTIES/CONNECTIONS DEFINITION
    # =============================================            
    properties = {"caption": Property("string", "Caption", "", "captionChanged"),
                  "parameter": Property("string", "Parameter", "", "parameterChanged"),
                  "toolTip": Property("string", "Tool tip", "", "toolTipChanged"),
                  "expertModeOnly": Property("boolean", "Expert mode only", "", "expertModeOnlyChanged", False)}


    connections = {"command": Connection("Command object",
                                            [Signal("commandStatusChanged", "commandStatusChanged")],
                                            [Slot("executeCommand")],
                                            "connectionStatusChanged")}

    signals = []
    slots = []


    def __init__(self, *args, **kargs):
        Core.BaseBrick.__init__(self, *args, **kargs)


    def init(self):
        self.__parameter = ""
        self.__toolTip = ""
        self.__expertModeOnly = False
        self.__expertMode = False

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
        self.getObject("command").executeCommand(self.__parameter)


    def commandStatusChanged(self, pValue):
        messageList = pValue.split(",", 2)
        if len(messageList) == 2:
            if messageList[0] == "0":   # command info
                logging.getLogger().info(messageList[1])
            elif messageList[0] == "1":     # command warning
                logging.getLogger().warning(messageList[1])
            elif messageList[0] == "2":     # command error
                logging.getLogger().error(messageList[1])

    def expert_mode(self, expert):
        self.__expertMode = expert
        self.commandPushButton.setEnabled(not self.__expertModeOnly or self.__expertMode)

    def connectionStatusChanged(self, peer):
        self.calibration_object = peer
        if self.calibration_object is None:
            self.brick_widget.setEnabled(False)
        else:
            self.brick_widget.setEnabled(True)
