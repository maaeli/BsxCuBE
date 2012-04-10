import types
from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot    



# =============================================
#  CLASS DEFINITION
# =============================================
class Reading(CObjectBase):


    __CHANNEL_LIST = ["readingChanged"]
    


    # =============================================
    #  SIGNALS/SLOTS DEFINITION
    # =============================================
    signals = [Signal(channel) for channel in __CHANNEL_LIST]                   
        
    slots = []



    # =============================================
    #  CONSTRUCTOR
    # =============================================    
    def __init__(self, *args, **kwargs):
        CObjectBase.__init__(self, *args, **kwargs)




    def init(self):
        for channel in self.__CHANNEL_LIST:
            try:
                value = self.channels.get(channel[:-7])
                setattr(self, channel[:-7], value)
                if value is not None:
                    getattr(self, channel[:-7]).connect("update", getattr(self, channel))
            except:
                logging.getLogger.exception('unable to connect update signal for channel')
                       

    def connectNotify(self, pValue):
        try:
            value = getattr(self, pValue[:-7]).value()
            getattr(self, pValue)(value)
        except:
            pass
        


    
    # =============================================
    #  COMMANDS
    # =============================================      



    # =============================================
    #  CHANNELS
    # =============================================
    def readingChanged(self, pValue):
        if type(pValue) == types.ListType or type(pValue) == types.TupleType:
            self.emit("readingChanged", pValue[0])
        else:
            self.emit("readingChanged", pValue)
                
      


