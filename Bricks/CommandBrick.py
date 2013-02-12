import logging
from Framework4.GUI import Core
from Framework4.GUI.Core import Property, Connection, Signal, Slot
from PyQt4 import Qt

logger = logging.getLogger( "CommandBrick" )

__category__ = "General"


class CommandBrick( Core.BaseBrick ):
    # =============================================
    #  PROPERTIES/CONNECTIONS DEFINITION
    # =============================================            
    properties = {"caption": Property( "string", "Caption", "", "captionChanged" ),
                  "parameter": Property( "string", "Parameter", "", "parameterChanged" ),
                  "toolTip": Property( "string", "Tool tip", "", "toolTipChanged" ),
                  "expertModeOnly": Property( "boolean", "Expert mode only", "", "expertModeOnlyChanged", False ),
                  "warningPopup" : Property( "boolean", "WarningPopup", "", "warningChanged", False )}


    connections = {"command": Connection( "Command object",
                                            [Signal( "commandStatusChanged", "commandStatusChanged" )],
                                            [Slot( "executeCommand" )],
                                            "connectionStatusChanged" )}

    signals = []
    slots = []


    def __init__( self, *args, **kargs ):
        Core.BaseBrick.__init__( self, *args, **kargs )


    def init( self ):
        self.__parameter = ""
        self.__toolTip = ""
        self.__expertModeOnly = False
        self.__expertMode = False
        self.__warning = False
        self.__caption = ""

        self.brick_widget.setLayout( Qt.QVBoxLayout() )
        self.commandPushButton = Qt.QPushButton( self.brick_widget )
        Qt.QObject.connect( self.commandPushButton, Qt.SIGNAL( "clicked()" ), self.commandPushButtonClicked )
        self.brick_widget.layout().addWidget( self.commandPushButton )


    def captionChanged( self, pValue ):
        self.__caption = pValue
        self.commandPushButton.setText( pValue )


    def parameterChanged( self, pValue ):
        self.__parameter = pValue


    def toolTipChanged( self, pValue ):
        self.__toolTip = pValue
        self.commandPushButton.setToolTip( self.__toolTip )


    def expertModeOnlyChanged( self, pValue ):
        self.__expertModeOnly = pValue
        self.expert_mode( self.__expertMode )

    def warningChanged( self, pValue ):
        self.__warning = pValue


    def commandPushButtonClicked( self ):
        if self.__warning:
            answer = Qt.QMessageBox.warning( self.brick_widget, "Warning", "You clicked on " + self.__caption + ".\nDo you really want to execute this command ?", Qt.QMessageBox.Ok, ( Qt.QMessageBox.Cancel | Qt.QMessageBox.Default ) )
            if answer == Qt.QMessageBox.Cancel:
                return
        self.getObject( "command" ).executeCommand( self.__parameter )


    def commandStatusChanged( self, pValue ):
        messageList = pValue.split( ",", 2 )
        if len( messageList ) == 2:
            if messageList[0] == "0":   # command info
                logger.info( messageList[1] )
            elif messageList[0] == "1":     # command warning
                logger.warning( messageList[1] )
            elif messageList[0] == "2":     # command error
                logger.error( messageList[1] )

    def expert_mode( self, expert ):
        self.__expertMode = expert
        self.commandPushButton.setEnabled( not self.__expertModeOnly or self.__expertMode )

    def connectionStatusChanged( self, peer ):
        self.calibration_object = peer
        if self.calibration_object is None:
            self.brick_widget.setEnabled( False )
        else:
            self.brick_widget.setEnabled( True )
