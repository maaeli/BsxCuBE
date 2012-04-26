import logging

from Framework4.GUI      import Core
from Framework4.GUI.Core import Connection, Signal
from PyQt4 import Qt

__category__ = "BsxCuBE"

class LoginBrick(Core.BaseBrick):

    properties = {}

    connections = {"login": Connection("Login object",
                    [],
                    [],
                    "loginConnected")}
    signals = [Signal("loggedIn")]
    slots = []


    def __init__(self, *args, **kargs):
        Core.BaseBrick.__init__(self, *args, **kargs)



    def init(self):
        self.__password = ""
        self.__user = "nobody"

        # layout
        self.modeLabel = Qt.QLabel("USER", self.brick_widget)
        self.modeLabel.setMinimumWidth(55)
        self.modeLabel.setToolTip("Current mode")
        self.modePushButton = Qt.QPushButton("Change", self.brick_widget)
        self.modePushButton.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.modePushButton.setToolTip("Change to expert mode")
        Qt.QObject.connect(self.modePushButton, Qt.SIGNAL("clicked()"), self.modePushButtonClicked)

    def passwordChanged(self, pValue):
        self.__password = pValue

    def loginConnected(self, pPeer):
        # we are connected, let us block the other bricks
        self.__loggedIn = False
        self.emit("loggedIn", self.__loggedIn)

    def modePushButtonClicked(self):
        if self.__expertMode:
            self.__expertMode = False
            self.emit("expertModeChanged", self.__expertMode)
            self.modeLabel.setText("USER")
            self.modePushButton.setToolTip("Change to expert mode")
            Qt.QMessageBox.information(self.brick_widget, "Info", "You are in user mode now!")
        else:
            password, buttonOk = Qt.QInputDialog.getText(self.brick_widget, "Login", "\nPlease, insert password for expert mode:", Qt.QLineEdit.Password)
            if buttonOk:
                if password == self.__password:
                    self.__expertMode = True
                    self.emit("expertModeChanged", self.__expertMode)
                    self.modeLabel.setText("EXPERT")
                    self.modePushButton.setToolTip("Change to user mode")
                    Qt.QMessageBox.information(self.brick_widget, "Info", "You are in expert mode now!")
                else:
                    Qt.QMessageBox.critical(self.brick_widget, "Error", "Invalid password. Please, try again!")
