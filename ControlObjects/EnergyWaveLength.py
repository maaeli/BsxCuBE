import logging
import math
import time
from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot


class EnergyWaveLength(CObjectBase):

    signals = [Signal("energyChanged")]

    slots = [Slot("setEnergy"), Slot("getEnergy"), Slot("pilatusReady"), Slot("setPilatusFill")]

    def __init__(self, *args, **kwargs):
        CObjectBase.__init__(self, *args, **kwargs)
        # Threshold in keV (to change the sensitivity)
        self.__pilatusThreshold = 12.00

    def init(self):
        # The keV to Angstrom calc
        self.hcOverE = 12.3984
        self.deltaPilatus = 0.1
        # check that we have connection to Pilatus
        self.pilatusThreshold = self.channels.get("pilatus_threshold")
        if  self.pilatusThreshold is None:
            logging.error("No connection to Pilatus")
        # Runnning = Nothing should be possible
        self.__pilatus_status = "Running"
        # make another connection
        self.pilatusFillMode = self.channels.get("fill_mode")
        # get spec motor as described in href and the corresponding energy.xml
        self.__energyMotor = self.objects["getEnergy"]
        if self.__energyMotor is not None:
            # connect to the signals from the CO Object specmotor
            self.__energyMotor.connect("positionChanged", self.newEnergy)
        else:
            logging.error("No connection to energy motor in spec")
        # Connect to fill_mode and correct it back each time it changes
        self.channels["fill_mode"].connect("update", self.fillModeChanged)


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

    def fillModeChanged(self, pValue):
        # read value first
        mode = self.pilatusFillMode.value()
        if mode != "ON" :
            # Here we have a problem.. Wait until pilatus has settled and then act
            while not self.pilatusReady() :
                time.sleep(0.5)
            self.setPilatusFill()

    def setPilatusFill(self):
        # Just for safety set fill mode to ON => gapfill -1
        self.pilatusFillMode.set_value("ON")

    def pilatusReady(self):
        # Check if Pilatus is ready
        self.__pilatus_status = self.channels["pilatus_status"].value()
        if self.__pilatus_status == "Ready":
            return True
        else:
            return False
