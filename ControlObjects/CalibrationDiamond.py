"""
=============================================
  NAME       : Calibration Diamond Control Object (CalibrationDiamond.py)
  
  DESCRIPTION:
    
  VERSION    : 1

  REVISION   : 0

  RELEASE    : 2010/ABR/14

  PLATFORM   : Bliss Framework 4

  EMAIL      : ricardo.fernandes@esrf.fr
  
  HISTORY    :
=============================================
"""




# =============================================
#  IMPORT MODULES
# =============================================
try:
    from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot    
except ImportError:
    print "%s.py: error when importing module!" % __name__




# =============================================
#  CLASS DEFINITION
# =============================================
class CalibrationDiamond(CObjectBase):


    __CHANNEL_LIST = ["calibrationStatusChanged",
                      "newPositionChanged"]
    


    # =============================================
    #  SIGNALS/SLOTS DEFINITION
    # =============================================
    signals = [Signal(channel) for channel in __CHANNEL_LIST]                
        
    slots = [Slot("executeCalibration"),
             Slot("setPosition")]



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
                pass

    # =============================================
    #  COMMANDS
    # =============================================      
    def executeCalibration(self, pValue):
        if pValue == "":
            self.commands["executeCalibration"]()
        else:
            self.commands["executeCalibration"](pValue)


    def setPosition(self, pValue):
        self.commands["setPosition"](pValue)



    # =============================================
    #  CHANNELS
    # =============================================
    def calibrationStatusChanged(self, pValue):
        self.emit("calibrationStatusChanged", pValue)

                
    def newPositionChanged(self, pValue):
        self.emit("newPositionChanged", pValue)
      

