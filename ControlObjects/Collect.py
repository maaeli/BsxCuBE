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

class Collect(CObjectBase):
    slots = [Slot("testCollect"),
             Slot("collect"),
             Slot("collectAbort"),
             Slot("setCheckBeam")]

    def __init__(self, *args, **kwargs):
        CObjectBase.__init__(self, *args, **kwargs)

    def __getattr__(self, attr):
        if not attr.startswith("__"):
          try:
             return self.channels[attr]
          except KeyError:
              pass
        raise AttributeError, attr

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
            self.channels["checkBeam"].set_value(1)
        else:
            self.channels["checkBeam"].set_value(0)

    # overwrite connectNotify ; first values will be read by brick
    def connectNotify(self, signal_name):
        pass

    def updateChannels(self):
        for channel_name, channel in self.channels.iteritems():
            channel.update(channel.value())
