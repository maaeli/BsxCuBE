from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot

class Shutter(CObjectBase):
    signals = [Signal('statusChanged'),
               Signal('stateChanged')]

    slots = [ Slot("open"), Slot("close") ]

    # TACO Shutterstate
#    shutterState = {
#        0: 'unknown',
#        3: 'closed',
#        4: 'opened',
#        9: 'moving',
#        17: 'automatic',
#        23: 'fault',
#        46: 'disabled',
#        - 1: 'error'
#    }

    # Tango Shutterstate
    shutterState = {
        0: 'on',
        1: 'off',
        2: 'closed',
        3: 'opened',
        4: 'insert',
        5: 'extract',
        6: 'moving',
        7: 'standby',
        8: 'fault',
        9: 'init',
        10: 'running',
        11: 'alarm',
        12: 'disabled',
        13: 'unknown',
        - 1: 'error'
    }

    def __init__(self, *args, **kwargs):
        CObjectBase.__init__(self, *args, **kwargs)


    def init(self):
        self.shutter_state = "unknown"
        self.channels["state"].connect("update", self.stateChanged)
        self.channels["status"].connect("update", self.statusChanged)

    def open(self):
        self.commands['open']()

    def close(self):
        self.commands['close']()

    def statusChanged(self, status):
        self.emit("statusChanged", status)

    def stateChanged(self, state):
        self.shutter_state = Shutter.shutterState.get(int(state), "unknown")
        self.emit("stateChanged", self.shutter_state)
