from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot    
import logging

class Attenuators(CObjectBase):
    __CHANNEL_LIST = ["attenuatorsStateChanged",
                     "attenuatorsFactorChanged"]

    signals = [Signal(channel) for channel in __CHANNEL_LIST]                   
    
    slots = [Slot("toggleFilter"),
             Slot("setTransmission")]


    def __init__(self, *args, **kwargs):
        CObjectBase.__init__(self, *args, **kwargs)

    def init(self):
        self.__attenuatorsState = None
        self.__attenuatorsList = []
        for data_elt in self.config["//data"]:
          key = data_elt.attrib["name"]
       	  bits = map(int, data_elt.attrib['bits'].split())
          for b in bits:
             self.__attenuatorsList.append([key, b])
        # the list contains [label, bits] lists
	# sort by bits
        self.__attenuatorsList.sort(key=lambda x: x[1])
        
        for channel in self.__CHANNEL_LIST:
            try:
                value = self.channels.get(channel[:-7])
                setattr(self, channel[:-7], value)
                if value is not None:
                    getattr(self, channel[:-7]).connect("update", getattr(self, channel))
            except:
                pass



    def connectNotify(self, pValue):
        try:
            value = getattr(self, pValue[:-7]).value()
            getattr(self, pValue)(value)
        except:
            pass
        
        


    def getAttenuatorsList(self):
        logging.getLogger().debug('isending att list %s', self.__attenuatorsList)
        if len(self.__attenuatorsList) == 0:
            return None
        else:
            return self.__attenuatorsList
    

    def getAttenuatorsState(self):
        return self.__attenuatorsState



    
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
        self.emit("attenuatorsFactorChanged", pValue)
        


