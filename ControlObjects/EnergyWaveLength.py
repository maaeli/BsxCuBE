import logging
from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot


class EnergyWaveLength(CObjectBase):

    signals = [Signal("energyChanged")]

    slots = [Slot("setEnergy"), Slot("getEnergy")]

    def __init__(self, *args, **kwargs):
        CObjectBase.__init__(self, *args, **kwargs)
        # Threshold in keV (to change the sensitivity)
        self.__pilatusThreshold = 12.00
        # get Pilatusdevice from config file
        # <data name="uri"  value="bm29/pilatus/p0" />
        self.pilatusDevName = str(self.config["/object/data[@name='uri']/@value"][0])
        # add a channel to read the Threshold constaqntly
        self.addChannel('tango',
                        'pilatus_threshold',
                        self.pilatusDevName,
                        'energy_threshold',
                        polling = 3000)
        # get threshold constantly
        self.pilatusThreshold = self.channels.get("pilatus_threshold")
        if  self.pilatusThreshold is not None:
            self.connect('update', self.pilatusThresholdChanged)
        else:
            logging.error("No connection to Pilatus")

        self.addChannel('tango',
                        'pilatus_threshold',
                        self.pilatusDevName,
                        'energy_threshold',
                        polling = 3000)


    def init(self):
        # The keV to Angstrom calc
        self.hcOverE = 12.398
        # set up connection to Spec motor energy
        # get spec motor as described in href and the corresponding energy.xml
        self.__energyMotor = self.objects["getEnergy"]
        if self.__energyMotor is not None:
            # connect to the signals from the CO Object specmotor
            self.__energyMotor.connect("positionChanged", self.newEnergy)
        else:
            logging.error("No connection to energy motor in spec")


    def newEnergy(self, pValue):
        self.__energy = float(pValue)
        self.pilatusThreshold.set_value(self.__energy)
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

    def pilatusThresholdChanged(self, pValue):
        print "New Threshold"
        self.__pilatusThreshold = pValue
        print pValue
        print type(pValue)
