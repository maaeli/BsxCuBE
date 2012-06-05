import logging
import math
from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot


class EnergyWaveLength(CObjectBase):

    signals = [Signal("energyChanged")]

    slots = [Slot("setEnergy"), Slot("getEnergy"), Slot("pilatusReady")]

    def __init__(self, *args, **kwargs):
        CObjectBase.__init__(self, *args, **kwargs)
        # Threshold in keV (to change the sensitivity)
        self.__pilatusThreshold = 12.00

    def init(self):
        # The keV to Angstrom calc
        self.hcOverE = 12.398
        self.deltaPilatus = 0.1
        # check that we have connection to Pilatus
        self.pilatusThreshold = self.channels.get("pilatus_threshold")
        if  self.pilatusThreshold is None:
            logging.error("No connection to Pilatus")
        # Runnning = Nothing should be possible
        self.__pilatus_status = "Running"
        # get spec motor as described in href and the corresponding energy.xml
        self.__energyMotor = self.objects["getEnergy"]
        if self.__energyMotor is not None:
            # connect to the signals from the CO Object specmotor
            self.__energyMotor.connect("positionChanged", self.newEnergy)
        else:
            logging.error("No connection to energy motor in spec")


    def newEnergy(self, pValue):
        self.__energy = float(pValue)
        # Calculate wavelength
        wavelength = self.hcOverE / self.__energy
        wavelengthStr = "%.4f" % wavelength
        # set value of BSX_GLOBAL
        self.channels["collectWaveLength"].set_value(wavelengthStr)
        self.emit("energyChanged", pValue)
        # if in movement already, just return....
        if not self.pilatusReady():
            return
        self.__currentPilatusThreshold = float(self.channels["pilatus_threshold"].value())
        if math.fabs(self.__energy - self.__currentPilatusThreshold) > self.deltaPilatus:
            self.pilatusThreshold.set_value(self.__energy)

    def getEnergy(self):
        return self.__energyMotor.position()

    def setEnergy(self, pValue):
        self.__energy = float(pValue)
        self.commands["setEnergy"](self.__energy)
        # Check if we need and can set new Energy on Pilatus first.
        self.__currentPilatusThreshold = float(self.channels["pilatus_threshold"].value())
        if math.fabs(self.__energy - self.__currentPilatusThreshold) > self.deltaPilatus:
            self.pilatusThreshold.set_value(self.__energy)


    def pilatusReady(self):
        # Check if Pilatus is ready
        self.__pilatus_status = self.channels["pilatus_status"].value()
        if self.__pilatus_status == "Ready":
            return True
        else:
            return False
