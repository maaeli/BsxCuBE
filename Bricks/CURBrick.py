import logging
from Framework4.GUI import Core
from Framework4.GUI.Core import Property, Connection, Signal, Slot
from PyQt4 import QtCore, QtGui, Qt
from Samples import Sample, CollectPars, SampleList
import cStringIO
import logging
import os.path, time
import pprint
from compiler.ast import For
import traceback

__category__ = "BsxCuBE"


logger = logging.getLogger( "CURBrick" )
rowletters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
class CURBrick( Core.BaseBrick ):


    connections = {"display": Connection( "Display object",
                                    [Signal( "displayResetChanged", "displayResetChanged" ),
                                    Signal( "displayItemChanged", "displayItemChanged" ),
                                    Signal( "transmissionChanged", "transmissionChanged" ),
                                    Signal( "grayOut", "grayOut" )],
                                    [] ),
                   "login": Connection( "Login object",
                                        [Signal( "loggedIn", "loggedIn" )],
                                        [],
                                        "connectionToLogin" )
                   }

    signals = [ ]
    slots = []


    def __init__( self, *args, **kargs ):
        Core.BaseBrick.__init__( self, *args, **kargs )
        self.collectBrickObject = None
        self.collectBrickObject = None

    def init( self ):
        self.__copyLine = []
        self.__history = []


        # To map samples with rows each time we create a sample we give a unique number
        #   the position of a sample in the map should correspond with the row of the sample in the table
        #   throught the operations
        self.sampleIDs = []
        self.sampleIDCount = 0
        self.CBblock = 0     # during swapping callbacks on table rows will be deactivated
        self.filename = ""



        self.bufferNames = []
        self.copiedSample = None


        # Setting configuration for columns in the samples table Widget
        self.column_headers = self.getColumns()
        self.PARAMLABEL_WIDTH = 130
        self.PARAMETERS_WIDTH = 220
        #
        # Style Sheet
        #
        self.brick_widget.setStyleSheet( "*[table=\"true\"] {font-size: 11px} \
                            *[valid=\"true\"]  {background-color: white}\
                            *[valid=\"false\"] {background-color: #f99}\
                            *[sampletype=\"Buffer\"] {background-color: #eec}\
                            *[sampletype=\"Sample\"] {background-color: #cce}" )


        upfile = os.path.join( os.path.dirname( __file__ ), "images/up.jpg" )
        downfile = os.path.join( os.path.dirname( __file__ ), "images/down.jpg" )
        delfile = os.path.join( os.path.dirname( __file__ ), "images/delete.jpg" )

        uppix = Qt.QPixmap( upfile ).scaled( 14, 14 )
        downpix = Qt.QPixmap( downfile ).scaled( 15, 15 )
        delpix = Qt.QPixmap( delfile ).scaled( 10, 10 )

        self.upIcon = Qt.QIcon( uppix )
        self.downIcon = Qt.QIcon( downpix )
        self.deleteIcon = Qt.QIcon( delpix )

        self.brick_widget.setLayout( Qt.QVBoxLayout() )
        mainLayout = self.brick_widget.layout()

        self.robotCheckBox = Qt.QCheckBox( "Collect using SC", self.brick_widget )

        # Note: We use stateChange instead of toggle to avoid infinite loop between CollectBrick and CURBrick
        Qt.QObject.connect( self.robotCheckBox, Qt.SIGNAL( "stateChanged(int)" ), self.__robotCheckBoxToggled )
        mainLayout.addWidget( self.robotCheckBox )

        self.groupBox = Qt.QGroupBox( "Parameters", self.brick_widget )
        self.groupBox.setSizePolicy( Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding )
        # All parameters are grayed out until collect using robot (AKA CUR) checkbox is selected
        self.groupBox.setDisabled( True )
        self.VerticalParametersLayout = Qt.QVBoxLayout( self.groupBox )
        mainLayout.addWidget( self.groupBox )

        # File row layout
        self.hBoxLayout0 = self.getFirstButtonsRowLayout()
        self.VerticalParametersLayout.addLayout( self.hBoxLayout0 )

        # Calibration Type or User defined
        self.optimizationLabel = Qt.QLabel( "Type", self.brick_widget )
        self.optimizationComboBox = Qt.QComboBox( self.brick_widget )
        self.optimizationComboBox.addItems( ["User defined", "BSA Calibration", "Water Calibration" ] )
        Qt.QObject.connect( self.optimizationComboBox, Qt.SIGNAL( "currentIndexChanged(QString)" ), self.loadCalibrationTemplate )
        # Sample Type
        self.sampleTypeLabel = Qt.QLabel( "Sample type", self.brick_widget )
        self.sampleTypeComboBox = Qt.QComboBox( self.brick_widget )
        self.sampleTypeComboBox.addItems( ["Green", "Yellow", "Red"] )
        # put all four together
        self.VerticalParametersLayout.addLayout( self.getHorizontalLabelValueLayoutFactory( [self.optimizationLabel, self.optimizationComboBox, self.sampleTypeLabel, self.sampleTypeComboBox] ) )

        # Storage Temperature
        self.storageTemperatureLabel = Qt.QLabel( "Storage temperature", self.brick_widget )
        self.storageTemperatureDoubleSpinBox = Qt.QDoubleSpinBox( self.brick_widget )
        self.storageTemperatureDoubleSpinBox.setSuffix( " C" )
        self.storageTemperatureDoubleSpinBox.setDecimals( 2 )
        self.storageTemperatureDoubleSpinBox.setRange( 4, 40 )
        self.storageTemperatureDoubleSpinBox.setValue( 4 )

        # Ex. Flow Time
        self.extraFlowTimeLabel = Qt.QLabel( "Extra flow time", self.brick_widget )
        self.extraFlowTimeSpinBox = Qt.QSpinBox( self.brick_widget )
        self.extraFlowTimeSpinBox.setSuffix( " s" )
        self.extraFlowTimeSpinBox.setRange( 0, 900 )
        self.VerticalParametersLayout.addLayout( self.getHorizontalLabelValueLayoutFactory( [self.storageTemperatureLabel, self.storageTemperatureDoubleSpinBox, self.extraFlowTimeLabel, self.extraFlowTimeSpinBox, ] ) )

        # Optimization
        self.optimizationLabel = Qt.QLabel( "Optimization", self.brick_widget )
        self.optimizationComboBox = Qt.QComboBox( self.brick_widget )
        self.optimizationComboBox.addItems( ["None", "Sample SEU temperature", "Sample code and SEU temperature"] )

        # Buffer mode
        self.bufferModeLabel = Qt.QLabel( "Buffer mode", self.brick_widget )
        self.bufferModeComboBox = Qt.QComboBox( self.brick_widget )
        self.bufferModeComboBox.addItems( ["First and After", "Before", "After", "None"] )
        self.VerticalParametersLayout.addLayout( self.getHorizontalLabelValueLayoutFactory( [self.optimizationLabel, self.optimizationComboBox, self.bufferModeLabel, self.bufferModeComboBox] ) )

        # Initial cleaning
        self.initialCleaningLabel = Qt.QLabel( "Initial Cleaning", self.brick_widget )
        self.initialCleaningCheckBox = Qt.QCheckBox( self.brick_widget )
        self.initialCleaningCheckBox.setChecked( 1 )
        self.VerticalParametersLayout.addLayout( self.getHorizontalLabelValueLayoutFactory( [self.initialCleaningLabel, self.initialCleaningCheckBox] ) )

        # History
#        self.historyLabel = Qt.QLabel( "History", self.brick_widget )
#        self.historyLabel.setFixedWidth( self.PARAMLABEL_WIDTH )
#        self.historyText = Qt.QTextEdit( self.brick_widget )
#        self.historyText.setReadOnly( True )
#        self.historyText.setFixedWidth( 600 )
#        self.historyText.setFixedHeight( 80 )
#        self.clearHistoryPushButton = Qt.QPushButton( "Clear", self.brick_widget )
#        self.clearHistoryPushButton.setFixedWidth( 50 )
#        Qt.QObject.connect( self.clearHistoryPushButton, Qt.SIGNAL( "clicked()" ), self.clearHistoryPushButtonClicked )
#        self.historyLabel.setAlignment( QtCore.Qt.AlignTop )
#        self.VerticalParametersLayout.addLayout( self.getHorizontalLayoutFactory( [self.historyLabel, self.historyText, self.clearHistoryPushButton] ) )

        # Sample Table
        self.tableWidget = Qt.QTableWidget( 0, len( self.column_headers ), self.brick_widget )
        self.tableWidget.setHorizontalHeaderLabels( self.column_headers )
        #Set entire table to 11px (see Style Sheet above)
        self.tableWidget.setProperty( "table", "true" )
        self.tableWidget.setFixedHeight( 420 )
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.setColumnWidth( self.SAMPLETYPE_COLUMN, 70 )
        self.tableWidget.setColumnWidth( self.PLATE_COLUMN, 45 )
        self.tableWidget.setColumnWidth( self.ROW_COLUMN, 45 )
        self.tableWidget.setColumnWidth( self.WELL_COLUMN, 45 )
        self.tableWidget.setColumnWidth( self.COMMENTS_COLUMN, 80 )
        self.tableWidget.setColumnWidth( self.MACROMOLECULE_COLUMN, 110 )
        self.tableWidget.setColumnWidth( self.CODE_COLUMN, 80 )
        self.tableWidget.setColumnWidth( self.VOLUME_COLUMN, 60 )
        self.tableWidget.setSelectionBehavior( Qt.QAbstractItemView.SelectRows )
        self.tableWidget.setSelectionMode( Qt.QAbstractItemView.SingleSelection )

        self.VerticalParametersLayout.addLayout( self.getHorizontalLayoutFactory( [self.tableWidget] ) )
        # Buttons at the end
        self.addPushButton = Qt.QPushButton( "Add Sample", self.brick_widget )
        Qt.QObject.connect( self.addPushButton, Qt.SIGNAL( "clicked()" ), self.addPushButtonClicked )

        self.copyPushButton = Qt.QPushButton( "Copy Sample", self.brick_widget )
        Qt.QObject.connect( self.copyPushButton, Qt.SIGNAL( "clicked()" ), self.copyPushButtonClicked )
        self.copyPushButton.setEnabled( 0 )

        self.pastePushButton = Qt.QPushButton( "Paste Sample", self.brick_widget )
        Qt.QObject.connect( self.pastePushButton, Qt.SIGNAL( "clicked()" ), self.pastePushButtonClicked )
        self.pastePushButton.setEnabled( 0 )

        self.clearPushButton = Qt.QPushButton( "Clear Configuration", self.brick_widget )
        Qt.QObject.connect( self.clearPushButton, Qt.SIGNAL( "clicked()" ), self.clearConfigurationPushButtonClicked )

        self.VerticalParametersLayout.addLayout( self.getGridLayoutFactory( [self.addPushButton, self.copyPushButton, self.pastePushButton, Qt.QLabel( "" ), Qt.QLabel( "" ), Qt.QLabel( "" ), self.clearPushButton ] ) )





    def getFirstButtonsRowLayout ( self ):
        self.fileLabel = Qt.QLabel( "File", self.brick_widget )
        self.fileLabel.setFixedWidth( self.PARAMLABEL_WIDTH )
        self.fileLineEdit = Qt.QLineEdit( self.brick_widget )
        self.fileLineEdit.setMaxLength( 100 )
        self.fileLineEdit.setFixedWidth( 400 )
        self.fileLineEdit.setEnabled( False )

        self.loadPushButton = Qt.QPushButton( "Load new", self.brick_widget )
        self.loadPushButton.setFixedWidth( 70 )
        Qt.QObject.connect( self.loadPushButton, Qt.SIGNAL( "clicked()" ), self.loadPushButtonClicked )

        self.savePushButton = Qt.QPushButton( "Save", self.brick_widget )
        self.savePushButton.setFixedWidth( 70 )
        Qt.QObject.connect( self.savePushButton, Qt.SIGNAL( "clicked()" ), self.savePushButtonClicked )

        self.saveAsPushButton = Qt.QPushButton( "Save as", self.brick_widget )
        self.saveAsPushButton.setFixedWidth( 70 )
        Qt.QObject.connect( self.saveAsPushButton, Qt.SIGNAL( "clicked()" ), self.saveAsPushButtonClicked )
        return self.getHorizontalLayoutFactory( [self.fileLabel, self.fileLineEdit, self.loadPushButton, self.savePushButton, self.saveAsPushButton] )



#        self.fillspace = Qt.QLabel( "" )
#        self.hBoxLayout16.addWidget( self.fillspace )



    def getHorizontalLabelValueLayoutFactory ( self, widgets ):
        # only works with 2 or 4
        if len( widgets ) == 2:
            widgets[0].setFixedWidth( self.PARAMLABEL_WIDTH )
            widgets[1].setFixedWidth( self.PARAMETERS_WIDTH )
            return self.getHorizontalLayoutFactory( [widgets[0], widgets[1]] )
        if len( widgets ) == 4:
            widgets[0].setFixedWidth( self.PARAMLABEL_WIDTH )
            widgets[1].setFixedWidth( self.PARAMETERS_WIDTH )
            widgets[2].setFixedWidth( self.PARAMLABEL_WIDTH )
            widgets[3].setFixedWidth( self.PARAMETERS_WIDTH )
            # we add a QLabel to make sure we have two rows not too close together
            return self.getHorizontalLayoutFactory( [widgets[0], widgets[1], Qt.QLabel( " "*10 ), widgets[2], widgets[3]] )

        return self.getHorizontalLayoutFactory( [] )


    def getGridLayoutFactory ( self, widgets ):
        gridBoxLayout = QtGui.QGridLayout()
        count = 0
        for widget in widgets:
            gridBoxLayout.addWidget( widget, 0, count )
            count = count + 1
        return gridBoxLayout

    def getHorizontalLayoutFactory ( self, widgets ):
        hBoxLayout = Qt.QHBoxLayout()
        hBoxLayout.setAlignment( QtCore.Qt.AlignLeft )
        for widget in widgets:
            hBoxLayout.addWidget( widget )
        return hBoxLayout

    def getColumns ( self ):
        self.UP_COLUMN = 0
        self.DOWN_COLUMN = 1
        self.ENABLE_COLUMN = 2
        self.SAMPLETYPE_COLUMN = 3
        self.PLATE_COLUMN = 4
        self.ROW_COLUMN = 5
        self.WELL_COLUMN = 6
        self.CONCENTRATION_COLUMN = 7
        self.COMMENTS_COLUMN = 8
        self.MACROMOLECULE_COLUMN = 9
        self.CODE_COLUMN = 10
        self.VISCOSITY_COLUMN = 11
        self.BUFFERNAME_COLUMN = 12
        self.TRANSMISSION_COLUMN = 13
        self.VOLUME_COLUMN = 14
        self.TEMPERATURE_COLUMN = 15
        self.FLOW_COLUMN = 16
        self.RECUPERATE_COLUMN = 17
        self.WAITTIME_COLUMN = 18
        self.DELETE_COLUMN = 19
        return [ "", "", "Use", "Type", "Plate", "Row", "Well", \
                                "Concentration", "Comments", "Macromol.", "Code", "Viscosity", "Buffername", \
                                "Transmission", "Volume", "SEU Temp", "Flow", "Recup", \
                                "Wait", "Del"]


   # When connected to Login, then block the brick
    def connectionToLogin( self, pPeer ):
        if pPeer is not None:
            self.brick_widget.setEnabled( False )

    # Logged In : True or False 
    def loggedIn( self, pValue ):
        self.brick_widget.setEnabled( pValue )
        # add automatically the robot from CollectBrick
        robotFileName = self.collectBrickObject.getRobotFileName()
        self.fileLineEdit.setText( robotFileName )
        if not os.path.exists( robotFileName ):
            if robotFileName != "":
                Qt.QMessageBox.critical( self.brick_widget, "Error", "Robot file %r does not exist anymore. I will start with an empty one" % robotFileName, Qt.QMessageBox.Ok )
            self.fileLineEdit.setText( "" )
            self.collectBrickObject.setRobotFileName( "" )

        if os.path.exists( robotFileName ):
            filename = str( robotFileName )
            self.loadFile( filename )

    # Connect to display 
    def grayOut( self, grayout ):
        if grayout is not None:
            if grayout:
                self.brick_widget.setEnabled( False )
            else:
                self.brick_widget.setEnabled( True )

    def displayResetChanged( self ):
        pass

    def displayItemChanged( self, __ ):
        pass

    def transmissionChanged( self, __ ):
        pass


#TODO: Staffan's note: take it away
#    def clearHistory( self ):
#        self.historyText.clear()
#TODO: Staffan's note: take it away
#    def addHistory( self, pLevel, pMessage ):
#        strLevel = ['INFO', 'WARNING', 'ERROR']
#        message = "<i>[%s] %s:</i> <b>%s</b>" % ( time.strftime( "%Y/%m/%d %H:%M:%S" ), strLevel[ pLevel] , pMessage )
#
#        self.historyText.append( message )

    def getCollectRobotPars( self, isAll = 0 ):
        params = CollectPars()
        sampleList = SampleList()
        bufferList = SampleList()

        params.sampleType = self.sampleTypeComboBox.currentText()
        params.storageTemperature = self.storageTemperatureDoubleSpinBox.value()
        params.extraFlowTime = self.extraFlowTimeSpinBox.value()
        params.optimization = self.optimizationComboBox.currentIndex()
        params.optimizationText = self.optimizationComboBox.currentText()
        params.initialCleaning = self.initialCleaningCheckBox.isChecked()
        params.bufferMode = self.bufferModeComboBox.currentIndex()


        #=================================================
        #  myBuffer mode
        #=================================================
        params.bufferFirst = False
        params.bufferBefore = False
        params.bufferAfter = False

        if params.bufferMode == 0:
            params.bufferFirst = True
            params.bufferAfter = True
        elif params.bufferMode == 1:
            params.bufferBefore = True
        elif params.bufferMode == 2:
            params.bufferAfter = True

        #=================================================
        # optimization mode
        #=================================================
        params.optimSEUtemp = False
        params.optimCodeAndSEU = False

        if params.optimization == 1:
            params.optimSEUtemp = True
        elif params.optimization == 2:
            params.optimCodeAndSEU = True


        # add alll samples into bufferList and sampleList
        for i in range( 0, self.tableWidget.rowCount() ):
            sample = self.getSampleRow( i )

            if isAll or sample.enable:
                if sample.isBuffer():
                    bufferList.append( sample )
                else:
                    sampleList.append( sample )

        #=================================================
        #  assign myBuffer to sample
        #  TODO:  allow to assign more than one myBuffer. isAll with same name
        #=================================================
        for sample in sampleList:
            sample.buffer = []
            if len( bufferList ) == 1:   # if there is one and only one myBuffer defined dont look at name. assign
                sample.buffer.append( bufferList[0] )
            else:
                for myBuffer in bufferList:
                    if myBuffer.buffername == sample.buffername:
                        sample.buffer.append( myBuffer )


        # Optimize data collection procedure (if requested)
        if params.optimSEUtemp:
            sampleList.sortSEUtemp()
        elif params.optimCodeAndSEU:
            sampleList.sortCodeAndSEU()

        params.sampleList = sampleList
        params.bufferList = bufferList

        return params

    def loadPushButtonClicked( self ):
        dirname = ""
        self.filename = str( self.fileLineEdit.text() )
        if self.filename != "":
            dirname = os.path.split( self.filename )[0]
        else:
            try:
                dirname = os.path.split( self.collectBrickObject.collectpars.directory )
            except Exception, e:
                print "Ignored Exception 6: " + str( e )
                traceback.print_exc()

        filename = Qt.QFileDialog.getOpenFileName( self.brick_widget, "Choose a new file to load", dirname, "XML File (*.xml)" )

        if not filename:
            return

        self.fileLineEdit.setText( filename )

        filename = str( filename )
        self.loadFile( filename )

    def loadFile( self, filename ):
        try:
            myPars = CollectPars( filename )
            self.clearConfiguration()

            #  Clear first if load was succesful
            # 
            for sampleID in self.sampleIDs:
                index = self.sampleIDs.index( sampleID )
                self.tableWidget.removeRow( index )
                self.sampleIDs.remove( sampleID )

            # 
            # General parameters
            # 
            self.CBblock = 1
            self.setComboBox( self.sampleTypeComboBox, myPars.sampleType )

            self.storageTemperatureDoubleSpinBox.setValue( float( myPars.storageTemperature ) )
            self.extraFlowTimeSpinBox.setValue( float( myPars.extraFlowTime ) )

            self.initialCleaningCheckBox.setChecked( myPars.initialCleaning )

            # These are saved by index
            self.optimizationComboBox.setCurrentIndex( myPars.optimization )
            self.bufferModeComboBox.setCurrentIndex( myPars.bufferMode )

            #TODO: Staffan's note: take it away
#            self.historyText.clear()
#            self.historyText.setText( myPars.history.strip() )

            for myBuffer in  myPars.bufferList:
                self.addSampleRow( myBuffer )
            for sample in  myPars.sampleList:
                self.addSampleRow( sample )

            self.CBblock = 0
            self.filename = filename
            self.collectBrickObject.setRobotFileName( filename )
            # strip all but the last part for label 
            self.collectBrickObject.changexmlLabel( filename )

        except Exception:
            logger.exception( 'Cannot load collection parameters file. \n' )
            Qt.QMessageBox.critical( self.brick_widget, "Error", "Error when trying to read file '%s'!" % filename )

    def saveAsPushButtonClicked( self ):
        self.filename = str( self.fileLineEdit.text() )
        filename = Qt.QFileDialog.getSaveFileName( self.brick_widget, "Choose a file to save", self.filename, "XML File (*.xml)" )
        if not filename:
            return

        filename = str( filename )

        if not str( filename ).lower().endswith( ".xml" ):
            filename += ".xml"
            self.fileLineEdit.setText( filename )

        self.filename = filename
        self.fileLineEdit.setText( filename )
        self.saveFile( filename )

        # Update robot file
        self.collectBrickObject.setRobotFileName( filename )
        # strip all but the last part for label 
        self.collectBrickObject.changexmlLabel( filename )

    def savePushButtonClicked( self ):
        if self.filename == "" or not os.path.isfile( self.filename ):
            self.saveAsPushButtonClicked()
        else:
            self.saveFile( self.filename , askrewrite = False )

    def saveFile( self, filename, askrewrite = True ):

        if os.path.exists( filename ):
            quitsave = Qt.QMessageBox.question( self.brick_widget, "Warning", "The file '%s' already exists. Overwrite it?" % filename, Qt.QMessageBox.Yes, Qt.QMessageBox.No, Qt.QMessageBox.NoButton ) != Qt.QMessageBox.Yes
            if quitsave:
                return

        myPars = self.getCollectRobotPars( isAll = 1 )
        #TODO: Staffan's note: take it away 
        #history = self.historyText.toPlainText()
        #TODO: remove if going back on history
        history = "No History in this version"

        try:
            if os.path.exists( filename ):
                #TODO: Staffan's note: take it away
                myPars.save( filename , history )
                Qt.QMessageBox.information( self.brick_widget, "Info", "The new version of the file '%s' was successfully saved!" % filename )
            else:
                myPars.save( filename , history )
                Qt.QMessageBox.information( self.brick_widget, "Info", "A new version of the file '%s' was successfully saved!" % filename )
        except Exception, e:
            import traceback
            traceback.print_exc()
            logger.exception( 'Cannot save collection parameters file.\n' )
            logger.error( "Full Exception: " + str( e ) )
            Qt.QMessageBox.critical( self.brick_widget, "Error", "Error when trying to save file '%s'!" % filename )


    #
    # Callbacks for table widgets
    #
    @Qt.pyqtSlot( int )
    def enableCheckBoxToggled( self, sampleID ):

        if self.CBblock:
            return
        try:
            index = self.sampleIDs.index( sampleID )
            checked = self.tableWidget.cellWidget( index, self.ENABLE_COLUMN ).isChecked()
            for col in range( 0, self.tableWidget.columnCount() ):
                if col != self.ENABLE_COLUMN:
                    self.tableWidget.cellWidget( index, col ).setEnabled( checked )
        except AttributeError:
            pass

    @Qt.pyqtSlot( int )
    def bufferComboBoxChanged( self, sampleID ):
        if self.CBblock:
              return

        try:
            index = self.sampleIDs.index( sampleID )

            well_type = str( self.tableWidget.cellWidget( index, self.SAMPLETYPE_COLUMN ).currentText() )

            if well_type == "Sample":
                return

            self.bufferNames = self.getBufferNames()
            self.assignBufferNames()
        except AttributeError:
            pass

    @Qt.pyqtSlot( int )
    def typeComboBoxChanged( self, sampleID ):
        if self.CBblock:
              return

        try:
            index = self.sampleIDs.index( sampleID )

            self.CBblock = 1
            self.assignOneBufferName( index, None )
            self.CBblock = 0

            self.formatLine( index )
        except AttributeError:
            pass

    @Qt.pyqtSlot( int )
    def plateComboBoxChanged( self, sampleID ):
        if self.CBblock:
              return

        plateInfos = self.getPlatesInfos()

        try:
            index = self.sampleIDs.index( sampleID )
            platevalue = self.tableWidget.cellWidget( index, self.PLATE_COLUMN ).currentIndex()

            row = self.tableWidget.cellWidget( index, self.ROW_COLUMN )
            well = self.tableWidget.cellWidget( index, self.WELL_COLUMN )

            nrows = int( plateInfos[platevalue][0] )
            ncols = int( plateInfos[platevalue][1] )

            #rowvalues  = [str(val) for val in range(1,nrows+1) ] 
            rowvalues = rowletters[:nrows]
            wellvalues = [str( val ) for val in range( 1, ncols + 1 ) ]

            row.clear()
            well.clear()

            row.addItems ( rowvalues )
            well.addItems( wellvalues )

        except AttributeError:
            pass


    def setComboBox( self, combo, value ):
        for i in range( combo.count() ):
            if value == combo.itemText( i ):
                combo.setCurrentIndex( i )
                break
        else:
            combo.setCurrentIndex( 0 )

    def getSampleRow( self, i ):
        table = self.tableWidget
        sampleRow = Sample()

        sampleRow.enable = table.cellWidget( i, self.ENABLE_COLUMN ).isChecked()
        sampleRow.type = str( table.cellWidget( i, self.SAMPLETYPE_COLUMN ).currentText() )
        sampleRow.typen = table.cellWidget( i, self.SAMPLETYPE_COLUMN ).currentIndex()
        sampleRow.plate = str( table.cellWidget( i, self.PLATE_COLUMN ).currentText() )
        #sampleRow.row            =  str(table.cellWidget(i, self.ROW_COLUMN).currentText())   
        rowtxt = str( table.cellWidget( i, self.ROW_COLUMN ).currentText() )
        sampleRow.row = rowletters.index( rowtxt ) + 1
        sampleRow.well = str( table.cellWidget( i, self.WELL_COLUMN ).currentText() )
        sampleRow.concentration = table.cellWidget( i, self.CONCENTRATION_COLUMN ).value()
        sampleRow.comments = str( table.cellWidget( i, self.COMMENTS_COLUMN ).text() )
        sampleRow.macromolecule = str( table.cellWidget( i, self.MACROMOLECULE_COLUMN ).text() )
        sampleRow.code = str( table.cellWidget( i, self.CODE_COLUMN ).text() )
        sampleRow.viscosity = str( table.cellWidget( i, self.VISCOSITY_COLUMN ).currentText() )
        sampleRow.buffername = str( table.cellWidget( i, self.BUFFERNAME_COLUMN ).currentText() )
        sampleRow.transmission = table.cellWidget( i, self.TRANSMISSION_COLUMN ).value()
        sampleRow.volume = table.cellWidget( i, self.VOLUME_COLUMN ).value()
        sampleRow.flow = table.cellWidget( i, self.FLOW_COLUMN ).isChecked()
        sampleRow.recuperate = table.cellWidget( i, self.RECUPERATE_COLUMN ).isChecked()
        if sampleRow.type == 'Sample':
            sampleRow.SEUtemperature = table.cellWidget( i, self.TEMPERATURE_COLUMN ).value()
            sampleRow.waittime = table.cellWidget( i, self.WAITTIME_COLUMN ).value()
        else:
            sampleRow.SEUtemperature = 4.0
            sampleRow.waittime = 0.0
        sampleRow.title = sampleRow.getTitle()

        return sampleRow

    def addSampleRow( self, sample = None, index = -1 ):

        if sample is None:
            samp = Sample()
            if self.tableWidget.rowCount() == 0:
                samp.type = "Buffer"
            else:
                samp.type = "Sample"
        else:
            samp = sample

        if index == -1:
            index = self.tableWidget.rowCount()

        self.createSampleRow( index )
        self.setSampleRow( index, samp )

        self.copyPushButton.setEnabled( 1 )
        self.tableWidget.setRangeSelected( Qt.QTableWidgetSelectionRange( 0, 0, index - 1, len( self.column_headers ) - 1 ), 0 )
        self.tableWidget.setRangeSelected( Qt.QTableWidgetSelectionRange( index, 0, index, len( self.column_headers ) - 1 ), 1 )
        self.tableWidget.setCurrentCell( index, 0 )

    def removeSampleRow( self, sid ):

        index = self.sampleIDs.index( sid )
        self.tableWidget.removeRow( index )
        self.sampleIDs.remove( sid )

        if self.tableWidget.rowCount() == 0:
            self.copyPushButton.setEnabled( 0 )

    def setSampleRow( self, index, sample ):

        tableWidget = self.tableWidget

        plateInfos = self.getPlatesInfos()

        # enable
        tableWidget.cellWidget( index, self.ENABLE_COLUMN ).setChecked( sample.enable )

        # type
        typeComboBox = tableWidget.cellWidget( index, self.SAMPLETYPE_COLUMN )
        self.setComboBox ( typeComboBox, sample.type )

        # plate, row, well
        plateComboBox = tableWidget.cellWidget( index, self.PLATE_COLUMN )
        rowComboBox = tableWidget.cellWidget( index, self.ROW_COLUMN )
        wellComboBox = tableWidget.cellWidget( index, self.WELL_COLUMN )

        plate = ( sample.plate is not None ) and ( int( sample.plate ) - 1 ) or 0
        row = ( sample.row   is not None ) and ( int( sample.row ) - 1 )   or 0
        well = ( sample.well  is not None ) and ( int( sample.well ) - 1 )  or 0

        if plate >= len( plateInfos ) or plate < 0: plate = 0

        nplates = len( plateInfos )
        nrows = int( plateInfos[plate][0] )
        nwells = int( plateInfos[plate][1] )

        if row >= nrows  or row < 0:  row = 0
        if well >= nwells or well < 0: well = 0

        plates = [str( num ) for num in range( 1, nplates + 1 )]
        #rows   = [str(num) for num in range(1,nrows+1)]
        rows = rowletters[:nrows]
        wells = [str( num ) for num in range( 1, nwells + 1 )]

        plateComboBox.clear()

        plateComboBox.addItems( plates )
        plateComboBox.setCurrentIndex( plate )

        rowComboBox.clear()
        wellComboBox.clear()

        rowComboBox.addItems( rows )
        wellComboBox.addItems( wells )

        rowComboBox.setCurrentIndex( row )
        wellComboBox.setCurrentIndex( well )

        # concentration
        concentrationDoubleSpinBox = tableWidget.cellWidget( index, self.CONCENTRATION_COLUMN )
        concentrationDoubleSpinBox.setValue( sample.concentration )

        # comments
        commentsLineEdit = tableWidget.cellWidget( index, self.COMMENTS_COLUMN )
        commentsLineEdit.setText( sample.comments )

        # code 
        codeLineEdit = tableWidget.cellWidget( index, self.CODE_COLUMN )
        codeLineEdit.setText( sample.code )

        # macromolecule 
        macromoleculeLineEdit = tableWidget.cellWidget( index, self.MACROMOLECULE_COLUMN )
        macromoleculeLineEdit.setText( sample.macromolecule )

        # viscosity
        viscosityComboBox = tableWidget.cellWidget( index, self.VISCOSITY_COLUMN )
        self.setComboBox( viscosityComboBox, sample.viscosity )

        # buffername
        bufferComboBox = tableWidget.cellWidget( index, self.BUFFERNAME_COLUMN )

        if sample.type == "Buffer":
            if sample.buffername not in self.bufferNames:
                self.bufferNames.append( sample.buffername )
        self.assignOneBufferName( index, sample.buffername )

        # transmission
        transmissionDoubleSpinBox = tableWidget.cellWidget( index, self.TRANSMISSION_COLUMN )
        transmissionDoubleSpinBox.setValue( sample.transmission )

        # volume
        volumeDoubleSpinBox = tableWidget.cellWidget( index, self.VOLUME_COLUMN )
        volumeDoubleSpinBox.setValue( sample.volume )

        # flow
        flowCheckBox = tableWidget.cellWidget( index, self.FLOW_COLUMN )
        flowCheckBox.setChecked( sample.flow )

        # recuperate
        recuperateCheckBox = tableWidget.cellWidget( index, self.RECUPERATE_COLUMN )
        recuperateCheckBox.setChecked( sample.recuperate )

        # waittime
        if sample.type != 'Buffer':
            waittimeSpinBox = tableWidget.cellWidget( index, self.WAITTIME_COLUMN )
            waittimeSpinBox.setValue( sample.waittime )
        # temperature SEU
        if sample.type != 'Buffer':
            temperatureSEUDoubleSpinBox = tableWidget.cellWidget( index, self.TEMPERATURE_COLUMN )
            temperatureSEUDoubleSpinBox.setValue( sample.SEUtemperature )


        # final arrangements
        self.formatLine( index, sample )


    def formatLine( self, index, sample = None ):

        table = self.tableWidget
        concentration = table.cellWidget( index, self.CONCENTRATION_COLUMN )
        seutemperature = table.cellWidget( index, self.TEMPERATURE_COLUMN )
        bufcombo = table.cellWidget( index, self.BUFFERNAME_COLUMN )

        well_type = str( self.tableWidget.cellWidget( index, self.SAMPLETYPE_COLUMN ).currentText() )

        if well_type == 'Buffer':
            concentration.setValue( 0 )
            concentration.setEnabled( False )
            bufcombo.setEditable( True )
            seutemperature.setEnabled( False )
            self.tableWidget.setCellWidget( index, self.WAITTIME_COLUMN, Qt.QLabel() )
            self.tableWidget.setCellWidget( index, self.TEMPERATURE_COLUMN, Qt.QLabel() )
        elif well_type == 'Sample':
            concentration.setEnabled( True )
            seutemperature.setEnabled( True )

            temperatureSEUDoubleSpinBox = Qt.QDoubleSpinBox( self.tableWidget )
            temperatureSEUDoubleSpinBox.setSuffix( " C" )
            temperatureSEUDoubleSpinBox.setDecimals( 2 )
            temperatureSEUDoubleSpinBox.setRange( 4, 60 )
            self.tableWidget.setCellWidget( index, self.TEMPERATURE_COLUMN, temperatureSEUDoubleSpinBox )

            waittimeSpinBox = Qt.QDoubleSpinBox( self.tableWidget )
            waittimeSpinBox.setSuffix( " s" )
            waittimeSpinBox.setDecimals( 0 )
            waittimeSpinBox.setRange( 0, 10000 )

            self.tableWidget.setCellWidget( index, self.WAITTIME_COLUMN, waittimeSpinBox )

            bufcombo.setEditable( False )

            if sample:
                temperatureSEUDoubleSpinBox.setValue( sample.SEUtemperature )
                waittimeSpinBox.setValue( sample.waittime )

        for i in range( len( self.column_headers ) ):
            self.tableWidget.cellWidget( index, i ).setProperty( "sampletype", well_type )

        self.brick_widget.setStyleSheet( self.brick_widget.styleSheet() )

    def getBufferNames( self ):
        bufferNames = []
        for index in range( self.tableWidget.rowCount() ):
            # get all buffer names first
            well_type = str( self.tableWidget.cellWidget( index, self.SAMPLETYPE_COLUMN ).currentText() )
            if well_type == "Buffer":
                bufferName = str( self.tableWidget.cellWidget( index, self.BUFFERNAME_COLUMN ).currentText() )
                if bufferName not in bufferNames:
                    bufferNames.append( bufferName )
        return bufferNames


    def assignBufferNames( self ):

        for index in range( self.tableWidget.rowCount() ):
            well_type = str( self.tableWidget.cellWidget( index, self.SAMPLETYPE_COLUMN ).currentText() )
            if well_type == "Sample":
                currentBuffer = str( self.tableWidget.cellWidget( index, self.BUFFERNAME_COLUMN ).currentText() )
                self.assignOneBufferName( index, currentBuffer )

    def assignOneBufferName( self, index, value ):
        try:
            self.tableWidget.cellWidget( index, self.BUFFERNAME_COLUMN ).clear()
            self.tableWidget.cellWidget( index, self.BUFFERNAME_COLUMN ).addItems( self.bufferNames )
            idx = self.bufferNames.index( value )
            if idx != -1:
                self.tableWidget.cellWidget( index, self.BUFFERNAME_COLUMN ).setCurrentIndex( idx )
        except AttributeError:
            pass     # there are some uncaught exceptions because when deleting samples some of the callbacks are still there. How to delete the callback?
        except ValueError:
            pass

    def addPushButtonClicked( self ):
        index = self.tableWidget.currentRow()
        self.addSampleRow( index = index + 1 )

    def copyPushButtonClicked( self ):
        index = self.tableWidget.currentRow()
        self.copiedSample = self.getSampleRow( index )
        self.pastePushButton.setEnabled( 1 )

    def pastePushButtonClicked( self ):
        index = self.tableWidget.currentRow()
        self.addSampleRow( index = index + 1 )
        if self.copiedSample is not None:
            self.setSampleRow( index + 1, self.copiedSample )

    @Qt.pyqtSlot( int )
    def upPushButtonClicked( self, sampleID1 ):

        index1 = self.sampleIDs.index( sampleID1 )
        if index1 < 1:
            return

        sampleID2 = self.sampleIDs[index1 - 1]

        self.swapRows( sampleID1, sampleID2 )


    @Qt.pyqtSlot( int )
    def downPushButtonClicked( self, sampleID2 ):

        index2 = self.sampleIDs.index( sampleID2 )
        if index2 >= ( self.tableWidget.rowCount() - 1 ):
            return

        sampleID1 = self.sampleIDs[index2 + 1]

        self.swapRows( sampleID1, sampleID2 )

    def swapRows( self, sid1, sid2 ):

        index1 = self.sampleIDs.index( sid1 )
        index2 = self.sampleIDs.index( sid2 )

        sample1 = self.getSampleRow( index1 )
        sample2 = self.getSampleRow( index2 )

        self.CBblock = 1    # to protect callbacks from doing things during swapping

        self.removeSampleRow( sid1 )
        self.addSampleRow( sample2, index1 )

        self.removeSampleRow( sid2 )
        self.addSampleRow( sample1, index2 )

        self.CBblock = 0


    @Qt.pyqtSlot( int )
    def deletePushButtonClicked( self, sampleID ):
        self.removeSampleRow( sampleID )

    def clearConfigurationPushButtonClicked( self ):
        if Qt.QMessageBox.question( self.brick_widget, "Warning", "Do you really want to clear the current configuration?", Qt.QMessageBox.Yes, Qt.QMessageBox.No, Qt.QMessageBox.NoButton ) == Qt.QMessageBox.Yes:
            self.fileLineEdit.setText( "" )
            self.clearConfiguration()

    def clearConfiguration( self ):
        self.sampleTypeComboBox.setCurrentIndex( 0 )
        self.storageTemperatureDoubleSpinBox.setValue( 0 )
        self.optimizationComboBox.setCurrentIndex( 0 )
        self.extraFlowTimeSpinBox.setValue( 0 )
        self.initialCleaningCheckBox.setChecked( 1 )
        self.bufferModeComboBox.setCurrentIndex( 0 )
        self.copyPushButton.setEnabled( 0 )
        self.pastePushButton.setEnabled( 0 )
        #TODO: Staffan's note: take it away
        #self.historyText.clear()

        while self.tableWidget.rowCount() > 0:
            self.tableWidget.removeRow( 0 )


#    def clearHistoryPushButtonClicked( self ):
#        if Qt.QMessageBox.question( self.brick_widget, "Warning", "Do you really want to clear the current history?", Qt.QMessageBox.Yes, Qt.QMessageBox.No, Qt.QMessageBox.NoButton ) == Qt.QMessageBox.Yes:
#            self.historyText.clear()

    def closePushButtonClicked( self ):
        self.accept()

    def grayOutParameters( self, pValue ):
        self.groupBox.setEnabled( pValue )


    def loadCalibrationTemplate( self, pValue ):
        if str( pValue ) == "User defined" :
            # activate load new button
            self.loadPushButton.setEnabled( 1 )
            self.savePushButton.setEnabled ( 1 )
            # We hit none, let us reload orig filename
            self.loadFile( self.filename )
        else:
            # gray out "Load new" 
            self.savePushButton.setEnabled ( 0 )
            self.loadPushButton.setEnabled ( 0 )
            templateDirectory = self.collectBrickObject.getTemplateDirectory()
            filename = str( templateDirectory + "/" + str( pValue ).split( " " )[0] + ".xml" )
            self.loadFile( filename )

    def __robotCheckBoxToggled( self, pValue ):
       self.collectBrickObject.robotCheckBoxToggled( pValue )

    def getPlatesNumber ( self ):
        if self.collectBrickObject is not None:
            return self.collectBrickObject.nbPlates
        return 0

    def getPlatesInfos ( self ):
        if self.collectBrickObject is not None:
            return self.collectBrickObject.plateInfos
        return []

    # This one creates a gui for each row
    def createSampleRow( self, row ):

        sampleID = self.sampleIDCount
        self.sampleIDCount += 1

        self.sampleIDs.insert( row, sampleID )

        tableWidget = self.tableWidget

        tableWidget.insertRow( row )

        # buttons
        upButton = Qt.QPushButton( self.upIcon, "", tableWidget )
        upButton.setFlat( True )
        downButton = Qt.QPushButton( self.downIcon, "", tableWidget )
        downButton.setFlat( True )
        deleteButton = Qt.QPushButton( self.deleteIcon, "", tableWidget )
        deleteButton.setFlat( True )
        tableWidget.setCellWidget( row, self.UP_COLUMN, upButton )
        tableWidget.setCellWidget( row, self.DOWN_COLUMN, downButton )
        tableWidget.setCellWidget( row, self.DELETE_COLUMN, deleteButton )

        # TODO.  Signal mapppers keep row at the moment of creation...but row number changes with these actions.
        #    we have to imagine another parameter
        upSignalMapper = Qt.QSignalMapper( self.brick_widget )
        upSignalMapper.setMapping( upButton, sampleID )
        upButton.clicked.connect( upSignalMapper.map )
        upSignalMapper.mapped[int].connect( self.upPushButtonClicked )

        downSignalMapper = Qt.QSignalMapper( self.brick_widget )
        downSignalMapper.setMapping( downButton, sampleID )
        downButton.clicked.connect( downSignalMapper.map )
        downSignalMapper.mapped[int].connect( self.downPushButtonClicked )

        deleteSignalMapper = Qt.QSignalMapper( self.brick_widget )
        deleteSignalMapper.setMapping( deleteButton, sampleID )
        deleteButton.clicked.connect( deleteSignalMapper.map )
        deleteSignalMapper.mapped[int].connect( self.deletePushButtonClicked )


        # enable 
        enableCheckBox = Qt.QCheckBox( tableWidget )
        tableWidget.setCellWidget( row, self.ENABLE_COLUMN, enableCheckBox )

        eSignalMapper = Qt.QSignalMapper( self.brick_widget )
        eSignalMapper.setMapping( enableCheckBox, sampleID )
        enableCheckBox.toggled.connect( eSignalMapper.map )
        eSignalMapper.mapped[int].connect( self.enableCheckBoxToggled )

        # type
        typeComboBox = Qt.QComboBox( tableWidget )
        typeComboBox.addItems( ["Buffer", "Sample"] )
        tableWidget.setCellWidget( row, self.SAMPLETYPE_COLUMN, typeComboBox )

        # use QSignalMapper to pass row as argument to the event handler
        tSignalMapper = Qt.QSignalMapper( self.brick_widget )
        tSignalMapper.setMapping( typeComboBox, sampleID )
        typeComboBox.currentIndexChanged.connect( tSignalMapper.map )
        tSignalMapper.mapped[int].connect( self.typeComboBoxChanged )

        # plate
        plateComboBox = Qt.QComboBox( tableWidget )
        tableWidget.setCellWidget( row, self.PLATE_COLUMN, plateComboBox )

        # use QSignalMapper to pass row as argument to the event handler
        pSignalMapper = Qt.QSignalMapper( self.brick_widget )
        pSignalMapper.setMapping( plateComboBox, sampleID )
        plateComboBox.currentIndexChanged.connect( pSignalMapper.map )
        pSignalMapper.mapped[int].connect( self.plateComboBoxChanged )


        # row
        rowComboBox = Qt.QComboBox( tableWidget )
        tableWidget.setCellWidget( row, self.ROW_COLUMN, rowComboBox )

        # well
        wellComboBox = Qt.QComboBox( tableWidget )
        tableWidget.setCellWidget( row, self.WELL_COLUMN, wellComboBox )

        # concentration
        concentrationDoubleSpinBox = Qt.QDoubleSpinBox( tableWidget )
        concentrationDoubleSpinBox.setSuffix( " mg/ml" )
        concentrationDoubleSpinBox.setDecimals( 2 )
        concentrationDoubleSpinBox.setRange( 0, 100 )
        tableWidget.setCellWidget( row, self.CONCENTRATION_COLUMN, concentrationDoubleSpinBox )

        # comments
        commentsLineEdit = Qt.QLineEdit( tableWidget )
        commentsLineEdit.setValidator( Qt.QRegExpValidator( Qt.QRegExp( "[a-zA-Z0-9\\%/()=+*^:.\-_ ]*" ), commentsLineEdit ) )
        tableWidget.setCellWidget( row, self.COMMENTS_COLUMN, commentsLineEdit )


        # macromolecule
        macromoleculeLineEdit = Qt.QLineEdit( tableWidget )
        macromoleculeLineEdit.setMaxLength( 30 )
        macromoleculeLineEdit.setValidator( Qt.QRegExpValidator( Qt.QRegExp( "^[a-zA-Z][a-zA-Z0-9_]*" ), macromoleculeLineEdit ) )
        tableWidget.setCellWidget( row, self.MACROMOLECULE_COLUMN, macromoleculeLineEdit )

        # code
        codeLineEdit = Qt.QLineEdit( tableWidget )
        codeLineEdit.setMaxLength( 30 )
        codeLineEdit.setValidator( Qt.QRegExpValidator( Qt.QRegExp( "^[a-zA-Z][a-zA-Z0-9_]*" ), codeLineEdit ) )
        tableWidget.setCellWidget( row, self.CODE_COLUMN, codeLineEdit )

        # viscosity
        viscosityComboBox = Qt.QComboBox( tableWidget )
        viscosityComboBox.addItems( ["Low", "Medium", "High"] )
        tableWidget.setCellWidget( row, self.VISCOSITY_COLUMN, viscosityComboBox )

        # buffername
        bufferComboBox = Qt.QComboBox( tableWidget )
        bufferComboBox.setEditable( True )
        tableWidget.setCellWidget( row, self.BUFFERNAME_COLUMN, bufferComboBox )

        bSignalMapper = Qt.QSignalMapper( self.brick_widget )
        bSignalMapper.setMapping( bufferComboBox, sampleID )
        bufferComboBox.editTextChanged.connect( bSignalMapper.map )
        bSignalMapper.mapped[int].connect( self.bufferComboBoxChanged )

        # transmission
        transmissionDoubleSpinBox = Qt.QDoubleSpinBox( tableWidget )
        transmissionDoubleSpinBox.setSuffix( " %" )
        transmissionDoubleSpinBox.setDecimals( 1 )
        transmissionDoubleSpinBox.setRange( 0, 100 )
        tableWidget.setCellWidget( row, self.TRANSMISSION_COLUMN, transmissionDoubleSpinBox )

        # volume
        volumeSpinBox = Qt.QSpinBox( tableWidget )
        volumeSpinBox.setSuffix( " u/l" )
        volumeSpinBox.setRange( 5, 150 )
        tableWidget.setCellWidget( row, self.VOLUME_COLUMN, volumeSpinBox )

        # temperature
        temperatureSEUDoubleSpinBox = Qt.QDoubleSpinBox( tableWidget )
        temperatureSEUDoubleSpinBox.setSuffix( " C" )
        temperatureSEUDoubleSpinBox.setDecimals( 2 )
        temperatureSEUDoubleSpinBox.setRange( 4, 60 )
        tableWidget.setCellWidget( row, self.TEMPERATURE_COLUMN, temperatureSEUDoubleSpinBox )

        # flow
        flowCheckBox = Qt.QCheckBox( tableWidget )
        tableWidget.setCellWidget( row, self.FLOW_COLUMN, flowCheckBox )
        recuperateCheckBox = Qt.QCheckBox( tableWidget )
        tableWidget.setCellWidget( row, self.RECUPERATE_COLUMN, recuperateCheckBox )

        # waittime
        waittimeSpinBox = Qt.QDoubleSpinBox( tableWidget )
        waittimeSpinBox.setSuffix( " s" )
        waittimeSpinBox.setDecimals( 0 )
        waittimeSpinBox.setRange( 0, 10000 )
        tableWidget.setCellWidget( row, self.WAITTIME_COLUMN, waittimeSpinBox )

        return sampleID
