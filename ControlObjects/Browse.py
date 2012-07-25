from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot


class Browse(CObjectBase):

    signals = []

    slots = []


    def __init__(self, *args, **kwargs):
        CObjectBase.__init__(self, *args, **kwargs)



    def init(self):
        # Do nothing for now
        pass
