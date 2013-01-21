import logging
from Framework4.GUI import Core
from Framework4.GUI.Core import Connection, Slot
from PyQt4 import Qt
import time

logger = logging.getLogger("VacPumpBrick")

__category__ = "BsxCuBE"


class VacPumpBrick(Core.BaseBrick):

    properties = {}

    connections = {"pumping": Connection("Pumping object",
                                         [],
                                         [Slot("exftclose"), Slot("exscclose"), Slot("vacftclose"), Slot("vacscclose"), Slot("vacftopen"), Slot("vacscopen"), Slot("rv5open"), Slot("rv6open"),
                                          Slot("getValveThreshold"), Slot("getPumpThreshold"), Slot("getUSThreshold"), Slot("getFTTimeout"), Slot("getSCTimeout"),
                                          Slot("getFTVacuum"), Slot("getSCVacuum"), Slot("getUSVacuum")],
                                         "connectionToPumping")}

    signals = []
    slots = []


    def __init__(self, *args, **kargs):
        Core.BaseBrick.__init__(self, *args, **kargs)
        self.pumpingObject = None
        self.valveThreshold = None
        self.pumpThreshold = None
        self.usThreshold = None
        self.ftTimeout = None
        self.scTimeout = None
        self.ftvacuum = 0.0
        self.scvacuum = 0.0
        self.usvacuum = 0.0

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
        Qt.QMessageBox.information(self.brick_widget, "Info", "Not implemented yet")
        return
        if self.pumpingObject is None:
            logger.error("Is not connected with the CO Server. I stop")
            return
        # Logic starts here
        self.ftvacuum = float(self.pumpingObject.getFTVacuum())
        self.scvacuum = float(self.pumpingObject.getSCVacuum())
        self.usvacuum = float(self.pumpingObject.getUSVacuum())
        if (self.usvacuum > self.usThreshold):
            logger.error("Upstream vacuum below threshold. Please contact expert")
            answer = Qt.QMessageBox.warning(self.brick_widget, "Warning", "Error in upstream vacuum\nDo you want to continue anyway ?", Qt.QMessageBox.Ok, (Qt.QMessageBox.Cancel | Qt.QMessageBox.Default))
            if answer == Qt.QMessageBox.Cancel:
                return
        if ((self.scvacuum < self.valveThreshold) and (self.ftvacuum < self.valveThreshold)):
            # SC and FT vacuum OK
            self.pumpingObject.rv5open()
            self.pumpingObject.rv6open()
        elif ((self.scvacuum < self.valveThreshold) and (self.ftvacuum < self.pumpThreshold)):
            # SC OK and FT good but not air
            self.pumpingObject.rv5open()
            self.pumpingObject.exftclose()
            Qt.QMessageBox.information(self.brick_widget, "Info", "Please go into the Hutch and start pump and ONLY when done click OK")
            self.pumpingObject.vacftopen()
            # Now wait for vacuum
            time_to_wait = self.ftTimeout
            exitOK = False
            while time_to_wait > 0:
                logger.info("Waiting for flight tube vacuum to be OK. %d seconds left..." % time_to_wait)
                time.sleep(min(20, time_to_wait))
                self.ftvacuum = float(self.pumpingObject.getFTVacuum())
                if (self.ftvacuum < self.valveThreshold):
                    exitOK = True
                    break
                time_to_wait = time_to_wait - 20
            if exitOK == False :
                logger.warning("Timeout, could not achieve vacuum in Flight Tube")
            else:
                logger.info("Vacuum achieved in Flight Tube")
                self.pumpingObject.rv6open()
        elif ((self.scvacuum < self.valveThreshold) and (self.ftvacuum >= self.pumpThreshold)):
            # SC OK and in FT is air
            self.pumpingObject.rv5open()
            self.pumpingObject.exftclose()
            self.pumpingObject.vacftopen()
            Qt.QMessageBox.information(self.brick_widget, "Info", "Please go into the Hutch and start pump and ONLY when done click OK")
            # Now wait for vacuum
            time_to_wait = self.ftTimeout
            exitOK = False
            while time_to_wait > 0:
                logger.info("Waiting for flight tube vacuum to be OK. %d seconds left..." % time_to_wait)
                time.sleep(min(20, time_to_wait))
                self.ftvacuum = float(self.pumpingObject.getFTVacuum())
                if (self.ftvacuum < self.valveThreshold):
                    exitOK = True
                    break
                time_to_wait = time_to_wait - 20
            if exitOK == False :
                logger.warning("Timeout, could not achieve vacuum in Flight Tube")
            else:
                logger.info("Vacuum achieved in Flight Tube")
                self.pumpingObject.rv6open()

    def expert_mode(self, expert):
        self.__expertMode = expert
        self.commandPushButton.setEnabled(self.__expertMode)

    def connectionToPumping(self, peer):
        if peer is not None:
            self.pumpingObject = peer
            # let us read in the static object if not already done
            if self.valveThreshold is None:
                self.valveThreshold = float(self.pumpingObject.getValveThreshold())
            if self.pumpThreshold is None:
                self.pumpThreshold = float(self.pumpingObject.getPumpThreshold())
            if self.usThreshold is None:
                self.usThreshold = float(self.pumpingObject.getUSThreshold())
            if self.ftTimeout is None:
                self.ftTimeout = int(self.pumpingObject.getFTTimeout())
            if self.scTimeout is None:
                self.scTimeout = int(self.pumpingObject.getSCTimeout())
