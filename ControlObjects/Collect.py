"""
=============================================
  NAME       : Collect Control Object (Collect.py)
  
  DESCRIPTION:
    
  VERSION    : 1

  REVISION   : 0

  RELEASE    : 2010/MAR/01

  PLATFORM   : Bliss Framework 4

  EMAIL      : ricardo.fernandes@esrf.fr
  
  HISTORY    :
=============================================
"""


# =============================================
#  IMPORT MODULES
# =============================================
from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot    
import logging


# =============================================
#  CLASS DEFINITION
# =============================================
class Collect(CObjectBase):
    


    __CHANNEL_LIST = ["collectDirectoryChanged",
                     "collectPrefixChanged",
                     "collectRunNumberChanged",
                     "collectNumberFramesChanged",
                     "collectTimePerFrameChanged",
                     "collectConcentrationChanged",
                     "collectCommentsChanged",
                     "collectCodeChanged",
                     "collectMaskFileChanged",
                     "collectDetectorDistanceChanged",
                     "collectWaveLengthChanged",
                     "collectPixelSizeXChanged",
                     "collectPixelSizeYChanged",
                     "collectBeamCenterXChanged",
                     "collectBeamCenterYChanged",
                     "collectNormalisationChanged",
                     "collectProcessDataChanged",
                     "collectNewFrameChanged",
                     "checkBeamChanged",
                     "beamLostChanged",
                     "abortCollectChanged"]
    


    # =============================================
    #  SIGNALS/SLOTS DEFINITION
    # =============================================
    signals = [Signal(channel) for channel in __CHANNEL_LIST]                   
    
    slots = [Slot("testCollect"),
             Slot("collect"),
             Slot("collectAbort"),
             Slot("setCheckBeam")]

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
    def testCollect(self, pDirectory, pPrefix, pRunNumber, pConcentration, pComments, pCode, pMaskFile, pDetectorDistance, pWaveLength, pPixelSizeX, pPixelSizeY, pBeamCenterX, pBeamCenterY, pNormalisation):
        self.collectDirectory.set_value(pDirectory)
        self.collectPrefix.set_value(pPrefix)
        self.collectRunNumber.set_value(pRunNumber)
        self.collectConcentration.set_value(pConcentration)
        self.collectComments.set_value(pComments)
        self.collectCode.set_value(pCode)
        self.collectMaskFile.set_value(pMaskFile)
        self.collectDetectorDistance.set_value(pDetectorDistance)
        self.collectWaveLength.set_value(pWaveLength)
        self.collectPixelSizeX.set_value(pPixelSizeX)
        self.collectPixelSizeY.set_value(pPixelSizeY)        
        self.collectBeamCenterX.set_value(pBeamCenterX)
        self.collectBeamCenterY.set_value(pBeamCenterY)
        self.collectNormalisation.set_value(pNormalisation)                       
        self.commands["testCollect"]()

    def collect(self, pDirectory, pPrefix, pRunNumber, pNumberFrames, pTimePerFrame, pConcentration, pComments, pCode, pMaskFile, pDetectorDistance, pWaveLength, pPixelSizeX, pPixelSizeY, pBeamCenterX, pBeamCenterY, pNormalisation, pProcessData):
        self.collectDirectory.set_value(pDirectory)
        self.collectPrefix.set_value(pPrefix)
        self.collectRunNumber.set_value(pRunNumber)
        self.collectNumberFrames.set_value(pNumberFrames)
        self.collectTimePerFrame.set_value(pTimePerFrame)
        self.collectConcentration.set_value(pConcentration)
        self.collectComments.set_value(pComments)
        self.collectCode.set_value(pCode)
        self.collectMaskFile.set_value(pMaskFile)
        self.collectDetectorDistance.set_value(pDetectorDistance)
        self.collectWaveLength.set_value(pWaveLength)
        self.collectPixelSizeX.set_value(pPixelSizeX)
        self.collectPixelSizeY.set_value(pPixelSizeY)        
        self.collectBeamCenterX.set_value(pBeamCenterX)
        self.collectBeamCenterY.set_value(pBeamCenterY)
        self.collectNormalisation.set_value(pNormalisation)
        self.collectProcessData.set_value(pProcessData)                  
        self.commands["collect"]()
        
    def collectAbort(self):
        logging.info("sending abort to stop spec collection")
        self.abortCollect.set_value(1)

        #self.commands["collect"].abort()

    def testCollectAbort(self):
        logging.info("sending abort to stop spec test collection")
        self.abortCollect.set_value(1)

        #self.commands["testCollect"].abort()

    def setCheckBeam(self, flag):
        logging.info("changing check beam in spec to %s" % flag) 
        if flag:
           self.checkBeam.set_value(1)
        else:
           self.checkBeam.set_value(0)

    # =============================================
    #  CHANNELS
    # =============================================
    def abortCollectChanged(self, pValue):
        self.emit("abortCollectChanged", pValue)

    def checkBeamChanged(self, pValue):
        self.emit("checkBeamChanged", pValue)

    def collectDirectoryChanged(self, pValue):
        self.emit("collectDirectoryChanged", pValue)
      
    def collectPrefixChanged(self, pValue):
        self.emit("collectPrefixChanged", pValue)
        
    def collectRunNumberChanged(self, pValue):
        self.emit("collectRunNumberChanged", pValue)
        
    def collectNumberFramesChanged(self, pValue):
        self.emit("collectNumberFramesChanged", pValue)

    def collectTimePerFrameChanged(self, pValue):
        self.emit("collectTimePerFrameChanged", pValue)        

    def collectConcentrationChanged(self, pValue):
        self.emit("collectConcentrationChanged", pValue)        

    def collectCommentsChanged(self, pValue):
        self.emit("collectCommentsChanged", pValue)        
                
    def collectCodeChanged(self, pValue):
        self.emit("collectCodeChanged", pValue)        

    def collectMaskFileChanged(self, pValue):
        self.emit("collectMaskFileChanged", pValue)

    def collectDetectorDistanceChanged(self, pValue):
        self.emit("collectDetectorDistanceChanged", pValue)        

    def collectWaveLengthChanged(self, pValue):
        self.emit("collectWaveLengthChanged", pValue)

    def collectPixelSizeXChanged(self, pValue):
        self.emit("collectPixelSizeXChanged", pValue)        

    def collectPixelSizeYChanged(self, pValue):
        self.emit("collectPixelSizeYChanged", pValue)        
                                
    def collectBeamCenterXChanged(self, pValue):
        self.emit("collectBeamCenterXChanged", pValue)        

    def collectBeamCenterYChanged(self, pValue):
        self.emit("collectBeamCenterYChanged", pValue)
        
    def collectNormalisationChanged(self, pValue):
        self.emit("collectNormalisationChanged", pValue)        

    def collectProcessDataChanged(self, pValue):
        self.emit("collectProcessDataChanged", pValue)        
                                                      
    def collectNewFrameChanged(self, pValue):
        self.emit("collectNewFrameChanged", pValue)

    def beamLostChanged(self, pValue):
        self.emit("beamLostChanged", pValue)
