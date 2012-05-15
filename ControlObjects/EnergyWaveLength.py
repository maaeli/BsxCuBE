from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot


class EnergyWaveLength(CObjectBase):

    signals = [Signal("energyChanged")]

    slots = [Slot("setEnergy"), Slot("getEnergy")]


    def __init__(self, *args, **kwargs):
        CObjectBase.__init__(self, *args, **kwargs)



    def init(self):
        # set up connection to Spec motor energy

        # get spec motor as described in href and the corresponding energy.xml
        self.__energy = self.objects["getEnergy"]
        # connect to the signals from the CO Object specmotor
        self.__energy.connect("positionChanged", self.newEnergy)

    def newEnergy(self, pValue):
        self.emit("energyChanged", pValue)

    def setEnergy(self, pValue):
        self.commands["setEnergy"](pValue)

    def getEnergy(self):
        print "Asked to get Energy"
        return self.__energy.position()

