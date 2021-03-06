import logging
from Framework4.GUI import Core
from Framework4.GUI.Core import Property, Connection, Signal, Slot
from PyQt4 import QtGui, Qt

logger = logging.getLogger( "MotorAlignmentBrick" )

__category__ = "General"


class MotorAlignmentBrick( Core.BaseBrick ):


    properties = {"caption": Property( "string", "Caption", "", "captionChanged" ),
                  "toolTip": Property( "string", "Tool tip", "", "toolTipChanged" ),
                  "expertModeOnly": Property( "boolean", "Expert mode only", "", "expertModeOnlyChanged", False )}

    connections = {"motoralignment": Connection( "MotorAlignment object",
                                             [Signal( "motorPositionChanged", "motorPositionChanged" )],
                                            [Slot( "moveMotor" ),
                                             Slot( "getMotorPosition" ),
                                             Slot( "getMotorsList" )],
                                             "connectedToMotorAlignment" )}
    signals = [Signal( "executeTestCollect" )]
    slots = []



    def motorPositionChanged( self, pValue ):
        if self.__motorAlignmentDialog is not None:
            self.__motorAlignmentDialog.setMotorPosition( pValue )



    def expert_mode( self, expert ):
        self.__expertMode = expert
        flag = ( not self.__expertModeOnly or self.__expertMode )
        self.motorAlignmentPushButton.setEnabled( flag )
        if not flag and self.__motorAlignmentDialog is not None:
            self.__motorAlignmentDialog.close()

    def __init__( self, *args, **kargs ):
        Core.BaseBrick.__init__( self, *args, **kargs )

    def init( self ):
        self.__toolTip = ""
        self.__motorAlignmentDialog = None
        self.__expertModeOnly = False
        self.__expertMode = False

        self.brick_widget.setLayout( Qt.QVBoxLayout() )
        self.motorAlignmentPushButton = Qt.QPushButton( self.brick_widget )
        Qt.QObject.connect( self.motorAlignmentPushButton, Qt.SIGNAL( "clicked()" ), self.motorAlignmentPushButtonClicked )
        self.brick_widget.layout().addWidget( self.motorAlignmentPushButton )

    def delete( self ):
        pass


    def connectedToMotorAlignment( self, pValue ):
        pass

    def captionChanged( self, pValue ):
        self.motorAlignmentPushButton.setText( pValue )

    def toolTipChanged( self, pValue ):
        self.motorAlignmentPushButton.setToolTip( pValue )

    def expertModeOnlyChanged( self, pValue ):
        self.__expertModeOnly = pValue
        self.expert_mode( self.__expertMode )

    def motorAlignmentPushButtonClicked( self ):
        if self.__motorAlignmentDialog is not None and self.__motorAlignmentDialog.isVisible():
            self.__motorAlignmentDialog.activateWindow()
            self.__motorAlignmentDialog.raise_()
        else:
            motorsList = self.getObject( "motoralignment" ).getMotorsList()
            if motorsList is None:
                Qt.QMessageBox.information( self.brick_widget, "Info", "There are no motors specified!" )
            else:
                logger.debug( 'MotorAlignmentBrick: got motor list %s', motorsList )
                self.__motorAlignmentDialog = MotorAlignmentDialog( self, motorsList )
                self.__motorAlignmentDialog.show()


class MotorAlignmentDialog( Qt.QDialog ):


    def __init__( self, pParent, pMotorList ):
        self.__parent = pParent
        self.__motorsList = pMotorList
        self.__qlabelDict = {}

        Qt.QDialog.__init__( self, self.__parent.brick_widget )
        caption = self.__parent.motorAlignmentPushButton.text()
        if caption == "":
            self.setWindowTitle( "Motor alignment" )
        else:
            self.setWindowTitle( caption )
        self.setLayout( Qt.QVBoxLayout() )
        self.parametersGroupBox = Qt.QGroupBox( "Parameters", self )
        self.parametersGroupBox.setSizePolicy( Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding )
        self.parametersVBoxLayout = Qt.QVBoxLayout( self.parametersGroupBox )
        self.parametersVBoxLayout.setSpacing( 0 )
        self.layout().addWidget( self.parametersGroupBox )


        i = 0
        for name, signal, label in self.__motorsList:
            if i % 2 == 0:
                hBoxLayout = Qt.QHBoxLayout()
                self.parametersVBoxLayout.addLayout( hBoxLayout )
            pushButton = PushButton( label, self )
            pushButton.setParent( self )
            pushButton.setMotor( name )
            pushButton.setSignal( signal )
            Qt.QObject.connect( pushButton, Qt.SIGNAL( "clicked()" ), pushButton.clicked )
            hBoxLayout.addWidget( pushButton )
            i += 1

        self.parametersHBoxLayout1 = Qt.QHBoxLayout()
        self.stepLabel = Qt.QLabel( "Step", self )
        self.stepLabel.setFixedWidth( 80 )
        self.parametersHBoxLayout1.addWidget( self.stepLabel )
        self.stepDoubleSpinBox = Qt.QDoubleSpinBox( self )
        self.stepDoubleSpinBox.setSuffix( " mm" )
        self.stepDoubleSpinBox.setDecimals( 2 )
        self.stepDoubleSpinBox.setRange( 0.01, 1 )
        self.stepDoubleSpinBox.setValue( 0.1 )
        self.stepDoubleSpinBox.setSingleStep( 0.01 )
        self.stepDoubleSpinBox.setToolTip( "Current step" )
        self.parametersHBoxLayout1.addWidget( self.stepDoubleSpinBox )
        self.parametersVBoxLayout.layout().addLayout( self.parametersHBoxLayout1 )

        self.collectTestFrameCheckBox = Qt.QCheckBox( "Collect test frame", self )
        self.collectTestFrameCheckBox.setChecked( True )
        self.collectTestFrameCheckBox.setToolTip( "Enable/disable collection of a test frame after moving motor" )
        self.parametersVBoxLayout.addWidget( self.collectTestFrameCheckBox )

        self.tableWidget = TableWidget( 0, 2, self )
        self.tableWidget.setHorizontalHeaderLabels( ["Motor", "Position"] )
        self.tableWidget.verticalHeader().hide()
        self.tableWidget.setSelectionBehavior( QtGui.QAbstractItemView.SelectRows )
        self.tableWidget.setSelectionMode( QtGui.QAbstractItemView.SingleSelection )
        self.parametersVBoxLayout.addWidget( self.tableWidget )

        self.closePushButton = Qt.QPushButton( "Close", self )
        self.closePushButton.setSizePolicy( Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Fixed )
        self.closePushButton.setToolTip( "Close window" )
        self.layout().addWidget( self.closePushButton )
        Qt.QObject.connect( self.closePushButton, Qt.SIGNAL( "clicked()" ), self.closePushButtonClicked )


        for name, _, _ in self.__motorsList:
            flag = True
            for i in range( 0, self.tableWidget.rowCount() ):
                if self.tableWidget.cellWidget( i, 0 ).text() == name:
                    flag = False
                    break
            if flag:
                i = self.tableWidget.rowCount()
                self.tableWidget.insertRow( i )
                self.tableWidget.setCellWidget( i, 0, Qt.QLabel( Qt.QString( name ) ) )
                position = self.__parent.getObject( "motoralignment" ).getMotorPosition( str( name ) )
                self.__qlabelDict[str( i )] = Qt.QLabel( str( position ) + " mm" )
                self.tableWidget.setCellWidget( i, 1, self.__qlabelDict[str( i )] )



    def setMotorPosition( self, pValue ):
        myList = pValue.split( "," )
        if len( myList ) > 1:
            motor = myList[0]
            position = myList[1]
            for i in range( 0, self.tableWidget.rowCount() ):
                if self.tableWidget.cellWidget( i, 0 ).text() == motor:
                    # Updating dictionary - otherwise there will be overwriting
                    ( self.__qlabelDict[str( i )] ).setText( Qt.QString( position + " mm" ) )
                    break


    def moveMotor( self, pMotor, pDirection ):
        if pDirection == "+":
            step = self.stepDoubleSpinBox.value()
        else:
            step = -self.stepDoubleSpinBox.value()
        logger.info( "Moving motor '%s' by '%s'..." % ( pMotor, step ) )
        self.__parent.getObject( "motoralignment" ).moveMotor( str( pMotor ), step )
        if self.collectTestFrameCheckBox.isChecked():
            self.__parent.emit( "executeTestCollect" )


    def closePushButtonClicked( self ):
        self.accept()



class TableWidget( QtGui.QTableWidget ):

    def __init__( self, *args ):
        QtGui.QTableWidget.__init__( self, *args )


    def resizeEvent( self, _ ):
        size = float( self.width() )
        self.setColumnWidth( 0, round( size / 2, 0 ) - 2 )
        self.setColumnWidth( 1, round( size / 2, 0 ) - 2 )



class PushButton( Qt.QPushButton ):

    def __init__( self, *args ):
        Qt.QPushButton.__init__( self, *args )
        self.__parent = None
        self.__motor = None
        self.__direction = None



    def setParent( self, pParent ):
        self.__parent = pParent



    def setMotor( self, pMotor ):
        self.__motor = pMotor
        self.setToolTip( "Move motor '%s'" % self.__motor )



    def setSignal( self, pDirection ):
        self.__direction = pDirection


    def clicked( self ):
        if self.__motor is not None and self.__direction is not None:
            self.__parent.moveMotor( self.__motor, self.__direction )
