from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot



class Browse(CObjectBase):


    __CHANNEL_LIST = ["browseTypeChanged",
                     "browseLocationChanged"]


    signals = [Signal(channel) for channel in __CHANNEL_LIST]

    slots = []




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

    def browseTypeChanged(self, pValue):
        print "emitting"
        self.emit("browseTypeChanged", pValue)
        print "ok"

    def browseLocationChanged(self, pValue):
        self.emit("browseLocationChanged", pValue)





