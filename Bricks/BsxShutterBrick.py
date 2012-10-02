"""BsxShutter brick - Changed from ShutterBrick by SO from FW4 22/8 2012 
"""

from Framework4.GUI import Core
from Framework4.GUI.Core import Property, PropertyGroup, Connection, Signal, Slot

from PyQt4 import Qt, QtGui
import os
import logging
import sip

logger = logging.getLogger("BsxShutterBrick")

__category__ = "BsxCuBE"


class BsxShutterBrick(Core.BaseBrick):
    description = 'Simple class to display and control a shutter'

    properties = {"icons": PropertyGroup("Icons", "Select icons for different elements", "set_icons",
                                          { "opened": Property("image", "Opened"),
                                            "closed": Property("image", "Closed") })
                    , 'shutter_name': Property('string', #type
                                            'Shutter name', #label
                                            'The name of the shutter', #description
                                            'shutterNameStateChanged', #onchange_cb
                                            '') #default value    
                    , 'show_state': Property('boolean', #type
                                            'Show state', #label
                                            '', #description
                                            'showStateChanged', #onchange_cb
                                            True) #default value
                    , 'show_button': Property('boolean', #type
                                            'Show button', #label
                                            'Allow the user to manipulate the shutter\'s state', #description
                                            'showButtonChanged', #onchange_cb
                                            True) #default value
                    , 'orientation': Property('combo', #type
                                                'Orientation', #label
                                                description = 'Layout of widgets',
                                                onchange_cb = 'orientationChanged',
                                                default = 'Portrait',
                                                choices = [ 'Portrait',
                                                            'Landscape'])
                    }



    connections = {"shutter": Connection("Shutter object",
                                          [ Signal("stateChanged", "shutter_state_changed") ],
                                          [ Slot("open"), Slot("close") ],
                                          "connectionStatusChanged"),

                   "display": Connection("Display object",
                                    [Signal("displayResetChanged", "displayResetChanged"),
                                    Signal("displayItemChanged", "displayItemChanged"),
                                    Signal("transmissionChanged", "transmissionChanged"),
                                    Signal("grayOut", "grayOut")],
                                    []),

                   "login": Connection("Login object",
                                        [Signal("loggedIn", "loggedIn")],
                                        [],
                                        "connectionToLogin")}


    # TACO Shutterstate
#    shutterState = {"unknown": Qt.QColor(0x64, 0x64, 0x64),
#                    "closed": Qt.QColor(0xff, 0x0, 0xff),
#                    "opened": Qt.QColor(0x0, 0xff, 0x0),
#                    "moving": Qt.QColor(0x66, 0x33, 0x0),
#                    "automatic": Qt.QColor(0x0, 0x99, 0x0),
#                    "fault": Qt.QColor(0x99, 0x0, 0x0),
#                    "disabled": Qt.QColor(0xec, 0x3c, 0xdd),
#                    "error": Qt.QColor(0xff, 0x0, 0x0)}

    # TANGO Shutterstate
    shutterState = {"on": Qt.QColor(0x0, 0xff, 0x0),
                    "off": Qt.QColor(0xec, 0x3c, 0xdd),
                    "closed": Qt.QColor(0xff, 0x0, 0xff),
                    "opened": Qt.QColor(0x0, 0xff, 0x0),
                    "insert": Qt.QColor(0x66, 0x33, 0x0),
                    "extract": Qt.QColor(0x66, 0x33, 0x0),
                    "moving": Qt.QColor(0xff, 0xa5, 0x0),
                    "standby": Qt.QColor(0x66, 0x33, 0x0),
                    "fault": Qt.QColor(0xff, 0x0, 0x0),
                    "init": Qt.QColor(0x66, 0x33, 0x0),
                    "running": Qt.QColor(0x66, 0x33, 0x0),
                    "alarm": Qt.QColor(0x99, 0x0, 0x0),
                    "disabled": Qt.QColor(0xec, 0x3c, 0xdd),
                    "unknown": Qt.QColor(0x64, 0x64, 0x64),
                    "error": Qt.QColor(0xff, 0x0, 0x0)}


    def __init__(self, *args, **kwargs):
        Core.BaseBrick.__init__(self, *args, **kwargs)

    def init(self):
        self.shutterName = None
        self.state = None
        self.shutter_state = Qt.QLabel("Unknown", self.brick_widget)
        self.shutter_state.setAutoFillBackground(True)
        self.shutter_state.palette().setColor(QtGui.QPalette.Background, self.shutterState["unknown"])
        self.shutter_state.setAlignment(Qt.Qt.AlignCenter)
        self.shutter_state.setToolTip("Current shutter state")
        self.shutter_cmd = Qt.QPushButton("Unknown", self.brick_widget)
        self.shutter_cmd.setToolTip("Unknown shutter state")
        Qt.QObject.connect(self.shutter_cmd, Qt.SIGNAL("clicked()"), self.shutter_cmd_clicked)


   # When connected to Login, then block the brick
    def connectionToLogin(self, pPeer):
        if pPeer is not None:
            self.brick_widget.setEnabled(False)

    # Logged In : True or False 
    def loggedIn(self, pValue):
        self.brick_widget.setEnabled(pValue)

    # Connect to display 

    def grayOut(self, grayout):
        if grayout is not None:
            if grayout:
                self.brick_widget.setEnabled(False)
            else:
                self.brick_widget.setEnabled(True)

    def displayResetChanged(self, _):
        pass

    def displayItemChanged(self, _):
        pass

    def transmissionChanged(self, _):
        pass

    def set_icons(self, icons):
        pass


    def shutterNameStateChanged(self, pValue):
        self.shutterName = pValue
        self.shutter_state.setToolTip("Current '%s' shutter state" % self.shutterName)
        state = self.state

        # force redisplay of state so the shutter name is displayed.
        if state is None:
            state = 'unknown'
        self.shutter_state_changed(state)


    def showStateChanged(self, pValue):
        if self.shutter_state is not None:
            self.shutter_state.setVisible(pValue)


    def showButtonChanged(self, pValue):
        if self.shutter_cmd is not None:
            self.shutter_cmd.setVisible(pValue)


    def orientationChanged(self, pValue):
        if self.brick_widget.layout() is not None:
            self.brick_widget.layout().removeWidget(self.shutter_state)
            self.brick_widget.layout().removeWidget(self.shutter_cmd)
            sip.transferback(self.brick_widget.layout())
        if pValue == "Landscape":
            self.brick_widget.setLayout(Qt.QHBoxLayout())
        else:
            self.brick_widget.setLayout(Qt.QVBoxLayout())
        self.brick_widget.layout().addWidget(self.shutter_state)
        self.brick_widget.layout().addWidget(self.shutter_cmd)



    def shutter_state_changed(self, state):
        self.state = state
        if state in ("opened", "automatic"):
            self.shutter_cmd.setText("Close")
            self.shutter_cmd.setEnabled(True)
            if self.shutterName is None:
                self.shutter_cmd.setToolTip("Close shutter")
            else:
                self.shutter_cmd.setToolTip("Close '%s' shutter" % self.shutterName)
        elif state == "unknown":
            self.shutter_cmd.setText("Unknown")
            self.shutter_cmd.setEnabled(True)
            if self.shutterName is None:
                self.shutter_cmd.setToolTip("Unknown shutter state")
            else:
                self.shutter_cmd.setToolTip("Unknown '%s' shutter state" % self.shutterName)
        else:
            self.shutter_cmd.setText("Open")
            self.shutter_cmd.setEnabled(True)
            if self.shutterName is None:
                self.shutter_cmd.setToolTip("Open shutter")
            else:
                self.shutter_cmd.setToolTip("Open '%s' shutter" % self.shutterName)
        palette = self.shutter_state.palette()
        palette.setColor(QtGui.QPalette.Background, self.shutterState[state])
        self.shutter_state.setPalette(palette)

        if self.shutterName is not None:
            state = '%s: %s' % (self.shutterName, state)

        self.shutter_state.setText(state)


    def connectionStatusChanged(self, pPeer):
        self.brick_widget.setEnabled(pPeer is not None)
        if pPeer is not None:
            pPeer.connect("ready", self.enable)

    def enable(self, arg):
        self.brick_widget.setEnabled(arg)

    def shutter_cmd_clicked(self):
        if self.shutter_cmd.text() == "Open":
            if self.shutterName is None:
                logger.info("Opening shutter...")
            else:
                logger.info("Opening '%s' shutter..." % self.shutterName)
            self.getObject('shutter').open()
        else:
            if self.shutterName is None:
                logger.info("Closing shutter...")
            else:
                logger.info("Closing '%s' shutter..." % self.shutterName)
            self.getObject('shutter').close()
