from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot


class Browse(CObjectBase):

    signals = [Signal("browseTypeChanged"), Signal("browseLocationChanged")]

    slots = []


    def __init__(self, *args, **kwargs):
        CObjectBase.__init__(self, *args, **kwargs)



    def init(self):
        self.channels["browseType"].connect("update", self.browseLocationChanged)
        self.channels["browseLocation"].connect("update", self.browseTypeChanged)

    def browseTypeChanged(self, pValue):
        self.emit("browseTypeChanged", pValue)

    def browseLocationChanged(self, pValue):
        self.emit("browseLocationChanged", pValue)
