from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot
import logging

class VacPump(CObjectBase):

    signals = []

    slots = [Slot("exftclose"), Slot("exscclose"), Slot("vacftclose"), Slot("vacscclose"), Slot("vacftopen"), Slot("vacscopen"), Slot("rv5open"), Slot("rv6open"),
             Slot("getValveThreshold"), Slot("getPumpThreshold"), Slot("getUSThreshold"), Slot("getFTTimeout"), Slot("getSCTimeout"),
             Slot("getFTVacuum"), Slot("getSCVacuum"), Slot("getUSVacuum")]




    def __init__(self, *args, **kwargs):
        CObjectBase.__init__(self, *args, **kwargs)

    def init(self):
        pass

    def exftclose(self):
        self.commands["exftclose"]()

    def exscclose(self):
        self.commands["exscclose"]()

    def vacftclose(self):
        self.commands["vacftclose"]()

    def vacscclose(self):
        self.commands["vacscclose"]()

    def vacftopen(self):
        self.commands["vacftopen"]()

    def vacscopen(self):
        self.commands["vacscopen"]()

    def rv5open(self):
        self.commands["rv5open"]()

    def rv6open(self):
        self.commands["rv6open"]()

    def getValveThreshold(self):
        channel = self.channels.get("valveThreshold")
        if channel is None:
            logging.error("Tried and failed to connect to EXP spec session")
            return 0
        else:
            return self.channels.get("valveThreshold").value()

    def getPumpThreshold(self):
        channel = self.channels.get("pumpThreshold")
        if channel is None:
            logging.error("Tried and failed to connect to EXP spec session")
            return 0
        else:
            return self.channels.get("pumpThreshold").value()

        #DEBUG
        # TODO 
    def getUSThreshold(self):
        return self.channels.get("usThreshold").value()

    def getFTTimeout(self):
        return self.channels.get("ftTimeout").value()

    def getSCTimeout(self):
        return self.channels.get("scTimeout").value()

    def getFTVacuum(self):
        return self.channels.get("FTVacuum").value()

    def getSCVacuum(self):
        return self.channels.get("SCVacuum").value()

    def getUSVacuum(self):
        return self.channels.get("USVacuum").value()
