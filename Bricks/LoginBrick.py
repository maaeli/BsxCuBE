from Framework4.GUI      import Core
from Framework4.GUI.Core import Connection, Signal, Slot
from PyQt4 import QtGui, Qt, QtCore
import ldap
import logging

__category__ = "General"

class LoginBrick(Core.BaseBrick):

    properties = {}

    signals = []
    slots = []


    def __init__(self, *args, **kargs):
        Core.BaseBrick.__init__(self, *args, **kargs)


    def init(self):
        self.__password = ""
        self.__username = "nobody"
        self.loginProxy = None

        #TODO: make it more prominent with coloring
        # Set up layout
        self.brick_widget.setLayout(Qt.QVBoxLayout())
        self.brick_widget.layout().setAlignment(QtCore.Qt.AlignTop)
        self.brick_widget.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        #
        # INFO on login
        #
        self.infoBox = Qt.QHBoxLayout()
        if self.brick_widget.layout() is not None:
            self.infoBox.setParent(None)
        self.brick_widget.layout().addLayout(self.infoBox)
        self.infoLabel = Qt.QLabel("You must log in to use BsxCuBE", self.brick_widget)
        self.infoBox.addWidget(self.infoLabel)

        #
        # Select User to login
        #
        self.userBox = Qt.QHBoxLayout()
        self.codeLabel = Qt.QLabel("Code:", self.brick_widget)
        self.userBox.addWidget(self.codeLabel)
        self.brick_widget.layout().addLayout(self.userBox)

        self.propType = Qt.QComboBox()
        self.propType.setEditable(True)
        self.propType.setSizePolicy(Qt.QSizePolicy.Fixed, Qt.QSizePolicy.MinimumExpanding)

        #TODO: read from XML
        self.choices = ['fx', 'ifx', 'ih', 'im', 'is', 'mx', 'mxihr', 'opd']
        self.propType.addItems(self.choices)
        self.userBox.addWidget(self.propType)
        self.dashLabel = Qt.QLabel(" - ", self.brick_widget)
        self.userBox.addWidget(self.dashLabel)
        self.propNumber = Qt.QLineEdit(self.brick_widget)
        self.propNumber.setValidator(Qt.QIntValidator(0, 99999, self.propNumber))
        self.userBox.addWidget(self.propNumber)

        #
        # Password and acknowledge on next row
        self.passwordBox = Qt.QHBoxLayout()
        self.brick_widget.layout().addLayout(self.passwordBox)
        self.passwordLabel = Qt.QLabel("Password:", self.brick_widget)
        self.passwordBox.addWidget(self.passwordLabel)
        self.propPassword = Qt.QLineEdit(self.brick_widget)
        self.propPassword.setEchoMode(Qt.QLineEdit.Password)
        self.passwordBox.addWidget(self.propPassword)
        Qt.QObject.connect(self.propPassword, Qt.SIGNAL('returnPressed()'), self.login)

        self.loginButton = Qt.QPushButton("Login")
        self.passwordBox.addWidget(self.loginButton)
        Qt.QObject.connect(self.loginButton, Qt.SIGNAL('clicked()'), self.login)

        self.logoutButton = Qt.QPushButton("Logout")
        Qt.QObject.connect(self.logoutButton, Qt.SIGNAL('clicked()'), self.openLogoutDialog)
        self.logoutButton.hide()
        self.passwordBox.addWidget(self.loginButton)

    def login(self):

        self.brick_widget.setEnabled(False)

        self.enteredPropType = str(self.propType.currentText())
        self.enteredPropNumber = str(self.propNumber.text())
        self.enteredPropPassword = str(self.propPassword.text())
        # be paranoid - empty entered password in text box
        self.propPassword.setText("")

        if self.enteredPropNumber == "" or self.enteredPropPassword == "":
            return self.refuseLogin("You need to enter a user and a password")
        self.__password = self.enteredPropPassword
        self.__username = self.enteredPropType + self.enteredPropNumber
        # Now check in ldap
        ## First set up info and connection
        self.ldapHost = "ldap.esrf.fr"
        self.ldapConnection = ldap.open(self.ldapHost)
        if (self.checkLogin(self.__username, self.__password)[0]):
            # Got usernamed checked
            #TODO: get info from IspyB
            # Get sessions from ISPyB 
            #      and if several -> ask which
            #      if none - Popup to suggest to use opd29
            # if username is opd29, no IspyB is needed

            self.brick_widget.setEnabled(True)
            self.loginButton.hide()
            self.logoutButton.show()
        else:
            self.refuseLogin("Username or password bad")


    # Creates a new connection to LDAP if there's an exception on the current connection
    def reconnect(self):
        if self.ldapConnection is not None:
            try:
                self.ldapConnection.result(timeout = 0)
            except ldap.LDAPError, err:
                logging.getLogger().debug("LdapLogin: reconnecting to LDAP server %s", self.ldapHost)
                logging.getLogger().error("Got Exception: " + str(err) + "When interpreting value")
                self.ldapConnection = ldap.open(self.ldapHost)


   # Logs the error message (or LDAP exception) and returns the respective tuple
    def cleanup(self, ex = None, msg = None):
        if ex is not None:
            try:
                msg = ex[0]['desc']
            except (IndexError, KeyError, ValueError, TypeError):
                msg = "generic LDAP error"
        logging.getLogger().debug("LdapLogin: %s" % msg)
        if ex is not None:
            self.reconnect()
        return (False, msg)


    def checkLogin(self, username, password, retry = True):
        if self.ldapConnection is None:
            return self.cleanup(msg = "no LDAP server connection")

        logging.getLogger().debug("LdapLogin: searching for %s" % username)
        try:
            found = self.ldapConnection.search_s("ou=People,dc=esrf,dc=fr", \
                ldap.SCOPE_ONELEVEL, "uid=" + username, ["uid"])
        except ldap.LDAPError, err:
            if retry:
                self.cleanup(ex = err)
                return self.checkLogin(username, password, retry = False)
            else:
                return self.cleanup(ex = err)

        if not found:
            return self.cleanup(msg = "unknown proposal %s" % username)
        if password == "":
            return self.cleanup(msg = "invalid password for %s" % username)

        logging.getLogger().debug("LdapLogin: validating %s" % username)
        handle = self.ldapConnection.simple_bind("uid=%s,ou=people,dc=esrf,dc=fr" % username, password)
        try:
            result = self.ldapConnection.result(handle)
        except ldap.INVALID_CREDENTIALS:
            return self.cleanup(msg = "invalid password for %s" % username)
        except ldap.LDAPError, err:
            if retry:
                self.cleanup(ex = err)
                return self.checkLogin(username, password, retry = False)
            else:
                return self.cleanup(ex = err)

        return (True, username)

#            now=time.strftime("%Y-%m-%d %H:%M:S")
#            prop_dict={'code':'', 'number':'', 'title':'', 'proposalId':''}
#            ses_dict={'sessionId':'', 'startDate':now, 'endDate':now, 'comments':''}
#            try:
#                locallogin_person=self.localLogin.person
#            except AttributeError:
#                locallogin_person="local user"
#            pers_dict={'familyName':locallogin_person}
#            lab_dict={'name':'ESRF'}
#            cont_dict={'familyName':'local contact'}
#
#            logging.getLogger().debug("ProposalBrick: local login password validated")
#
#            return self.acceptLogin(prop_dict,pers_dict,lab_dict,ses_dict,cont_dict)
#
#        try:
#            beamline_name=os.environ[ENV_BEAMLINE_NAME]
#        except KeyError:
#            beamline_name=""
#        if beamline_name=="":
#            return self.refuseLogin(False,"Unknown beamline (environment variable %s is missing)." % ENV_BEAMLINE_NAME)
#
#        try:
#            prop_number=int(prop_number)
#        except (ValueError,TypeError):
#            return self.refuseLogin(None,"Invalid proposal number.")
#
#        if self.ldapConnection is None and str(beamline_name) != "My_office":
#            return self.refuseLogin(False,'Not connected to LDAP, unable to verify password.')
#        if self.dbConnection is None:
#            return self.refuseLogin(False,'Not connected to the ISPyB database, unable to get proposal.')
#
#        if str(beamline_name) == "My_office":
#            self.loginActions=LoginThread(self,prop_type,prop_number,prop_password,beamline_name,self.ldapConnection,self.dbConnection, imper
#sonate=True)
#        else:
#            self.loginActions=LoginThread(self,prop_type,prop_number,prop_password,beamline_name,self.ldapConnection,self.dbConnection)
#        self.loginActions.start()



    def refuseLogin(self, message = None):
        if message is not None:
            self.errorBox = Qt.QMessageBox.critical(self.brick_widget, "Error", message, Qt.QMessageBox.Ok)
            self.brick_widget.setEnabled(True)

    # Opens the logout dialog (modal); if the answer is OK then logout the user
    def openLogoutDialog(self):
        logoutDialog = Qt.QMessageBox.critical("Confirm logout", "Press OK to logout.", Qt.QMessageBox.Ok)
        if logoutDialog.exec_loop() == Qt.QMessageBox.Ok:
            self.logout()

    # Logout the user; reset the brick; changes from logout mode to login mode
    def logout(self):
        print "Logout"
#        # Reset brick info
#        self.propNumber.setText("")
#        self.proposal=None
#        self.session=None
#        #self.sessionId=None
#        self.person=None
#        self.laboratory=None
#        # Change mode from logout to login
#        self.loginBox.show()
#        self.logoutButton.hide()
#        self.titleLabel.hide()
#        self.proposalLabel.setText(ProposalBrick2.NOBODY_STR)
#        QToolTip.add(self.proposalLabel,"")
#
#        # Emit signals clearing the proposal and session
#        self.emit(PYSIGNAL("setWindowTitle"),(self["titlePrefix"],))
#        self.emit(PYSIGNAL("sessionSelected"),(None, ))
#        self.emit(PYSIGNAL("loggedIn"), (False, ))


#    def acceptLogin(self, proposal_dict, person_dict, lab_dict, session_dict, contact_dict):
#        if self.loginActions is not None:
#            self.loginActions.wait()
#            self.loginActions = None
#        self.setProposal(proposal_dict, person_dict, lab_dict, session_dict, contact_dict)
#        self.setEnabled(True)
#
#    def ispybDown(self):
#        if self.loginActions is not None:
#            self.loginActions.wait()
#            self.loginActions = None
#
#        msg_dialog = QMessageBox("Register user", \
#            "Couldn't contact the ISPyB database server: you've been logged as the local user.\nYour experiments' information will not be sto
#red in ISPyB!", \
#            QMessageBox.Warning, QMessageBox.Ok, QMessageBox.NoButton, \
#            QMessageBox.NoButton, self)
#        s = self.font().pointSize()
#        f = msg_dialog.font()
#        f.setPointSize(s)
#        msg_dialog.setFont(f)
#        msg_dialog.updateGeometry()
#        msg_dialog.exec_loop()
#
#        now = time.strftime("%Y-%m-%d %H:%M:S")
#        prop_dict = {'code':'', 'number':'', 'title':'', 'proposalId':''}
#        ses_dict = {'sessionId':'', 'startDate':now, 'endDate':now, 'comments':''}
#        try:
#            locallogin_person = self.localLogin.person
#        except AttributeError:
#            locallogin_person = "local user"
#        pers_dict = {'familyName':locallogin_person}
#        lab_dict = {'name':'ESRF'}
#        cont_dict = {'familyName':'local contact'}
#        self.acceptLogin(prop_dict, pers_dict, lab_dict, ses_dict, cont_dict)
#
#### Thread to perform the login actions in the background: verify LDAP password,
#### get proposal and sessions from the ISPyB server
#class LoginThread(QThread):
#    def __init__(self, brick, proposal_code, proposal_number, proposal_password, beamline_name, ldap_connection, db_connection, impersonate = False):
#        QThread.__init__(self)
#
#        self.Brick = brick
#        self.proposalCode = proposal_code
#        self.proposalNumber = proposal_number
#        self.proposalPassword = proposal_password
#        self.beamlineName = beamline_name
#        self.ldapConnection = ldap_connection
#        self.dbConnection = db_connection
#        self.condition = LoginCondition()
#        self.impersonate = impersonate
#
#    def postAcceptEvent(self, proposal, person, laboratory, session, localcontact):
#        #logging.getLogger().debug("ProposalBrick2: queue accept event")
#        method = ProposalBrick2.acceptLogin
#        arguments = (self.Brick, proposal, person, laboratory, session, localcontact)
#        custom_event = ProposalGUIEvent(method, arguments)
#        self.postEvent(self.Brick, custom_event)
#
#    def postRefuseEvent(self, stat, message):
#        #logging.getLogger().debug("ProposalBrick2: queue refuse event")
#        method = ProposalBrick2.refuseLogin
#        arguments = (self.Brick, stat, message)
#        custom_event = ProposalGUIEvent(method, arguments)
#        self.postEvent(self.Brick, custom_event)
#
#    def postNewSessionEvent(self):
#        #logging.getLogger().debug("ProposalBrick2: queue new session event")
#        method = ProposalBrick2.askForNewSession
#        arguments = (self.Brick,)
#        custom_event = ProposalGUIEvent(method, arguments)
#        self.postEvent(self.Brick, custom_event)
#
#    def postIspybDownEvent(self):
#        #logging.getLogger().debug("ProposalBrick2: queue ispyb down event")
#        method = ProposalBrick2.ispybDown
#        arguments = (self.Brick,)
#        custom_event = ProposalGUIEvent(method, arguments)
#        self.postEvent(self.Brick, custom_event)
#
#    def createSession(self, create):
#        if create:
#            self.condition.proceed()
#        else:


#                                                      


#
# OLD CODE
#
#    def passwordChanged(self, pValue):
#        self.__password = pValue
#
#    def loginConnected(self, pPeer):
#        if pPeer is not None:
#            # we are connected, let us block the other bricks
#            self.__loggedIn = False
#            self.loginProxy = pPeer
#            self.loginProxy.loginTry("tes")
#            self.emit("loggedIn", self.__loggedIn)
#
#    def modePushButtonClicked(self):
#        print "Pushed button"
