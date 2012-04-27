from Framework4.GUI      import Core
from Framework4.GUI.Core import Connection, Signal, Slot
from PyQt4 import QtGui, Qt
import sip

__category__ = "General"

class LoginBrick(Core.BaseBrick):

    properties = {}

    signals = []
    slots = []


    def __init__(self, *args, **kargs):
        Core.BaseBrick.__init__(self, *args, **kargs)


    def init(self):
        self.__password = ""
        self.__user = "nobody"
        self.loginProxy = None
        # Just To Display (from Attenuator
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
        self.hBoxLayout.addWidget(self.newTransmissionComboBox)

        self.filtersPushButton = Qt.QPushButton("Filters", self.brick_widget)
        self.filtersPushButton.setToolTip("Enable/disable transmission filters")

        if self.brick_widget.layout() is not None:
            self.hBoxLayout.setParent(None)
            self.brick_widget.layout().removeWidget(self.filtersPushButton)
            sip.transferback(self.brick_widget.layout())
        self.brick_widget.setLayout(Qt.QHBoxLayout())
        self.filtersPushButton.setSizePolicy(Qt.QSizePolicy.Fixed, Qt.QSizePolicy.Expanding)
        self.brick_widget.layout().addLayout(self.hBoxLayout)
        self.brick_widget.layout().addWidget(self.filtersPushButton)
        self.newTransmissionComboBoxChanged(None)

    # From attenuatorBrick    
    def newTransmissionComboBoxChanged(self, pValue):
        if pValue is None or pValue == "":
            self.newTransmissionComboBox.lineEdit().palette().setColor(QtGui.QPalette.Base, QtGui.QColor(255, 255, 0))
        else:
            if self.newTransmissionComboBox.lineEdit().hasAcceptableInput():
                self.newTransmissionComboBox.lineEdit().palette().setColor(QtGui.QPalette.Base, QtGui.QColor(255, 255, 255))
            else:
                self.newTransmissionComboBox.lineEdit().palette().setColor(QtGui.QPalette.Base, QtGui.QColor(255, 0, 0))
        self.newTransmissionComboBox.lineEdit().update()



#    def passwordChanged(self, pValue):
#        self.__password = pValue
#
#    def loginConnected(self, pPeer):
#        if pPeer is not None:
#            # we are connected, let us block the other bricks
#            self.__loggedIn = False
#            self.loginProxy = pPeer
#            self.loginProxy.loginTry("tes")
#            self.emit("loggedIn", self.__loggedIn)
#
#    def modePushButtonClicked(self):
#        print "Pushed button"
