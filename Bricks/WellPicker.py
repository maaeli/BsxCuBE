import sys, os, time
import logging

from PyQt4 import QtCore, Qt, Qt

class WellPickerWidget( Qt.QWidget ):

    # geometry is a list of 3 lists (one per plate)
    # each sublist should contain the num. of rows, colums and deep well columns
    rowletters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

    def __init__( self, geometry, title, default_well = None, display_volume = False, display_cycles = False, parent = None ):

        Qt.QWidget.__init__( self, parent )
        self._geometry = geometry
        #TODO: DEBUG
        print "well picker geometry >>>>>>> %r" % self._geometry
        self._display_volume = display_volume
        self._display_cycles = display_cycles

        #Build the GUI according to geometry
        self.setLayout( Qt.QGridLayout( self ) )
        # add the 3 labels
        self.layout().addWidget( Qt.QLabel( '<b><u>' + title + '</u></b>', self ), 0, 0, 1, 2 )
        self.layout().addWidget( Qt.QLabel( 'Plate', self ), 1, 0 )
        self.layout().addWidget( Qt.QLabel( 'Row', self ), 2, 0 )
        self.layout().addWidget( Qt.QLabel( 'Column', self ), 3, 0 )

        # Add the 3 combo boxes
        self.plate_combo = Qt.QComboBox( self )
        self.row_combo = Qt.QComboBox( self )
        self.column_combo = Qt.QComboBox( self )

        self.layout().addWidget( self.plate_combo, 1, 1 )
        self.layout().addWidget( self.row_combo, 2, 1 )
        self.layout().addWidget( self.column_combo, 3, 1 )

        # the optional volume spinbox
        if self._display_volume:
            self.layout().addWidget( Qt.QLabel( 'Volume', self ), 4, 0 )

            self.volume_spinbox = Qt.QSpinBox( self )
            self.volume_spinbox.setSuffix( " u/l" )
            self.volume_spinbox.setRange( 5, 150 )
            self.volume_spinbox.setValue( 10 )
            self.layout().addWidget( self.volume_spinbox, 4, 1 )

        if self._display_cycles:
            self.layout().addWidget( Qt.QLabel( 'Cycles', self ), 5, 0 )

            self.cycles_spinbox = Qt.QSpinBox( self )
            self.cycles_spinbox.setSuffix( " " )
            self.cycles_spinbox.setRange( 1, 10 )
            self.cycles_spinbox.setValue( 1 )
            self.layout().addWidget( self.cycles_spinbox, 5, 1 )

        self.plate_combo.addItems( ['1', '2', '3'] )
        # other 2 combos filled  by callbacks

        QtCore.QObject.connect( self.plate_combo, QtCore.SIGNAL( "currentIndexChanged(const QString &)" ), self.plate_changed )

        if default_well != None:
            plate, row, column = default_well
            self.plate_changed( str( plate ) )
            self.setRow( row )
            self.setColumn( column )
        else:
            self.plate_changed( '1' )

    @QtCore.pyqtSlot( str )
    def plate_changed( self, selected_plate ):
        # fill the row and colum combos with acceptable values
        # select the first one by default

        selected_plate = int( selected_plate ) - 1

        self.plate_combo.setCurrentIndex( selected_plate )

        self.row_combo.clear()
        self.column_combo.clear()

        # in the geometry, most of the numerical stuff are floats
        #TODO: DEBUG
        print "before getting geometry >>>>>>> %r %r" % ( self._geometry, selected_plate )
        print type( self._geometry )
        print type( selected_plate )
        num_rows = int( self._geometry[selected_plate][0] )
        num_cols = int( self._geometry[selected_plate][1] )

        # rows are letters
        self.row_combo.addItems( self.rowletters[:num_rows] )

        self.column_combo.addItems( ['%d' % ( x + 1 ) for x in range( 0, num_cols )] )

    def setRow( self, row ):
        self.row_combo.setCurrentIndex( int( row ) - 1 )

    def setColumn( self, column ):
        self.column_combo.setCurrentIndex( int( column ) - 1 )


    def get_selected_well( self ):

        plate = self.plate_combo.currentText()
        row = self.row_combo.currentText()
        column = self.column_combo.currentText()

        row = self.rowletters.index( row ) + 1

        selected_well = [int( plate ), int( row ), int( column )]

        if self._display_volume:
            volume = self.volume_spinbox.value()
            selected_well.append( int( volume ) )

        if self._display_cycles:
            cycles = self.cycles_spinbox.value()
            selected_well.append( int( cycles ) )

        return selected_well

class WellPickerDialog( Qt.QDialog ):

    def __init__( self, geometry, title = 'Well Selection', default_well = None, display_volume = False, display_cycles = False, parent = None ):

        Qt.QDialog.__init__( self, parent )
        self.setLayout( Qt.QVBoxLayout() )
        self.setWindowTitle( title )
        self.well_picker = WellPickerWidget( geometry, title, default_well = default_well, display_volume = display_volume, display_cycles = display_cycles )

        self.button_layout = Qt.QHBoxLayout()

        self.ok_button = Qt.QPushButton( 'Ok' )
        self.cancel_button = Qt.QPushButton( 'Cancel' )

        self.ok_button.clicked.connect( self.ok_clicked )
        self.cancel_button.clicked.connect( self.cancel_clicked )

        self.button_layout.addWidget( self.ok_button )
        self.button_layout.addWidget( self.cancel_button )

        self.layout().addWidget( self.well_picker )
        self.layout().addLayout( self.button_layout )

    def ok_clicked( self ):
        self.accept()
    def cancel_clicked( self ):
        self.reject()

    def get_selected_well( self ):
        # proxy to get the value after ok has been clicked
        return self.well_picker.get_selected_well()


class Well2PickerDialog( Qt.QDialog ):
    def __init__( self, geometry, title1 = '', title2 = '', default_well = None, display_volume = False, display_cycles = False, parent = None ):

        Qt.QDialog.__init__( self, parent )
        self.setLayout( Qt.QVBoxLayout() )

        self.display_volume = display_volume

        self.setWindowTitle( "Two Well Selection" )

        self.well_layout = Qt.QHBoxLayout()
        self.well1_picker = WellPickerWidget( geometry, title1, default_well = default_well )
        self.well2_picker = WellPickerWidget( geometry, title2, default_well = default_well )

        if self.display_volume:
            self.volume_layout = Qt.QHBoxLayout()
            volume_label = Qt.QLabel( '<b><u>Volume:</u></b>' )
            volume_label.setAlignment( QtCore.Qt.AlignLeft )
            self.volume_layout.addWidget( volume_label )
            self.volume_spinbox = Qt.QSpinBox( self )
            self.volume_spinbox.setSuffix( " u/l" )
            self.volume_spinbox.setRange( 5, 150 )
            self.volume_spinbox.setValue( 10 )
            self.volume_layout.addWidget( self.volume_spinbox )

        self.button_layout = Qt.QHBoxLayout()

        self.ok_button = Qt.QPushButton( 'Ok' )
        self.cancel_button = Qt.QPushButton( 'Cancel' )

        self.ok_button.clicked.connect( self.ok_clicked )
        self.cancel_button.clicked.connect( self.cancel_clicked )

        self.button_layout.addWidget( self.ok_button )
        self.button_layout.addWidget( self.cancel_button )

        self.well_layout.setAlignment( QtCore.Qt.AlignTop )
        self.well_layout.addWidget( self.well1_picker )
        self.well_layout.addWidget( self.well2_picker )

        self.layout().addLayout( self.well_layout )
        if self.display_volume:
            self.layout().addLayout( self.volume_layout )
        self.layout().addLayout( self.button_layout )

    def ok_clicked( self ):
        self.accept()
    def cancel_clicked( self ):
        self.reject()

    def get_selected_well( self ):
        # proxy to get the value after ok has been clicked
        well1 = self.well1_picker.get_selected_well()
        well2 = self.well2_picker.get_selected_well()
        rwell = well1 + well2
        if self.display_volume:
           volume = self.volume_spinbox.value()
           rwell += [volume, ]
        return  rwell

def getWell( geometry, title, default_well = None ):
    dialog = WellPickerDialog( geometry, title , default_well = default_well )
    retvalue = dialog.exec_()
    if retvalue == Qt.QDialog.Accepted:
       return dialog.get_selected_well()
    else:
       return None

def getWellAndVolume( geometry, title, default_well = None ):
    dialog = WellPickerDialog( geometry, title = title, default_well = default_well, display_volume = True )
    retvalue = dialog.exec_()
    if retvalue == Qt.QDialog.Accepted:
       return dialog.get_selected_well()
    else:
       return None

def getWellVolumeAndCycles( geometry, title, default_well = None ):
    dialog = WellPickerDialog( geometry, title = title, default_well = default_well, display_volume = True, display_cycles = True )
    retvalue = dialog.exec_()
    if retvalue == Qt.QDialog.Accepted:
       return dialog.get_selected_well()
    else:
       return None

def getTwoWell( geometry, title1, title2, default_well = None ):
    dialog = Well2PickerDialog( geometry, title1, title2 , default_well = default_well )
    retvalue = dialog.exec_()
    if retvalue == Qt.QDialog.Accepted:
       return dialog.get_selected_well()
    else:
       return None

def getTwoWellsAndVolume( geometry, title1, title2, default_well = None ):
    dialog = Well2PickerDialog( geometry, title1, title2 , default_well = default_well, display_volume = True )
    retvalue = dialog.exec_()
    if retvalue == Qt.QDialog.Accepted:
       return dialog.get_selected_well()
    else:
       return None
