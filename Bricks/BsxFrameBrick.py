import logging
from Framework4.GUI import Core
from Framework4.GUI.Core import Property, PropertyGroup, Connection, Signal, Slot
from PyQt4 import QtCore, QtGui, Qt
from Qub.qt4.Widget.DataDisplay import QubDataImageDisplay
from Qub.qt4.Widget.QubDialog import QubMaskToolsDialog
from Qub.qt4.Widget.QubActionSet import QubOpenDialogAction
from Qub.qt4.Data.Class.QubDataClass import QubDataSourcePlug
from Qub.qt4.Data.DisplayManager.QubDisplayManager import QubDisplayManager, QubDisplayManagerCreator
from Qub.qt4.Widget.QubActionSet import QubSliderNSpinAction
from Qub.qt4.Widget.DataDisplay.QubDataImageDisplay import QubDataImageDisplay


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
        self.frameDisplay = QubDataImageDisplay(self.brick_widget, noAction = True, forcePopupSubWindow = True)
        # layout
        # Next line will always have an error in Eclipse, even if it is correct.
        self.frameDisplay.setSizePolicy(Qt.QSizePolicy.MinimumExpanding, Qt.QSizePolicy.MinimumExpanding)
        self.brick_widget.layout().addWidget(self.frameDisplay)
        # No foreground color change - all other left in
        action_enum = [QubDataImageDisplay.QUICK_SCROLL,
                      QubDataImageDisplay.SUB_DATA_VIEW,
                      QubDataImageDisplay.PRINT_PREVIEW,
                      QubDataImageDisplay.SAVE_IMAGE,
                      QubDataImageDisplay.STAT_ACTION,
                      QubDataImageDisplay.HEADER_INFO,
                      QubDataImageDisplay.ZOOM,
                      QubDataImageDisplay.COLORMAP,
                      QubDataImageDisplay.HORIZONTAL_SELECTION,
                      QubDataImageDisplay.VERTICAL_SELECTION,
                      QubDataImageDisplay.LINE_SELECTION,
                      QubDataImageDisplay.POSITION_AND_VALUE]
        self.frameDisplay.addStdAction(action_enum, zoomValList = None)
        # Add the monkey dialog box for masks
        openDialog = QubOpenDialogAction(parent = self.frameDisplay,
                                         name = 'mask', iconName = 'mask',
                                         group = 'Mask')
        dialog = QubMaskToolsDialog(None)
        dialog.setGraphicsView(self.frameDisplay.getDrawingView())
        openDialog.setDialog(dialog)
        openDialog._dialog = dialog
        self.frameDisplay.addDataAction(openDialog, dialog)
        # Reference the openDialog to make sure the Garbage Collector does not remove it (_openD could be _dummy)
        self.frameDisplay._openD = openDialog

    def displayItemChanged(self, files_string):
        filesList = files_string.split(",")
        for f in filesList:
            if f.endswith('.edf'):
                self.frameDisplay.setDataSource(f)

    def displayResetChanged(self, *args):
        return
