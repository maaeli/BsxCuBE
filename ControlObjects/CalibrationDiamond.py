import logging
from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot

class CalibrationDiamond(CObjectBase):
    __CHANNEL_LIST = ["calibrationStatusChanged", "newPositionChanged"]


    signals = [Signal(channel) for channel in __CHANNEL_LIST]

    slots = [Slot("executeCalibration"),
             Slot("setPosition")]



    def __init__(self, *args, **kwargs):
        CObjectBase.__init__(self, *args, **kwargs)



    def init(self):
        for channel in self.__CHANNEL_LIST:
            try:
                value = self.channels.get(channel[:-7])
                setattr(self, channel[:-7], value)
                if value is not None:
                    getattr(self, channel[:-7]).connect("update", getattr(self, channel))
            except Exception, e:
                logging.getLogger().error("Ignored Exception: " + e)

    def executeCalibration(self, pValue):
        if pValue == "":
            self.commands["executeCalibration"]()
        else:
            self.commands["executeCalibration"](pValue)


    def setPosition(self, pValue):
        self.commands["setPosition"](pValue)



    def calibrationStatusChanged(self, pValue):
        self.emit("calibrationStatusChanged", pValue)


    def newPositionChanged(self, pValue):
        self.emit("newPositionChanged", pValue)


