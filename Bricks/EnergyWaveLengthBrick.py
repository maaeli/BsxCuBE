from Framework4.GUI import Core
from Framework4.GUI.Core import Connection, Signal, Slot
from PyQt4 import Qt


__category__ = "General"


class EnergyWaveLengthBrick(Core.BaseBrick):


    properties = {}

    connections = {"energy": Connection("Energy object",
                                            [Signal("energyChanged", "energyChanged")],
                                            [Slot("setEnergy"), Slot("getEnergy")],
                                            "connectedToEnergy"),
                   "login": Connection("Login object",
                                            [Signal("loggedIn", "loggedIn")],
                                            [],
                                            "connectionToLogin")}

    signals = []
    slots = []


    def __init__(self, *args, **kargs):
        Core.BaseBrick.__init__(self, *args, **kargs)


    def init(self):
        # The keV to Angstrom calc
        self.hcOverE = 12.398

        self.vboxLayout = Qt.QVBoxLayout()
        self.hBox1Layout = Qt.QHBoxLayout()

        self.brick_widget.setLayout(self.vboxLayout)
        self.energyLabel = Qt.QLabel("Energy [keV]     (current, new)", self.brick_widget)
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

        self.wavelengthLabel = Qt.QLabel("Wavelength [A] (current, new)", self.brick_widget)
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
            self.__energy = float(pValue)
            energyStr = "%.4f" % self.__energy
            self.energyLineEdit.setText(energyStr + " keV")
            # and calculate wavelength
            wavelength = self.hcOverE / self.__energy
            wavelengthStr = "%.4f" % wavelength
            self.waveLengthLineEdit.setText(wavelengthStr + " Angstrom")

    def connectedToEnergy(self, pPeer):
        self.energyControlObject = pPeer
        # read energy when getting contact with CO Object
        self.__energy = self.energyControlObject.getEnergy()

    def newEnergyChanged(self):
        newEnergy = float(self.newEnergyLineEdit.text())
        if self.isEnergyOK(newEnergy):
            print "sent %.4f" % newEnergy
            newEnergyStr = "%.4f" % newEnergy
            self.energyControlObject.setEnergy(newEnergyStr)
        else:
            Qt.QMessageBox.critical(self.brick_widget, "Warning", "Only Energy between 7 and 15 keV", Qt.QMessageBox.Ok)

    def newEnergyReturnPressed(self):
        newEnergy = float(self.newEnergyLineEdit.text())
        if self.isEnergyOK(newEnergy):
            print "sent %.4f" % newEnergy
            newEnergyStr = "%.4f" % newEnergy
            self.energyControlObject.setEnergy(newEnergyStr)
        else:
            Qt.QMessageBox.critical(self.brick_widget, "Warning", "Only Energy between 7 and 15 keV", Qt.QMessageBox.Ok)

    def newWaveLengthChanged(self):
        print "New Wavelength"

    def newWaveLengthReturnPressed(self):
        print "New Wavelength Return Pressed"

    def isEnergyOK(self, energy):
        if energy < 7.0 or energy > 15.0 :
            return False
        else:
            return True

