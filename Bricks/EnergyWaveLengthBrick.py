import logging
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
        # to keep track in case a dialog boxes is open
        self.__energyDialogOpen = False
        self.__energyDialog = None
        self.__waveLengthDialogOpen = False
        self.__waveLengthDialog = None


    def init(self):
        # The keV to Angstrom calc
        self.hcOverE = 12.398

        self.vboxLayout = Qt.QVBoxLayout()
        self.hBox1Layout = Qt.QHBoxLayout()

        self.brick_widget.setLayout(self.vboxLayout)
        self.energyLabel = Qt.QLabel("Energy [keV]     ", self.brick_widget)
        self.hBox1Layout.addWidget(self.energyLabel)

        self.energyLineEdit = Qt.QLineEdit(self.brick_widget)
        self.energyLineEdit.setEnabled(False)
        self.energyLineEdit.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.energyLineEdit.setToolTip("Current Energy")
        self.hBox1Layout.addWidget(self.energyLineEdit)

        self.newEnergyPushButton = Qt.QPushButton("New Energy", self.brick_widget)
        Qt.QObject.connect(self.newEnergyPushButton, Qt.SIGNAL("clicked()"), self.newEnergyPushButtonClicked)
        self.hBox1Layout.addWidget(self.newEnergyPushButton)

        self.brick_widget.layout().addLayout(self.hBox1Layout)

        self.hBox2Layout = Qt.QHBoxLayout()

        self.wavelengthLabel = Qt.QLabel("Wavelength [A] ", self.brick_widget)
        self.hBox2Layout.addWidget(self.wavelengthLabel)

        self.waveLengthLineEdit = Qt.QLineEdit(self.brick_widget)
        self.waveLengthLineEdit.setEnabled(False)
        self.waveLengthLineEdit.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.waveLengthLineEdit.setToolTip("Current Wavelength")
        self.hBox2Layout.addWidget(self.waveLengthLineEdit)

        self.newWaveLengthPushButton = Qt.QPushButton("New Wavelength", self.brick_widget)
        Qt.QObject.connect(self.newWaveLengthPushButton, Qt.SIGNAL("clicked()"), self.newWaveLengthPushButtonClicked)
        self.hBox2Layout.addWidget(self.newWaveLengthPushButton)

        self.brick_widget.layout().addLayout(self.hBox2Layout)

    # When connected to Login, then block the brick
    def connectionToLogin(self, pPeer):
        if pPeer is not None:
            self.brick_widget.setEnabled(False)


    # Logged In : True or False 
    def loggedIn(self, pValue):
        self.brick_widget.setEnabled(pValue)

    def newEnergyPushButtonClicked(self):
        if self.__energyDialogOpen :
            self.__energyDialog.activateWindow()
            self.__energyDialog.raise_()
        else:
            self.__energyDialog = EnterEnergy(self)
            self.__energyDialog.show()

    def energyDialogOpen(self):
        self.__energyDialogOpen = True

    def energyDialogClose(self):
        self.__energyDialogOpen = False


    def newWaveLengthPushButtonClicked(self):
        if self.__waveLengthDialogOpen :
            self.__waveLengthDialog.activateWindow()
            self.__waveLengthDialog.raise_()
        else:
            self.__waveLengthDialog = EnterWaveLength(self)
            self.__waveLengthDialog.show()

    def waveLengthDialogOpen(self):
        self.__waveLengthDialogOpen = True

    def waveLengthDialogClose(self):
        self.__waveLengthDialogOpen = False

    def setEnergy(self, energyStr):
        if self.energyControlObject is not None:
            self.energyControlObject.setEnergy(energyStr)
        else:
            logging.error("Could not set Energy to " + energyStr)

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
        if pPeer is not None:
            self.energyControlObject = pPeer
            # read energy when getting contact with CO Object
            self.__energy = float(self.energyControlObject.getEnergy())
            energyStr = "%.4f" % self.__energy
            self.energyLineEdit.setText(energyStr + " keV")
            # and calculate wavelength
            wavelength = self.hcOverE / self.__energy
            wavelengthStr = "%.4f" % wavelength
            self.waveLengthLineEdit.setText(wavelengthStr + " Angstrom")


class EnterEnergy(Qt.QDialog):


    def __init__(self, pParent):
        self.__parent = pParent
        self.__parent.energyDialogOpen()

        Qt.QDialog.__init__(self, self.__parent.brick_widget)
        self.resize(300, 30)


        self.setWindowTitle("New Energy in keV")
        self.setLayout(Qt.QHBoxLayout())
        self.hBox3Layout = Qt.QHBoxLayout()
        self.newEnergyLineEdit = Qt.QLineEdit(self)
        self.newEnergyLineEdit.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.newEnergyLineEdit.setToolTip("New Energy")
        Qt.QObject.connect(self.newEnergyLineEdit, Qt.SIGNAL("editTextChanged(const QString &)"), self.newEnergySet)
        Qt.QObject.connect(self.newEnergyLineEdit, Qt.SIGNAL("returnPressed()"), self.newEnergySet)
        self.hBox3Layout.addWidget(self.newEnergyLineEdit)


        self.setPushButton = Qt.QPushButton("Set Energy", self)
        Qt.QObject.connect(self.setPushButton, Qt.SIGNAL("clicked()"), self.newEnergySet)
        self.hBox3Layout.addWidget(self.setPushButton)

        self.cancelPushButton = Qt.QPushButton("Cancel", self)
        Qt.QObject.connect(self.cancelPushButton, Qt.SIGNAL("clicked()"), self.cancelClicked)
        self.hBox3Layout.addWidget(self.cancelPushButton)

        self.layout().addLayout(self.hBox3Layout)

    def cancelClicked(self):
        self.newEnergyLineEdit.setText("")
        self.__parent.energyDialogClose()
        self.accept()

    def newEnergySet(self):
        try:
            float(self.newEnergyLineEdit.text())
        except ValueError:
            Qt.QMessageBox.critical(self, "Warning", "Please enter a number in keV", Qt.QMessageBox.Ok)
            return
        newEnergy = float(self.newEnergyLineEdit.text())
        if self.isEnergyOK(newEnergy):
            newEnergyStr = "%.4f" % newEnergy
            self.__parent.setEnergy(newEnergyStr)
            self.newEnergyLineEdit.setText("")
            self.__parent.energyDialogClose()
            self.accept()
        else:
            Qt.QMessageBox.critical(self, "Warning", "Only Energies between 7 and 15 keV", Qt.QMessageBox.Ok)

    def isEnergyOK(self, energy):
        if energy < 7.0 or energy > 15.0 :
            return False
        else:
            return True

class EnterWaveLength(Qt.QDialog):


    def __init__(self, pParent):
        # The keV to Angstrom calc
        self.hcOverE = 12.398
        self.__parent = pParent
        self.__parent.waveLengthDialogOpen()

        Qt.QDialog.__init__(self, self.__parent.brick_widget)
        self.resize(300, 30)


        self.setWindowTitle("New Wavelength in A")
        self.setLayout(Qt.QHBoxLayout())
        self.hBox3Layout = Qt.QHBoxLayout()
        self.newWaveLengthLineEdit = Qt.QLineEdit(self)
        self.newWaveLengthLineEdit.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.newWaveLengthLineEdit.setToolTip("New Wavelength")
        Qt.QObject.connect(self.newWaveLengthLineEdit, Qt.SIGNAL("editTextChanged(const QString &)"), self.newWaveLengthSet)
        Qt.QObject.connect(self.newWaveLengthLineEdit, Qt.SIGNAL("returnPressed()"), self.newWaveLengthSet)
        self.hBox3Layout.addWidget(self.newWaveLengthLineEdit)


        self.setPushButton = Qt.QPushButton("Set WaveLength", self)
        Qt.QObject.connect(self.setPushButton, Qt.SIGNAL("clicked()"), self.newWaveLengthSet)
        self.hBox3Layout.addWidget(self.setPushButton)

        self.cancelPushButton = Qt.QPushButton("Cancel", self)
        Qt.QObject.connect(self.cancelPushButton, Qt.SIGNAL("clicked()"), self.cancelClicked)
        self.hBox3Layout.addWidget(self.cancelPushButton)

        self.layout().addLayout(self.hBox3Layout)

    def cancelClicked(self):
        self.newWaveLengthLineEdit.setText("")
        self.__parent.waveLengthDialogClose()
        self.accept()

    def newWaveLengthSet(self):
        try:
            float(self.newWaveLengthLineEdit.text())
        except ValueError:
            Qt.QMessageBox.critical(self, "Warning", "Please enter a number in Angstrom", Qt.QMessageBox.Ok)
            return
        newWaveLength = float(self.newWaveLengthLineEdit.text())
        if self.isWaveLengthOK(newWaveLength):
            # set energy from wavelength
            newEnergy = self.hcOverE / newWaveLength
            newEnergyStr = "%.4f" % newEnergy
            self.__parent.setEnergy(newEnergyStr)
            self.newWaveLengthLineEdit.setText("")
            self.__parent.waveLengthDialogClose()
            self.accept()
        else:
            Qt.QMessageBox.critical(self, "Warning", "Only Wavelengths between 0.83 A and 1.77 A [7-15 keV]", Qt.QMessageBox.Ok)

    def isWaveLengthOK(self, wavelength):
        if wavelength < 0.83 or wavelength > 1.77:
            return False
        else:
            return True
