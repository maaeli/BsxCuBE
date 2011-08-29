import logging
from Framework4.GUI import Core
from Framework4.GUI.Core import Property, PropertyGroup, Connection, Signal, Slot                   
from PyQt4 import QtCore, QtGui, Qt
from Qub.Widget.DataDisplay import QubDataImageDisplay    

__category__ = "BsxCuBE"

class BsxFrameBrick(Core.BaseBrick):
    properties = {}       
    connections = {"display": Connection("Display object",
                                      [Signal("displayResetChanged", "displayResetChanged"),
                                       Signal("displayItemChanged", "displayItemChanged")],
                                       [])}
    signals = []
    slots = []

    def __init__(self, *args, **kargs):
        Core.BaseBrick.__init__(self, *args, **kargs)
        
    def init(self):
        Qt.QVBoxLayout(self.brick_widget)
        self.frameDisplay = QubDataImageDisplay.QubDataImageDisplay(self.brick_widget, noAction = False, noToolbarAction = False, forcePopupSubWindow = True)
        self.frameDisplay.setSizePolicy(Qt.QSizePolicy.MinimumExpanding, Qt.QSizePolicy.MinimumExpanding)
        self.brick_widget.layout().addWidget(self.frameDisplay)
        #self.frameDisplay.setFit2Screen(True)

    def displayItemChanged(self, files_string):
        filesList = files_string.split(",")
        for f in filesList:
            if f.endswith('.edf'):
                #logging.debug('BsxFrame loading %s', f)
                self.frameDisplay.setDataSource(f)

    def displayResetChanged(self, *args):
        return
