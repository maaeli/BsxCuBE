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
        print "Got new value of Energy %d" % pValue
        self.emit("energyChanged", pValue)

    def setEnergy(self, pValue):
        print "Should set energy to %s" % pValue

    def getEnergy(self):
        print "Asked to get Energy"

