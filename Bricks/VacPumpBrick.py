import logging
from Framework4.GUI import Core
from Framework4.GUI.Core import Property, Connection, Signal, Slot
from PyQt4 import Qt

logger = logging.getLogger("VacPumpBrick")

__category__ = "BsxCuBE"


class VacPumpBrick(Core.BaseBrick):

    properties = {}

    connections = {"pumping": Connection("Pumping object",
                                         [],
                                         [Slot("exftclose"), Slot("exscclose"), Slot("vacftclose"), Slot("vacscclose"), Slot("rv5open"), Slot("rv6open"),
                                          Slot("getValveThreshold"), Slot("getPumpThreshold"), Slot("getFTTimeout"), Slot("getSCTimeout"),
                                          Slot("getFTVacuum"), Slot("getSCVacuum"), Slot("getUSVacuum")],
                                         "connectionToPumping")}

    signals = []
    slots = []


    def __init__(self, *args, **kargs):
        Core.BaseBrick.__init__(self, *args, **kargs)
        self.pumpingObject = None
        self.valveThreshold = None
        self.pumpThreshold = None
        self.ftTimeout = None
        self.scTimeout = None

    def init(self):

        self.brick_widget.setLayout(Qt.QVBoxLayout())
        self.commandPushButton = Qt.QPushButton(self.brick_widget)
        Qt.QObject.connect(self.commandPushButton, Qt.SIGNAL("clicked()"), self.commandPushButtonClicked)
        self.brick_widget.layout().addWidget(self.commandPushButton)
        # Only in expert mode
        self.commandPushButton.setEnabled(False)
        self.commandPushButton.setText("Pump Vacuum")

    def commandPushButtonClicked(self):

        answer = Qt.QMessageBox.warning(self.brick_widget, "Warning", "You clicked on Pump Vacuum\nDo you really want to execute this command ?", Qt.QMessageBox.Ok, (Qt.QMessageBox.Cancel | Qt.QMessageBox.Default))
        if answer == Qt.QMessageBox.Cancel:
            return
        if  self.pumpingObject is not None:
            self.pumpingObject.exftclose()
        ## test
        Qt.QMessageBox.information(self.brick_widget, "Info", "This command does noting yet")


    def expert_mode(self, expert):
        self.__expertMode = expert
        self.commandPushButton.setEnabled(self.__expertMode)

    def connectionToPumping(self, peer):
        if peer is not None:
            self.pumpingObject = peer
            # let us read in the static object if not already done
            if self.valveThreshold is None:
                self.valveThreshold = self.pumpingObject.getValveThreshold()
                #DEBUG
                print ">>> %r " % self.valveThreshold
                print ">>> %s " % type(self.valveThreshold)
            if self.pumpThreshold is None:
                self.pumpThreshold = self.pumpingObject.getPumpThreshold()
                #DEBUG
                print ">>> %r " % self.pumpThreshold
                print ">>> %s " % type(self.pumpThreshold)
            if self.ftTimeout is None:
                self.ftTimeout = self.pumpingObject.getFTTimeout()
                #DEBUG
                print ">>> %r " % self.ftTimeout
                print ">>> %s " % type(self.ftTimeout)
            if self.scTimeout is None:
                self.scTimeout = self.pumpingObject.getSCTimeout()
                #DEBUG
                print ">>> %r " % self.scTimeout
                print ">>> %s " % type(self.scTimeout)
