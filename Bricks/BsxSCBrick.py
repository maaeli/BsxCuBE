import logging

from Framework4.GUI      import Core
from Framework4.GUI.Core import Connection, Signal

from BsxSCWidget import BsxSCWidget
from PyQt4 import Qt

__category__ = "BsxCuBE"

class BsxSCBrick(Core.BaseBrick):

    properties = {}
    connections = {"samplechanger": Connection("Sample Changer object",
                            [Signal('seuTemperatureChanged', 'seu_temperature_changed'),
                             Signal('storageTemperatureChanged', 'storage_temperature_changed'),
                             Signal('stateChanged', 'state_changed'), ],
                            [],
                            "sample_changer_connected"),
                    "login": Connection("Login object",
                            [Signal("loggedIn", "loggedIn")],
                            [],
                            "connectionToLogin")}

    def __init__(self, *args, **kargs):
        Core.BaseBrick.__init__(self, *args, **kargs)

    def init(self):
        self._sampleChanger = None

        mainLayout = Qt.QHBoxLayout(self.brick_widget)
        self.SCWidget = BsxSCWidget(self.brick_widget)
        mainLayout.addWidget(self.SCWidget)
        self.brick_widget.setLayout(mainLayout)
        # self.SCWidget.setState( "Disconnected" )

    # When connected to Login, then block the brick
    def connectionToLogin(self, pPeer):
        if pPeer is not None:
            self.brick_widget.setEnabled(False)


    # Logged In : True or False 
    def loggedIn(self, pValue):
        self.brick_widget.setEnabled(pValue)


    def sample_changer_connected(self, sc):
        if sc is not None:
            logging.info("Sample Changer connected")

            self._sampleChanger = sc

            geometry = [ self._sampleChanger.getPlateInfo(i) for i in range(1, 3) ]
            #TODO: DEBUG
            print ">>>> geometry in sample_changer %r" % geometry
            self.SCWidget.setPlateGeometry(geometry)

            # redefine calls in SCWidget
            self.SCWidget.startSyringeForward = self.startSyringeForward
            self.SCWidget.startSyringeBackward = self.startSyringeBackward
            self.SCWidget.stopSyringe = self._sampleChanger.stopSyringe
            self.SCWidget.setLiquidPositionFixed = self._sampleChanger.setLiquidPositionFixed
            self.SCWidget.fill = self._sampleChanger.fill
            self.SCWidget.dry = self._sampleChanger.dry
            self.SCWidget.flow = self._sampleChanger.flowAll
            self.SCWidget.recuperate = self._sampleChanger.recuperate
            self.SCWidget.clean = self._sampleChanger.clean
            self.SCWidget.abort = self._sampleChanger.abort
            self.SCWidget.mix = self._sampleChanger.mix
            self.SCWidget.transfer = self._sampleChanger.transfer
            self.SCWidget.restart = self._sampleChanger.restart
            self.SCWidget.setStorageTemperature = self._sampleChanger.setStorageTemperature
            self.SCWidget.setSEUTemperature = self._sampleChanger.setSEUTemperature
            self.SCWidget.setState("READY", "Connected")
        else:
            logging.info("Sample Changer NOT connected ")
            self.SCWidget.setState("DISCONNECTED", "SC GUI not running?")
            return

    def storage_temperature_changed(self, temperature):
        self.SCWidget.setCurrentStorageTemperature(temperature)

    def seu_temperature_changed(self, temperature):
        self.SCWidget.setCurrentSEUTemperature(temperature)

    def state_changed(self, state, status):
        if self._sampleChanger is None:
            return
        cmdException = self._sampleChanger.getCommandException()
        self.SCWidget.setState(state, status, cmdException)

    def startSyringeForward(self):
        self._sampleChanger.moveSyringeForward(5)
    def startSyringeBackward(self):
        self._sampleChanger.moveSyringeBackward(5)
