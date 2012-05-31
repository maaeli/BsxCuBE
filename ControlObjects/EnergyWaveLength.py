from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot


class EnergyWaveLength(CObjectBase):

    signals = [Signal("energyChanged")]

    slots = [Slot("setEnergy"), Slot("getEnergy")]

    def __init__(self, *args, **kwargs):
        CObjectBase.__init__(self, *args, **kwargs)



    def init(self):
        # The keV to Angstrom calc
        self.hcOverE = 12.398
        # set up connection to Spec motor energy
        # get spec motor as described in href and the corresponding energy.xml
        self.__energyMotor = self.objects["getEnergy"]
        # connect to the signals from the CO Object specmotor
        self.__energyMotor.connect("positionChanged", self.newEnergy)

    def newEnergy(self, pValue):
        self.__energy = float(pValue)
        # Calculate wavelength
        wavelength = self.hcOverE / self.__energy
        wavelengthStr = "%.4f" % wavelength
        # set value of BSX_GLOBAL
        self.channels["collectWaveLength"].set_value(wavelengthStr)
        self.emit("energyChanged", pValue)

    def setEnergy(self, pValue):
        self.commands["setEnergy"](pValue)

    def getEnergy(self):
        return self.__energyMotor.position()

