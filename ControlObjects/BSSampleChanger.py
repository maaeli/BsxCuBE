import logging
import time
from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot

class BSSampleChanger(CObjectBase):
    signals = [Signal('seuTemperatureChanged')
               , Signal('storageTemperatureChanged')
               , Signal('stateChanged')
               ]

    def __init__(self, *args, **kwargs):
        CObjectBase.__init__(self, *args, **kwargs)


        # Usable channels:
        # "Status", "AlarmList", "BeamLocation",
        # "BeamMarkVolume", "BeamShapeEllipse", "CleanVenturiOK",
        # "CollisionDetected", "CommandException", "CommandOutput",
        # "CoverOpen", "CurrentLiquidPosition", "DetergentEmpty",
        # "Flooding", "OverflowVenturiOK", "PlateID",
        # "PLCState", "HardwareInitPending", "Power12OK",
        # "SampleType", "TemperatureSampleStorage", "TemperatureSEU",
        # "LocalLockout", "State", "VacuumOK",
        # "ViscosityLevel", "WasteFull", "WaterEmpty",
        # "LiquidPositionFixed"

        # The target user-entered temperature
        self.__target_temperature = None

    def init(self):
        self.current_status = self.current_state = 'Not Available'
        self.channels['State'].connect('update', self.stateChanged)
        self.channels['Status'].connect('update', self.statusChanged)
        self.channels['BeamLocation'].connect('update', self.beamlocationChanged)

    def stateChanged(self, state):
        self.current_state = str(state)
        self.emit('stateChanged', self.current_state, self.current_status)

    def statusChanged(self, status):
        self.current_status = str(status)
        self.emit('stateChanged', self.current_state, self.current_status)

    #TODO: SO - Why is beamlocation not used
    def beamlocationChanged(self, beamlocation):
        self.beam_location = self.getBeamLocation()
        self.emit('beamLocationChanged', self.beam_location)

    def setBeamLocation(self, x1, y1, x2, y2):
        self.channels["BeamLocation"] = "%d %d %d %d" % (x1, y1, x2, y2)

    #
    # We should not need to use this from the Brick. We should just connect to beamLocationChanged
    #
    def getBeamLocation(self):
        # beam is string
        beam = self.channels["BeamLocation"].value()
        try:
            beamLocation = map(int, beam.strip().split())
            return beamLocation
        except:
            return None

    def getState(self):
        # scState is _PyTango.DevState
        scState = self.channels["State"].value()
        return scState

    def getCommandException(self):
        scException = self.channels["CommandException"].value()
        return scException

    def setBeamMark(self, x1, y1, x2, y2, is_ellipse):
        self.setBeamLocation(x1, y1, x2, y2)
        self.channels["BeamShapeEllipse"].set_value(is_ellipse)

    def setLiquidPositionFixed(self, fixed):
        self.channels["LiquidPositionFixed"].set_value(fixed)

    def setSampleType(self, sample_type):
        self.channels["SampleType"].set_value(sample_type)

    def setSEUTemperature(self, temp):
        # Note that this has a timeout in the SC as X minutes/degrees
        self.commands["SEUTemperature"](temp)
        self.wait(7200)

    def setStorageTemperature(self, temp):
        # Note that this has a timeout in the SC as X minutes/degrees
        self.commands["TemperatureSampleStorage"](temp)
        self.wait(7200)

    def setViscosityLevel(self, level):
        self.channels["ViscosityLevel"].set_value(level)

    def setHPLCMode(self, hplc_mode):
        try:
            self.channels["ModeHPLC"].set_value(bool(hplc_mode))
        except:
            return False
        else:
            if not str(self.getState()) in ("STANDBY", "ON"):
              return False
            return True

    def fill(self, plate, row, column, volume):
        print ">>> fill ", plate, row, column, volume
        self.commands['fill'](map(str, (plate, row, column, volume)))

    def flow(self, volume, t):
        self.commands['flow'](map(str, (volume, t)))

    def recuperate(self, *args):
        self.commands['recuperate'](map(str, args))

    def mix(self, *args):
        self.commands['mix'](map(str, args))

    def transfer(self, *args):
        self.commands['transfer'](map(str, args))

    def clean(self):
        self.commands['clean']()

    def isExecuting(self):
        state = str(self.getState())
        if state:
            return (state == "RUNNING")
        else:
            return False

    def doCleanProcedure(self):
        self.clean()
        self.wait()


    def wait(self, timeout = 240):
        loopCount = 0
        while self.isExecuting():
            loopCount = loopCount + 1
            time.sleep(0.5)
            # check if timeout*0.5 seconds has passed
            if loopCount > timeout :
                raise RuntimeError, "Timeout from Sample Changer"

        exception = self.getCommandException()
        if exception is not None and exception != "":
            raise RuntimeError, "Sample Changer exception: " + exception


    def doSetSEUTemperatureProcedure(self, temperature):
        self.setSEUTemperature(temperature)

    def doFillProcedure(self, *args):
        self.fill(*args)
        self.wait()

    def doFlowProcedure(self, *args):
        self.flow(*args)
        self.wait()

    def doRecuperateProcedure(self, *args):
        self.recuperate(*args)
        self.wait()
