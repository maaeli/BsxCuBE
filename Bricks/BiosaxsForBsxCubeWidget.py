# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'widget2.ui'
#
# Created: Thu Jul 26 10:42:50 2012
#      by: PyQt4 UI code generator 4.9.4
#
# WARNING! All changes made in this file will be lost!

from BiosaxsClient import BiosaxsClient
from PyQt4 import QtCore, QtGui
import os, sys


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Widget(object):
    def setupUi(self, Widget):
        Widget.setObjectName(_fromUtf8("Widget"))
        Widget.resize(596, 362)

        self.response = None

        self.label = QtGui.QLabel(Widget)
        self.label.setGeometry(QtCore.QRect(10, 60, 81, 16))
        self.label.setObjectName(_fromUtf8("label"))

        self.open_ISPYB_WUI_Button = QtGui.QPushButton(Widget)
        self.open_ISPYB_WUI_Button.setGeometry(QtCore.QRect(430, 80, 151, 23))
        self.open_ISPYB_WUI_Button.setObjectName(_fromUtf8("open_ISPYB_WUI_Button"))
        #self.open_ISPYB_WUI_Button.clicked.connect(self.open_ISPyB_WebWidget)

        self.tableWidget = QtGui.QTableWidget(Widget)
        self.tableWidget.setEnabled(True)
        self.tableWidget.setGeometry(QtCore.QRect(10, 80, 411, 241))
        self.tableWidget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.tableWidget.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.tableWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setObjectName(_fromUtf8("tableWidget"))
        QtCore.QObject.connect(self.tableWidget, QtCore.SIGNAL("selectionChanged()"), self.getSelection)
        QtCore.QObject.connect(self.tableWidget, QtCore.SIGNAL(_fromUtf8("itemSelectionChanged()")), self.getSelection)

        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        self.label_2 = QtGui.QLabel(Widget)
        self.label_2.setGeometry(QtCore.QRect(10, 10, 181, 16))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.close_button = QtGui.QPushButton(Widget)
        self.close_button.setGeometry(QtCore.QRect(430, 330, 141, 23))
        self.close_button.setObjectName(_fromUtf8("close_button"))
        self.Load_plates_button = QtGui.QPushButton(Widget)
        self.Load_plates_button.setGeometry(QtCore.QRect(140, 330, 141, 23))
        self.Load_plates_button.setObjectName(_fromUtf8("Load_plates_button"))
        self.Load_plates_button.clicked.connect(self.onLoadPlatesButtonClicked)

        self.comboBox = QtGui.QComboBox(Widget)
        self.comboBox.setGeometry(QtCore.QRect(10, 30, 411, 22))
        self.comboBox.setObjectName(_fromUtf8("comboBox"))
        QtCore.QObject.connect(self.comboBox, QtCore.SIGNAL("currentIndexChanged(QString)"), self.onExperimentChosen)

        self.refresh_data_button = QtGui.QPushButton(Widget)
        self.refresh_data_button.setGeometry(QtCore.QRect(430, 30, 151, 23))
        self.refresh_data_button.setObjectName(_fromUtf8("refresh_data_button"))
        self.refresh_data_button.clicked.connect(self.onRefreshDataButtonClicked)

        self.close_button.clicked.connect(self.onCloseButtonClicked)

        self.retranslateUi(Widget)
        QtCore.QMetaObject.connectSlotsByName(Widget)


    def onLoadPlatesButtonClicked(self):
        plateIds = self.getSelection()
        self.response = self.client.getRobotXMLByPlateIds(self.experiment.experiment.experimentId, plateIds)
        self.tableWidget.parentWidget().accept()


    def loadSamplePlateData(self, data):
        self.tableWidget.setRowCount(len(data))
        #for row in data

    def getSelection(self):
        print "getSelection() ..."

        plateIds = set()
        for item in self.tableWidget.selectedIndexes():
            #plateIds.add(item.row())
            plateIds.add(self.experiment.getPlates()[item.row()].samplePlateId)
        #print item.row()
        for id in plateIds:
            print id
        return plateIds


    def onRefreshDataButtonClicked(self):
        #Clean comboBox
        while (self.comboBox.count() <> 0):
            self.comboBox.removeItem(0)

        self.client = BiosaxsClient('mx1438', 'Rfo4-73')
        self.experiments = self.client.getExperimentsByProposalId(3124)
        for experiment in self.experiments:
            self.comboBox.addItem(experiment.experiment.name, experiment.experiment.experimentId)


    def onCloseButtonClicked(self):
        self.tableWidget.parentWidget().reject()

    def onExperimentChosen(self):
        print self.comboBox.currentIndex()
        print self.experiments[self.comboBox.currentIndex()].experiment.name
        self.experiment = self.experiments[self.comboBox.currentIndex()]
        self.tableWidget.setRowCount(len(self.experiments[self.comboBox.currentIndex()].getPlates()))
        i = 0
        for  plate in self.experiments[self.comboBox.currentIndex()].getPlates():
            print plate.name + "  " + plate.platetype3VO.name
            name = QtGui.QTableWidgetItem(plate.name)
            sampletype = QtGui.QTableWidgetItem(plate.platetype3VO.name)
            storageTemperature = QtGui.QTableWidgetItem(plate.storageTemperature)
            self.tableWidget.setItem(i, 0, name)
            self.tableWidget.setItem(i, 1, sampletype)
            self.tableWidget.setItem(i, 2, storageTemperature)
            i = i + 1


    def retranslateUi(self, Widget):
        Widget.setWindowTitle(QtGui.QApplication.translate("Widget", "Widget", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Widget", "Select plates:", None, QtGui.QApplication.UnicodeUTF8))
        self.open_ISPYB_WUI_Button.setText(QtGui.QApplication.translate("Widget", "Open ISPyB Web Interface", None, QtGui.QApplication.UnicodeUTF8))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(QtGui.QApplication.translate("Widget", "Name", None, QtGui.QApplication.UnicodeUTF8))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(QtGui.QApplication.translate("Widget", "Type", None, QtGui.QApplication.UnicodeUTF8))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(QtGui.QApplication.translate("Widget", "Storage Temp.", None, QtGui.QApplication.UnicodeUTF8))

        self.label_2.setText(QtGui.QApplication.translate("Widget", "Select experiment:", None, QtGui.QApplication.UnicodeUTF8))
        self.close_button.setText(QtGui.QApplication.translate("Widget", "Cancel", None, QtGui.QApplication.UnicodeUTF8))
        self.Load_plates_button.setText(QtGui.QApplication.translate("Widget", "Load Plates to Robot", None, QtGui.QApplication.UnicodeUTF8))
        self.refresh_data_button.setText(QtGui.QApplication.translate("Widget", "Refresh from ISPyB", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Widget = QtGui.QWidget()
    ui = Ui_Widget()
    ui.setupUi(Widget)
    Widget.show()


    sys.exit(app.exec_())

