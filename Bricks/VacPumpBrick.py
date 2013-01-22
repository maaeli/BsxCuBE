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
        self.commandPushButton.setToolTip("Make Vacuum in Flight Tube and/or Sample Changer safely")
        self.commandPushButton.setText("Smart Vacuum")

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
        if (self.ftvacuum < 0 or self.scvacuum < 0 or self.usvacuum < 0):
            logging.error("Can not read vacuum gauges. I stop")
            return
        if (self.usvacuum > self.usThreshold):
            logger.error("Upstream vacuum below threshold. Please contact expert")
            answer = Qt.QMessageBox.warning(self.brick_widget, "Warning", "Error in upstream vacuum\nDo you want to continue anyway ?", Qt.QMessageBox.Ok, (Qt.QMessageBox.Cancel | Qt.QMessageBox.Default))
            if answer == Qt.QMessageBox.Cancel:
                return
        if ((self.scvacuum < self.valveThreshold) and (self.ftvacuum < self.valveThreshold)):
            # SC and FT vacuum OK
            logger.info("Vacuum already OK in Sample Changer")
            logger.info("Vacuum already OK in Flight Tube")
            self.pumpingObject.rv5open()
            self.pumpingObject.rv6open()
        elif ((self.scvacuum < self.valveThreshold) and (self.ftvacuum < self.pumpThreshold)):
            # SC OK and FT good but not air
            logger.info("Vacuum already OK in Sample Changer")
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
                self.pumpingObject.vacftclose()
                Qt.QMessageBox.information(self.brick_widget, "Info", "Please go into the Hutch and stop the pump")
        elif ((self.scvacuum < self.valveThreshold)):
            # SC OK and in FT is air - FT vacuum value from Logic - If we came here, FT is air
            logger.info("Vacuum already OK in Sample Changer")
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
                self.pumpingObject.vacftclose()
                Qt.QMessageBox.information(self.brick_widget, "Info", "Please go into the Hutch and stop the pump")
        elif ((self.ftvacuum < self.valveThreshold) and (self.scvacuum < self.pumpThreshold)):
            # FT OK and SC good but not air
            logger.info("Vacuum already OK in Flight Tube")
            self.pumpingObject.exscclose()
            Qt.QMessageBox.information(self.brick_widget, "Info", "Please go into the Hutch and start pump and ONLY when done click OK")
            self.pumpingObject.vacscopen()
            # Now wait for vacuum
            time_to_wait = self.scTimeout
            exitOK = False
            while time_to_wait > 0:
                logger.info("Waiting for sample changer vacuum to be OK. %d seconds left..." % time_to_wait)
                time.sleep(min(20, time_to_wait))
                self.scvacuum = float(self.pumpingObject.getSCVacuum())
                if (self.scvacuum < self.valveThreshold):
                    exitOK = True
                    break
                time_to_wait = time_to_wait - 20
            if exitOK == False :
                logger.warning("Timeout, could not achieve vacuum in Sample Changer")
            else:
                logger.info("Vacuum achieved in Sample Changer")
                self.pumpingObject.vacscclose()
                self.pumpingObject.rv5open()
                logger.info("Check Flight Tube Vacuum again")
                self.ftvacuum = float(self.pumpingObject.getFTVacuum())
                if (self.ftvacuum >= self.valveThreshold):
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
                        self.pumpingObject.vacftclose()
                        logger.info("Vacuum achieved in Flight Tube")
                        self.pumpingObject.rv6open()
                        Qt.QMessageBox.information(self.brick_widget, "Info", "Please go into the Hutch and stop the pump")
                else:
                    logger.info("Vacuum still OK in Flight Tube")
                    self.pumpingObject.rv6open()
                    Qt.QMessageBox.information(self.brick_widget, "Info", "Please go into the Hutch and stop the pump")
        elif ((self.ftvacuum < self.valveThreshold)):
            # FT OK and in SC is air - SC vacuum value from Logic - If we came here, SC in air
            logger.info("Vacuum already OK in Flight Tube")
            self.pumpingObject.exscclose()
            self.pumpingObject.vacscopen()
            Qt.QMessageBox.information(self.brick_widget, "Info", "Please go into the Hutch and start pump and ONLY when done click OK")
            # Now wait for vacuum
            time_to_wait = self.scTimeout
            exitOK = False
            while time_to_wait > 0:
                logger.info("Waiting for sample changer vacuum to be OK. %d seconds left..." % time_to_wait)
                time.sleep(min(20, time_to_wait))
                self.ftvacuum = float(self.pumpingObject.getSCVacuum())
                if (self.scvacuum < self.valveThreshold):
                    exitOK = True
                    break
                time_to_wait = time_to_wait - 20
            if exitOK == False :
                logger.warning("Timeout, could not achieve vacuum in Sample Changer")
            else:
                logger.info("Vacuum achieved in Sample Changer")
                self.pumpingObject.vacscclose()
                self.pumpingObject.rv5open()
                logger.info("Check Flight Tube Vacuum again")
                self.ftvacuum = float(self.pumpingObject.getFTVacuum())
                if (self.ftvacuum >= self.valveThreshold):
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
                        self.pumpingObject.vacftclose()
                        logger.info("Vacuum achieved in Flight Tube")
                        self.pumpingObject.rv6open()
                        Qt.QMessageBox.information(self.brick_widget, "Info", "Please go into the Hutch and stop the pump")
                else:
                    logger.info("Vacuum still OK in Flight Tube")
                    self.pumpingObject.rv6open()
                    Qt.QMessageBox.information(self.brick_widget, "Info", "Please go into the Hutch and stop the pump")
        elif ((self.ftvacuum < self.pumpThreshold) and (self.scvacuum < self.pumpThreshold)):
            # FT and SC both good and not air
            self.pumpingObject.exftclose()
            self.pumpingObject.exscclose()
            Qt.QMessageBox.information(self.brick_widget, "Info", "Please go into the Hutch and start pump and ONLY when done click OK")
            self.pumpingObject.vacscopen()
            self.pumpingObject.vacftopen()
            # Now wait for vacuum in SC first
            time_to_wait = self.scTimeout
            exitOK = False
            while time_to_wait > 0:
                logger.info("Waiting for sample changer vacuum to be OK. %d seconds left..." % time_to_wait)
                time.sleep(min(20, time_to_wait))
                self.scvacuum = float(self.pumpingObject.getSCVacuum())
                if (self.scvacuum < self.valveThreshold):
                    exitOK = True
                    break
                time_to_wait = time_to_wait - 20
            if exitOK == False :
                logger.warning("Timeout, could not achieve vacuum in Sample Changer")
                # we do not try to do anything else
            else:
                logger.info("Vacuum achieved in Sample Changer")
                # Now deal with FT
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
                    self.pumpingObject.rv5open()
                    self.pumpingObject.vacscclose()
                    self.pumpingObject.vacftclose()
                    Qt.QMessageBox.information(self.brick_widget, "Info", "Please go into the Hutch and stop the pump")
        elif ((self.ftvacuum < self.pumpThreshold)):
            # FT good and in SC is air - SC vacuum value from Logic - If we came here, SC in air
            self.pumpingObject.exftclose()
            self.pumpingObject.exscclose()
            self.pumpingObject.vacscopen()
            Qt.QMessageBox.information(self.brick_widget, "Info", "Please go into the Hutch and start pump and ONLY when done click OK")
            self.pumpingObject.vacftopen()
            # Now wait for vacuum in SC first
            time_to_wait = self.scTimeout
            exitOK = False
            while time_to_wait > 0:
                logger.info("Waiting for sample changer vacuum to be OK. %d seconds left..." % time_to_wait)
                time.sleep(min(20, time_to_wait))
                self.scvacuum = float(self.pumpingObject.getSCVacuum())
                if (self.scvacuum < self.valveThreshold):
                    exitOK = True
                    break
                time_to_wait = time_to_wait - 20
            if exitOK == False :
                logger.warning("Timeout, could not achieve vacuum in Sample Changer")
                # we do not try to do anything else
            else:
                logger.info("Vacuum achieved in Sample Changer")
                # Now deal with FT
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
                    self.pumpingObject.rv5open()
                    self.pumpingObject.vacscclose()
                    self.pumpingObject.vacftclose()
                    Qt.QMessageBox.information(self.brick_widget, "Info", "Please go into the Hutch and stop the pump")
        elif ((self.scvacuum < self.pumpThreshold)):
            # SC good and in FT is air - FT vacuum value from Logic - If we came here, FT in air
            self.pumpingObject.exftclose()
            self.pumpingObject.exscclose()
            self.pumpingObject.vacftopen()
            Qt.QMessageBox.information(self.brick_widget, "Info", "Please go into the Hutch and start pump and ONLY when done click OK")
            self.pumpingObject.vacscopen()
            # Now wait for vacuum in SC first
            time_to_wait = self.scTimeout
            exitOK = False
            while time_to_wait > 0:
                logger.info("Waiting for sample changer vacuum to be OK. %d seconds left..." % time_to_wait)
                time.sleep(min(20, time_to_wait))
                self.scvacuum = float(self.pumpingObject.getSCVacuum())
                if (self.scvacuum < self.valveThreshold):
                    exitOK = True
                    break
                time_to_wait = time_to_wait - 20
            if exitOK == False :
                logger.warning("Timeout, could not achieve vacuum in Sample Changer")
                # we do not try to do anything else
            else:
                logger.info("Vacuum achieved in Sample Changer")
                # Now deal with FT
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
                    self.pumpingObject.rv5open()
                    self.pumpingObject.vacscclose()
                    self.pumpingObject.vacftclose()
                    Qt.QMessageBox.information(self.brick_widget, "Info", "Please go into the Hutch and stop the pump")
        else:
            # SC and FT is air - FT and SC vacuum value from Logic - If we came here, FT and SC in air
            self.pumpingObject.exftclose()
            self.pumpingObject.exscclose()
            self.pumpingObject.vacftopen()
            self.pumpingObject.vacscopen()
            Qt.QMessageBox.information(self.brick_widget, "Info", "Please go into the Hutch and start pump and ONLY when done click OK")
            # Now wait for vacuum in SC first
            time_to_wait = self.scTimeout
            exitOK = False
            while time_to_wait > 0:
                logger.info("Waiting for sample changer vacuum to be OK. %d seconds left..." % time_to_wait)
                time.sleep(min(20, time_to_wait))
                self.scvacuum = float(self.pumpingObject.getSCVacuum())
                if (self.scvacuum < self.valveThreshold):
                    exitOK = True
                    break
                time_to_wait = time_to_wait - 20
            if exitOK == False :
                logger.warning("Timeout, could not achieve vacuum in Sample Changer")
                # we do not try to do anything else
            else:
                logger.info("Vacuum achieved in Sample Changer")
                # Now deal with FT
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
                    self.pumpingObject.rv5open()
                    self.pumpingObject.vacscclose()
                    self.pumpingObject.vacftclose()
                    Qt.QMessageBox.information(self.brick_widget, "Info", "Please go into the Hutch and stop the pump")

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
