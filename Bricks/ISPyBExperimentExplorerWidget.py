#Temporal Widget for testing ISPyB

import sys
from PyQt4 import Qt, QtCore, QtGui
import os, sys
from suds.client import Client
from suds.transport.http import HttpAuthenticated
import json
import time

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class ISPyBExperimentExplorerWidget( Qt.QDialog ):

    def __init__( self, title = "Time" ):

        Qt.QDialog.__init__( self )

        self.resize( 800, 600 )
        self.setWindowTitle( title )
        self.setModal( True )

        Widget = self
        self.label = QtGui.QLabel( Widget )
        self.label.setGeometry( QtCore.QRect( 10, 60, 81, 16 ) )
        self.label.setObjectName( _fromUtf8( "label" ) )
        self.tableWidget = QtGui.QTableWidget( Widget )
        self.tableWidget.setEnabled( True )
        self.tableWidget.setGeometry( QtCore.QRect( 10, 20, 750, 500 ) )
        self.tableWidget.setEditTriggers( QtGui.QAbstractItemView.NoEditTriggers )
        self.tableWidget.setSelectionMode( QtGui.QAbstractItemView.SingleSelection )
        self.tableWidget.setSelectionBehavior( QtGui.QAbstractItemView.SelectRows )
        self.tableWidget.setRowCount( 0 )
        self.tableWidget.setColumnCount( 3 )
        self.tableWidget.setObjectName( _fromUtf8( "tableWidget" ) )

        header = self.tableWidget.horizontalHeader()
        header.setStretchLastSection( True )

        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem( 0, item )
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem( 1, item )
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem( 2, item )
        self.close_button = QtGui.QPushButton( Widget )
        self.close_button.setGeometry( QtCore.QRect( 400, 550, 141, 23 ) )
        self.close_button.setObjectName( _fromUtf8( "close_button" ) )
        self.close_button.clicked.connect( self.onCancel )
        self.Load_plates_button = QtGui.QPushButton( Widget )
        self.Load_plates_button.setGeometry( QtCore.QRect( 240, 550, 141, 23 ) )
        self.Load_plates_button.setObjectName( _fromUtf8( "Accept" ) )
        self.Load_plates_button.clicked.connect( self.onAccept )
        self.retranslateUi( Widget )
        QtCore.QMetaObject.connectSlotsByName( Widget )

    def retranslateUi( self, Widget ):
        Widget.setWindowTitle( QtGui.QApplication.translate( "Widget", "Widget", None, QtGui.QApplication.UnicodeUTF8 ) )
        self.label.setText( QtGui.QApplication.translate( "Widget", "Select Experiment:", None, QtGui.QApplication.UnicodeUTF8 ) )
        item = self.tableWidget.horizontalHeaderItem( 0 )
        item.setText( QtGui.QApplication.translate( "Widget", "Name", None, QtGui.QApplication.UnicodeUTF8 ) )
        item = self.tableWidget.horizontalHeaderItem( 1 )
        item.setText( QtGui.QApplication.translate( "Widget", "Type", None, QtGui.QApplication.UnicodeUTF8 ) )
        item = self.tableWidget.horizontalHeaderItem( 2 )
        item.setText( QtGui.QApplication.translate( "Widget", "Time", None, QtGui.QApplication.UnicodeUTF8 ) )

        self.close_button.setText( QtGui.QApplication.translate( "Widget", "Cancel", None, QtGui.QApplication.UnicodeUTF8 ) )
        self.Load_plates_button.setText( QtGui.QApplication.translate( "Widget", "Accept", None, QtGui.QApplication.UnicodeUTF8 ) )

    def loadExperiments( self, response ):
        self.experiments = json.loads( response )
        i = 0

        self.tableWidget.setRowCount( len( self.experiments ) )
        for experiment in self.experiments:
            print "DEBUG - experiment next line" 
            print experiment
            if experiment["experimentType"] == "HPLC":
                experimentName = 'HPLC'
            else:
                experimentName = experiment["name"]
            name = QtGui.QTableWidgetItem( experimentName )
            type = QtGui.QTableWidgetItem( experiment["experimentType"] )
            self.tableWidget.setItem( i, 0, name )
            self.tableWidget.setItem( i, 1, type )
            self.tableWidget.setItem( i, 2, QtGui.QTableWidgetItem( experiment["creationDate"] ) )
            i = i + 1
        self.tableWidget.resizeColumnsToContents()

    def getSelectedExperimentId( self ):
        return self.experimentId

    def onAccept( self ):
        for idx in self.tableWidget.selectedIndexes():
            experimentId = self.experiments[idx.row()]["experimentId"]
            #print str( self.getWSClient().service.getRobotByExperimentId( experimentId ) )
            self.experimentId = experimentId
            self.accept()

    def onCancel( self ):
        self.close()

