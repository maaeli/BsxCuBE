from Framework4.GUI      import Core
from Framework4.GUI.Core import Signal, Slot
from PyQt4 import Qt, QtCore
import ldap
import logging

logger = logging.getLogger("LoginBrick")

__category__ = "General"

class LoginBrick(Core.BaseBrick):

    properties = {}

    signals = [Signal("loggedIn")]
    slots = []


    def __init__(self, *args, **kargs):
        Core.BaseBrick.__init__(self, *args, **kargs)


    def init(self):
        #TODO: DEBUG - Timestamp for all working - Test to put it here [as late as possible] (used by starting mechanism)
        self.__password = ""
        self.__username = "nobody"
        self.loginProxy = None
        self.__loggedIn = False

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
        self.infoLabel = Qt.QLabel("<h2>You must log in to use BsxCuBE</h2>", self.brick_widget)
        self.infoLabel.setStyleSheet('QLabel {color: red}')
        self.infoBox.addWidget(self.infoLabel)
        #
        # Add spacer
        self.spacerBox = Qt.QHBoxLayout()
        self.brick_widget.layout().addLayout(self.spacerBox)
        self.spacerLabel = Qt.QLabel(" ", self.brick_widget)
        self.spacerBox.addWidget(self.spacerLabel)

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
        self.choices = ['opd', 'fx', 'ifx', 'ih', 'im', 'is', 'mx', 'mxihr']
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
        self.passwordBox.addWidget(self.logoutButton)

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
            self.logoutButton.show()
            self.brick_widget.setEnabled(True)
            self.infoLabel.setStyleSheet('QLabel {color: gray}')
            infoLabelText = "<h2>Logged in as %s to BsxCUBE</h2>" % self.__username
            self.infoLabel.setText(infoLabelText)
            self.codeLabel.hide()
            self.propType.hide()
            self.dashLabel.hide()
            self.propNumber.hide()
            self.passwordLabel.hide()
            self.propPassword.hide()
            self.loginButton.hide()
            self.__loggedIn = True
            self.emit("loggedIn", self.__loggedIn)
        else:
            self.refuseLogin("Username or password bad")


    # Creates a new connection to LDAP if there's an exception on the current connection
    def reconnect(self):
        if self.ldapConnection is not None:
            try:
                self.ldapConnection.result(timeout = 0)
            except ldap.LDAPError, err:
                logger.debug("LdapLogin: reconnecting to LDAP server %s", self.ldapHost)
                logger.error("Got Exception: " + str(err) + "When interpreting value")
                self.ldapConnection = ldap.open(self.ldapHost)


   # Logs the error message (or LDAP exception) and returns the respective tuple
    def cleanup(self, ex = None, msg = None):
        if ex is not None:
            try:
                msg = ex[0]['desc']
            except (IndexError, KeyError, ValueError, TypeError):
                msg = "generic LDAP error"
        logger.debug("LdapLogin: %s" % msg)
        if ex is not None:
            self.reconnect()
        return (False, msg)


    def checkLogin(self, username, password, retry = True):
        if self.ldapConnection is None:
            return self.cleanup(msg = "no LDAP server connection")

        logger.debug("LdapLogin: searching for %s" % username)
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

        logger.debug("LdapLogin: validating %s" % username)
        handle = self.ldapConnection.simple_bind("uid=%s,ou=people,dc=esrf,dc=fr" % username, password)
        try:
            self.result = self.ldapConnection.result(handle)
        except ldap.INVALID_CREDENTIALS:
            return self.cleanup(msg = "invalid password for %s" % username)
        except ldap.LDAPError, err:
            if retry:
                self.cleanup(ex = err)
                return self.checkLogin(username, password, retry = False)
            else:
                return self.cleanup(ex = err)

        return (True, username)


    def refuseLogin(self, message = None):
        if message is not None:
            self.errorBox = Qt.QMessageBox.critical(self.brick_widget, "Error", message, Qt.QMessageBox.Ok)
            self.brick_widget.setEnabled(True)

    # Opens the logout dialog (modal); if the answer is OK then logout the user
    def openLogoutDialog(self):
        self.logoutDialog = Qt.QMessageBox.critical(self.brick_widget, "Confirm logout", "Press OK to logout.", Qt.QMessageBox.Ok)
        self.logout()

    def getUserInfo(self):
        return (self.__username, self.__password)


    # Logout the user; reset the brick; changes from logout mode to login mode
    def logout(self):
        self.logoutButton.hide()
        self.loginButton.show()
        self.infoLabel.setStyleSheet('QLabel {color: red}')
        self.infoLabel.setText("<h2>You must log in to use BsxCuBE</h2>")
        self.codeLabel.show()
        self.propType.show()
        self.dashLabel.show()
        self.propNumber.show()
        self.passwordLabel.show()
        self.propPassword.show()
        self.loginButton.show()
        self.__loggedIn = False
        self.emit("loggedIn", self.__loggedIn)
