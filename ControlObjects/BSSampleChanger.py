import logging
from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot
from PyTango import DevState

class BSSampleChanger(CObjectBase):
    signals = [Signal('seuTemperatureChanged')
               , Signal('storageTemperatureChanged')
               , Signal('stateChanged')
               ]

    def __init__(self, *args, **kwargs):
        CObjectBase.__init__(self, *args, **kwargs)

        #
        # this is not used.  it is just a list of things
        #
        self.__channels = ["Status", "AlarmList", "BeamLocation",
                           "BeamMarkVolume", "BeamShapeEllipse", "CleanVenturiOK",
                           "CollisionDetected", "CommandException", "CommandOutput",
                           "CoverOpen", "CurrentLiquidPosition", "DetergentEmpty",
                           "Flooding", "OverflowVenturiOK", "PlateID",
                           "PLCState", "HardwareInitPending", "Power12OK",
                           "SampleType", "TemperatureSampleStorage", "TemperatureSEU",
                           "LocalLockout", "State", "VacuumOK",
                           "ViscosityLevel", "WasteFull", "WaterEmpty",
                           "LiquidPositionFixed"]

        # The target user-entered temperature
        self.__target_temperature = None

    def init(self):
        self.current_status = self.current_state = 'Not Available'
        self.channels['State'].connect('update', self.state_changed)
        self.channels['Status'].connect('update', self.status_changed)
        self.channels['BeamLocation'].connect('update', self.beamlocation_changed)

    def state_changed(self, state):
        self.current_state = str(state)
        self.emit('stateChanged', self.current_state, self.current_status)

    def status_changed(self, status):
        self.current_status = str(status)
        self.emit('stateChanged', self.current_state, self.current_status)

    def beamlocation_changed(self, beamlocation):
        self.beam_location = self.getBeamLocation()
        self.emit('beamLocationChanged', self.beam_location)

    def setBeamLocation(self, x1, y1, x2, y2):
        self.channels["BeamLocation"] = "%d %d %d %d" % (x1, y1, x2, y2)

    #
    # We should not need to use this from the Brick. We should just connect to beamLocationChanged
    #
    def getBeamLocation(self):
        beam = self.channels["BeamLocation"].value()
        try:
             beamLocation = map(int, beam.strip().split())
             return beamLocation
        except:
             return None

    def setBeamMark(self, x1, y1, x2, y2, is_ellipse):
        self.setBeamLocation(x1, y1, x2, y2)
        self.channels["BeamShapeEllipse"].set_value(is_ellipse)

    def setLiquidPositionFixed(self, fixed):
        self.channels["LiquidPositionFixed"].set_value(fixed)

    def setSampleType(self, sample_type):
        self.channels["SampleType"].set_value(sample_type)

    def setSEUTemperature(self, temp):
        self.channels["SEUTemperature"].set_value(temp)

    def setStorageTemperature(self, temp):
        self.channels["TemperatureSampleStorage"].set_value(temp)

    def setViscosityLevel(self, level):
        self.channels["ViscosityLevel"].set_value(level)

    def fill(self, plate, row, column, volume):
        self.commands['fill'](map(str, (plate, row, column, volume)))

    def flow(self, volume, t):
        self.commands['flow'](map(str, (volume, t)))

    def recuperate(self, *args):
        self.commands['recuperate'](map(str, args))

    def mix(self, *args):
        self.commands['mix'](map(str, args))

    def transfer(self, *args):
        self.commands['transfer'](map(str, args))

    def isExecuting(self):
        state = self.getState()
        if state:
           return (state != DevState.STANDBY)
        else:
           return False

