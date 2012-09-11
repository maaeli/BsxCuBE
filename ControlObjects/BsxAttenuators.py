from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot
import logging

class BsxAttenuators(CObjectBase):

    signals = [Signal("attenuatorsStateChanged"),
               Signal("attenuatorsFactorChanged")]

    slots = [Slot("toggleFilter"),
             Slot("setTransmission")]


    def __init__(self, *args, **kwargs):
        CObjectBase.__init__(self, *args, **kwargs)

    def init(self):
        self.__attenuatorsState = None
        self.__attenuatorsFactor = None
        self.__attenuatorsList = []
        for data_elt in self.config["//data"]:
            key = data_elt.attrib["name"]
            bits = map(int, data_elt.attrib['bits'].split())
            for b in bits:
                self.__attenuatorsList.append([key, b])
        # the list contains [label, bits] lists
        # sort by bits
        self.__attenuatorsList.sort(key = lambda x: x[1])

        # Set up all channels
        self.channels["attenuatorsState_oh"].connect("update", self.attenuatorsStateChanged)
        self.channels["attenuatorsState_exp"].connect("update", self.attenuatorsStateChanged)
        self.channels["attenuatorsFactor_oh"].connect("update", self.attenuatorsFactorChanged)
        self.channels["attenuatorsFactor_exp"].connect("update", self.attenuatorsFactorChanged)



    def connectNotify(self, pValue):
        try:
            value = getattr(self, pValue[:-7]).value()
            getattr(self, pValue)(value)
        except:
            pass




    def getAttenuatorsList(self):
        logging.getLogger().debug('is sending attribute list %s', self.__attenuatorsList)
        if len(self.__attenuatorsList) == 0:
            return None
        else:
            return self.__attenuatorsList


    def getAttenuatorsState(self):
        self.__attenuatorsState = self.channels["attenuatorsState_oh"].value()
        return self.__attenuatorsState

    def getAttenuatorsFactor(self):
        self.__attenuatorsFactor = self.channels["attenuatorsFactor_oh"].value()
        return self.__attenuatorsFactor



    # =============================================
    #  COMMANDS
    # =============================================      
    def toggleFilter(self, pValue):
        self.commands["toggleFilter"](pValue)


    def setTransmission(self, pValue):
        self.commands["setTransmission"](pValue)




    # =============================================
    #  CHANNELS
    # =============================================    
    def attenuatorsStateChanged(self, pValue):
        self.__attenuatorsState = int(pValue)
        self.emit("attenuatorsStateChanged", self.__attenuatorsState)


    def attenuatorsFactorChanged(self, pValue):
        self.__attenuatorsFactor = int(pValue)
        self.emit("attenuatorsFactorChanged", self.__attenuatorsFactor)



