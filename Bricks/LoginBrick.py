import sip
from Framework4.GUI import Core
from Framework4.GUI.Core import Property, Signal
from PyQt4 import QtCore, Qt


__category__ = "General"



class LoginBrick(Core.BaseBrick):



    properties = {"password": Property("string", "Password", "", "passwordChanged"),
                  "orientation": Property("combo", "Orientation", "layout of widgets", "orientationChanged", "Portrait", ["Portrait", "Landscape"])}

    connections = {}


    signals = [Signal("expertModeChanged")]
    slots = []


    def __init__(self, *args, **kargs):
        Core.BaseBrick.__init__(self, *args, **kargs)



    def init(self):
        self.__expertMode = False
        self.__password = ""

        self.modeLabel = Qt.QLabel("USER", self.brick_widget)
        self.modeLabel.setMinimumWidth(55)
        self.modeLabel.setToolTip("Current mode")
        self.modePushButton = Qt.QPushButton("Change", self.brick_widget)
        self.modePushButton.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.modePushButton.setToolTip("Change to expert mode")
        Qt.QObject.connect(self.modePushButton, Qt.SIGNAL("clicked()"), self.modePushButtonClicked)

    def passwordChanged(self, pValue):
        self.__password = pValue


    def orientationChanged(self, pValue):
        if self.brick_widget.layout() is not None:
            self.brick_widget.layout().removeWidget(self.modeLabel)
            self.brick_widget.layout().removeWidget(self.modePushButton)
            sip.transferback(self.brick_widget.layout())
        if pValue == "Landscape":
            self.brick_widget.setLayout(Qt.QHBoxLayout())
            self.modeLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        else:
            self.brick_widget.setLayout(Qt.QVBoxLayout())
            self.modeLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.brick_widget.layout().addWidget(self.modeLabel)
        self.brick_widget.layout().addWidget(self.modePushButton)


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


    def connectionStatusChanged(self, pPeer):
        pass


