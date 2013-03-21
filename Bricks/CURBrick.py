import logging
from Framework4.GUI import Core
from Framework4.GUI.Core import Property, Connection, Signal, Slot
from PyQt4 import QtCore, QtGui, Qt
from Samples import Sample, CollectPars, SampleList
import cStringIO
import logging
import os.path, time
import pprint


__category__ = "BsxCuBE"


logger = logging.getLogger( "CURBrick" )
rowletters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
class CURBrick( Core.BaseBrick ):

#  ,
#                   "login": Connection( "Login object",
#                                        [Signal( "loggedIn", "loggedIn" )],
#                                        [],
#                                        "connectionToLogin" )
    connections = {"display": Connection( "Display object",
                                    [Signal( "displayResetChanged", "displayResetChanged" ),
                                    Signal( "displayItemChanged", "displayItemChanged" ),
                                    Signal( "transmissionChanged", "transmissionChanged" ),
                                    Signal( "grayOut", "grayOut" )],
                                    [] )

                   }

    signals = []
    slots = [Slot( "setParentObject" )]


    def __init__( self, *args, **kargs ):
        Core.BaseBrick.__init__( self, *args, **kargs )
        self.__parent = None

    def init( self ):
        # Setting configuration for columns in the samples table Widget
        self.column_headers = self.getColumns()
        self.PARAMLABEL_WIDTH = 130
        self.PARAMETERS_WIDTH = 220


        self.brick_widget.setLayout( Qt.QVBoxLayout() )
        mainLayout = self.brick_widget.layout()

        self.robotCheckBox = Qt.QCheckBox( "Collect using robot", self.brick_widget )
        Qt.QObject.connect( self.robotCheckBox, Qt.SIGNAL( "toggled(bool)" ), self.robotCheckBoxToggled )
        mainLayout.addWidget( self.robotCheckBox )

        self.groupBox = Qt.QGroupBox( "Parameters", self.brick_widget )
        self.groupBox.setSizePolicy( Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding )
        # All parameters are grayed out until collect using robot (AKA CUR) checkbox is selected
        self.groupBox.setDisabled( True )
        self.VerticalParametersLayout = Qt.QVBoxLayout( self.groupBox )
        mainLayout.addWidget( self.groupBox )


        self.hBoxLayout0 = self.getFirstButtonsRowLayout()
        self.VerticalParametersLayout.addLayout( self.hBoxLayout0 )

        # Calibration Type or User defined
        self.optimizationLabel = Qt.QLabel( "Type", self.brick_widget )
        self.optimizationComboBox = Qt.QComboBox( self.brick_widget )
        self.optimizationComboBox.addItems( ["User defined", "BSA Calibration", "Water Calibration" ] )
        Qt.QObject.connect( self.optimizationComboBox, Qt.SIGNAL( "currentIndexChanged(QString)" ), self.loadCalibrationTemplate )
        self.VerticalParametersLayout.addLayout( self.getHorizontalLabelValueLayoutFactory( [self.optimizationLabel, self.optimizationComboBox] ) )


        # Sample Type
        self.sampleTypeLabel = Qt.QLabel( "Sample type", self.brick_widget )
        self.sampleTypeComboBox = Qt.QComboBox( self.brick_widget )
        self.sampleTypeComboBox.addItems( ["Green", "Yellow", "Red"] )
        self.VerticalParametersLayout.addLayout( self.getHorizontalLabelValueLayoutFactory( [self.sampleTypeLabel, self.sampleTypeComboBox] ) )


        # Storage Temperature
        self.storageTemperatureLabel = Qt.QLabel( "Storage temperature", self.brick_widget )
        self.storageTemperatureDoubleSpinBox = Qt.QDoubleSpinBox( self.brick_widget )
        self.storageTemperatureDoubleSpinBox.setSuffix( " C" )
        self.storageTemperatureDoubleSpinBox.setDecimals( 2 )
        self.storageTemperatureDoubleSpinBox.setRange( 4, 40 )
        self.storageTemperatureDoubleSpinBox.setValue( 4 )
        self.VerticalParametersLayout.addLayout( self.getHorizontalLabelValueLayoutFactory( [self.storageTemperatureLabel, self.storageTemperatureDoubleSpinBox] ) )

        # Ex. Flow Time
        self.extraFlowTimeLabel = Qt.QLabel( "Extra flow time", self.brick_widget )
        self.extraFlowTimeSpinBox = Qt.QSpinBox( self.brick_widget )
        self.extraFlowTimeSpinBox.setSuffix( " s" )
        self.extraFlowTimeSpinBox.setRange( 0, 900 )
        self.VerticalParametersLayout.addLayout( self.getHorizontalLabelValueLayoutFactory( [self.extraFlowTimeLabel, self.extraFlowTimeSpinBox] ) )

        # Optimization
        self.optimizationLabel = Qt.QLabel( "Optimization", self.brick_widget )
        self.optimizationComboBox = Qt.QComboBox( self.brick_widget )
        self.optimizationComboBox.addItems( ["None", "Sample SEU temperature", "Sample code and SEU temperature"] )
        self.VerticalParametersLayout.addLayout( self.getHorizontalLabelValueLayoutFactory( [self.optimizationLabel, self.optimizationComboBox] ) )

        # Initial cleaning
        self.initialCleaningLabel = Qt.QLabel( "Initial Cleaning", self.brick_widget )
        self.initialCleaningCheckBox = Qt.QCheckBox( self.brick_widget )
        self.initialCleaningCheckBox.setChecked( 1 )
        self.VerticalParametersLayout.addLayout( self.getHorizontalLabelValueLayoutFactory( [self.initialCleaningLabel, self.initialCleaningCheckBox] ) )

        # Buffer mode
        self.bufferModeLabel = Qt.QLabel( "Buffer mode", self.brick_widget )
        self.bufferModeComboBox = Qt.QComboBox( self.brick_widget )
        self.bufferModeComboBox.addItems( ["First and After", "Before", "After", "None"] )
        self.VerticalParametersLayout.addLayout( self.getHorizontalLabelValueLayoutFactory( [self.bufferModeLabel, self.bufferModeComboBox] ) )

        # History
        self.historyLabel = Qt.QLabel( "History", self.brick_widget )
        self.historyLabel.setFixedWidth( self.PARAMLABEL_WIDTH )
        self.historyText = Qt.QTextEdit( self.brick_widget )
        self.historyText.setReadOnly( True )
        self.historyText.setFixedWidth( 600 )
        self.historyText.setFixedHeight( 80 )
        self.clearHistoryPushButton = Qt.QPushButton( "Clear", self.brick_widget )
        self.clearHistoryPushButton.setFixedWidth( 50 )
        Qt.QObject.connect( self.clearHistoryPushButton, Qt.SIGNAL( "clicked()" ), self.clearHistoryPushButtonClicked )
        self.historyLabel.setAlignment( QtCore.Qt.AlignTop )
        self.VerticalParametersLayout.addLayout( self.getHorizontalLayoutFactory( [self.historyLabel, self.historyText, self.clearHistoryPushButton] ) )

        # Sample Table
        self.tableWidget = Qt.QTableWidget( 0, len( self.column_headers ), self.brick_widget )
        self.tableWidget.setHorizontalHeaderLabels( self.column_headers )
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

        self.VerticalParametersLayout.addLayout( self.getHorizontalLayoutFactory( [self.addPushButton, self.copyPushButton, self.pastePushButton, self.clearPushButton ] ) )


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


    def getHorizontalLabelValueLayoutFactory ( self, widgets ):
        widgets[0].setFixedWidth( self.PARAMLABEL_WIDTH )
        widgets[1].setFixedWidth( self.PARAMETERS_WIDTH )
        return self.getHorizontalLayoutFactory( [widgets[0], widgets[1]] )

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
                                "Concentration", "Comments", "Macromolecule", "Code", "Viscosity", "Buffername", \
                                "Transmission", "Volume", "SEU Temp", "Flow", "Recup.", \
                                "Wait Time", "Del"]

    # getting a handle to the parent = CollectBrick
    def setParentObject( self, pParent ):
        #TODO: DEBUG
        print "Got parent handle in CURBrick"
        if pParent is not None:
            self.__parent = pParent

   # When connected to Login, then block the brick
    def connectionToLogin( self, pPeer ):
        if pPeer is not None:
            self.brick_widget.setEnabled( False )

    # Logged In : True or False 
    def loggedIn( self, pValue ):
        self.brick_widget.setEnabled( pValue )


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

#---------------#
# CALLBACKS     #
#---------------#

    #------------------------------------------------------------------------
    #  loadPushButton -  Load file with collection parameters and history
    #------------------------------------------------------------------------
    def loadPushButtonClicked( self ):
        dirname = ""
        self.filename = str( self.fileLineEdit.text() )
        if self.filename != "":
            dirname = os.path.split( self.filename )[0]
        else:
            try:
                dirname = os.path.split( self.__parent.collectpars.directory )
            except Exception, e:
                print "Ignored Exception 5: " + str( e )

        filename = Qt.QFileDialog.getOpenFileName( self, "Choose a new file to load", dirname, "XML File (*.xml)" )

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

            self.historyText.clear()
            self.historyText.setText( myPars.history.strip() )

            for myBuffer in  myPars.bufferList:
                self.addSampleRow( myBuffer )
            for sample in  myPars.sampleList:
                self.addSampleRow( sample )

            self.CBblock = 0
            self.filename = filename
            self.__parent.setRobotFileName( filename )

        except Exception, e:
            logger.exception( 'Cannot load collection parameters file. \n' )
            Qt.QMessageBox.critical( self, "Error", "Error when trying to read file '%s'!" % filename )

    def saveAsPushButtonClicked( self ):
        self.filename = str( self.fileLineEdit.text() )
        filename = Qt.QFileDialog.getSaveFileName( self, "Choose a file to save", self.filename, "XML File (*.xml)" )
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
        self.__parent.setRobotFileName( filename )




    def savePushButtonClicked( self ):
        if self.filename == "" or not os.path.isfile( self.filename ):
            self.saveAsPushButtonClicked()
        else:
            self.saveFile( self.filename , askrewrite = False )

    def saveFile( self, filename, askrewrite = True ):

        if os.path.exists( filename ):
            quitsave = Qt.QMessageBox.question( self, "Warning", "The file '%s' already exists. Overwrite it?" % filename, Qt.QMessageBox.Yes, Qt.QMessageBox.No, Qt.QMessageBox.NoButton ) != Qt.QMessageBox.Yes
            if quitsave:
                return

        myPars = self.getCollectRobotPars( isAll = 1 )
        history = self.historyText.toPlainText()

        try:
            if os.path.exists( filename ):
                myPars.save( filename , history )
                Qt.QMessageBox.information( self, "Info", "The new version of the file '%s' was successfully saved!" % filename )
            else:
                myPars.save( filename , history )
                Qt.QMessageBox.information( self, "Info", "A new version of the file '%s' was successfully saved!" % filename )
        except Exception, e:
            import traceback
            traceback.print_exc()
            logger.exception( 'Cannot save collection parameters file.\n' )
            logger.error( "Full Exception: " + str( e ) )
            Qt.QMessageBox.critical( self, "Error", "Error when trying to save file '%s'!" % filename )


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

        plateInfos = self.__parent.plateInfos

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

#-------------------------------------------
#  Internal functions
#-------------------------------------------


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

        plateInfos = self.__parent.plateInfos

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
            waittimeSpinBox.setSuffix( " sec" )
            waittimeSpinBox.setDecimals( 0 )
            waittimeSpinBox.setRange( 0, 10000 )
            self.tableWidget.setCellWidget( index, self.WAITTIME_COLUMN, waittimeSpinBox )

            bufcombo.setEditable( False )

            if sample:
                temperatureSEUDoubleSpinBox.setValue( sample.SEUtemperature )
                waittimeSpinBox.setValue( sample.waittime )

        for i in range( len( self.column_headers ) ):
            self.tableWidget.cellWidget( index, i ).setProperty( "sampletype", well_type )

        self.setStyleSheet( self.styleSheet() )

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
        if Qt.QMessageBox.question( self, "Warning", "Do you really want to clear the current configuration?", Qt.QMessageBox.Yes, Qt.QMessageBox.No, Qt.QMessageBox.NoButton ) == Qt.QMessageBox.Yes:
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

        self.historyText.clear()

        while self.tableWidget.rowCount() > 0:
            self.tableWidget.removeRow( 0 )


    def clearHistoryPushButtonClicked( self ):
        if Qt.QMessageBox.question( self, "Warning", "Do you really want to clear the current history?", Qt.QMessageBox.Yes, Qt.QMessageBox.No, Qt.QMessageBox.NoButton ) == Qt.QMessageBox.Yes:
            self.historyText.clear()

    def closePushButtonClicked( self ):
        self.accept()

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
            templateDirectory = self.__parent.getTemplateDirectory()
            filename = str( templateDirectory + "/" + str( pValue ).split( " " )[0] + ".xml" )
            self.loadFile( filename )

    def robotCheckBoxToggled( self, pValue, fromBrick = False ):
      self.__parent.robotCheckBoxToggled( pValue, fromCUR = True )
      if fromBrick:
          self.robotCheckBox.setChecked( pValue )

