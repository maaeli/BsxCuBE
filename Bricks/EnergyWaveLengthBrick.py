import logging
from Framework4.GUI import Core
from Framework4.GUI.Core import Property, Connection, Signal
from PyQt4 import QtGui, Qt

__category__ = "BsxCuBE"


class EnergyWavewLengthBrick(Core.BaseBrick):

    properties = {}

    connections = {"login": Connection("Login object",
                                        [Signal("loggedIn", "loggedIn")],
                                        [],
                                        "connectionToLogin")}


    signals = []
    slots = []


    def __init__(self, *args, **kargs):
        Core.BaseBrick.__init__(self, *args, **kargs)


    def init(self):
        #
        # Layout
        #
        self.vboxLayout = Qt.QVBoxLayout()
        self.hBox1Layout = Qt.QHBoxLayout()

        self.brick_widget.setLayout(self.vboxLayout)

        self.energyLabel = Qt.QLabel("Energy (current, new)", self.brick_widget)
        self.hBox1Layout.addWidget(self.energyLabel)

        self.energyLineEdit = Qt.QLineEdit(self.brick_widget)
        self.energyLineEdit.setEnabled(False)
        self.energyLineEdit.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.energyLineEdit.setToolTip("Current Energy")
        self.hBox1Layout.addWidget(self.energyLineEdit)

        self.newEnergyLineEdit = Qt.QLineEdit(self.brick_widget)
        self.newEnergyLineEdit.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.newEnergyLineEdit.setToolTip("New Energy")
        Qt.QObject.connect(self.newEnergyLineEdit, Qt.SIGNAL("editTextChanged(const QString &)"), self.newEnergyChanged)
        Qt.QObject.connect(self.newEnergyLineEdit, Qt.SIGNAL("returnPressed()"), self.newEnergyReturnPressed)
        self.hBox1Layout.addWidget(self.newEnergyLineEdit)

        self.brick_widget.layout().addLayout(self.hBox1Layout)

        self.hBox2Layout = Qt.QHBoxLayout()

        self.wavelengthLabel = Qt.QLabel("Wavelength (current, new)", self.brick_widget)
        self.hBox2Layout.addWidget(self.wavelengthLabel)

        self.waveLengthLineEdit = Qt.QLineEdit(self.brick_widget)
        self.waveLengthLineEdit.setEnabled(False)
        self.waveLengthLineEdit.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.waveLengthLineEdit.setToolTip("Current Wavelength")
        self.hBox2Layout.addWidget(self.waveLengthLineEdit)

        self.newWaveLengthLineEdit = Qt.QLineEdit(self.brick_widget)
        self.newWaveLengthLineEdit.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.newWaveLengthLineEdit.setToolTip("New WaveLength")
        Qt.QObject.connect(self.newWaveLengthLineEdit, Qt.SIGNAL("editTextChanged(const QString &)"), self.newWaveLengthChanged)
        Qt.QObject.connect(self.newWaveLengthLineEdit, Qt.SIGNAL("returnPressed()"), self.newWaveLengthReturnPressed)
        self.hBox2Layout.addWidget(self.newWaveLengthLineEdit)

        self.brick_widget.layout().addLayout(self.hBox2Layout)


    # When connected to Login, then block the brick
    def connectionToLogin(self, pPeer):
        if pPeer is not None:
            self.brick_widget.setEnabled(False)

    # Logged In : True or False 
    def loggedIn(self, pValue):
        self.brick_widget.setEnabled(pValue)

    def energyChanged(self, pValue):
        if pValue is not None:
            self.energyLineEdit.setText(str(float(pValue)) + "Angstrom")

    def connectionStatusChanged(self, pPeer):
        pass

    def newEnergyChanged(self, pValue):
        print "New Energy"


    def newEnergyReturnPressed(self, pValue):
        print "New Energy Return Pressed"

    def newWaveLengthChanged(self, pValue):
        pass

    def newWaveLengthReturnPressed(self, pValue):
        pass

