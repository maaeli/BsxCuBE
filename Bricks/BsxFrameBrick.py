from Framework4.GUI import Core
from Framework4.GUI.Core import Connection, Signal
from Qub.qt4.Widget.DataDisplay import QubDataImageDisplay
from Qub.qt4.Widget.QubDialog import QubMaskToolsDialog
from Qub.qt4.Widget.QubActionSet import QubOpenDialogAction
from Qub.qt4.Widget.DataDisplay.QubDataImageDisplay import QubDataImageDisplay
from PyQt4 import QtCore, QtGui, Qt

__category__ = "BsxCuBE"

class BsxFrameBrick(Core.BaseBrick):
    properties = {}
    connections = {"display": Connection("Display object",
                                    [Signal("displayResetChanged", "displayResetChanged"),
                                    Signal("displayItemChanged", "displayItemChanged"),
                                    Signal("transmissionChanged", "transmissionChanged"),
                                    Signal("grayOut", "grayOut")],
                                    []),
                    "login": Connection("Login object",
                                    [Signal("loggedIn", "loggedIn")],
                                    [],
                                    "connectionToLogin")}
    signals = []
    slots = []

    def __init__(self, *args, **kargs):
        Core.BaseBrick.__init__(self, *args, **kargs)

    def init(self):
        Qt.QVBoxLayout(self.brick_widget)
        self.frameDisplay = QubDataImageDisplay(self.brick_widget, noAction = True, forcePopupSubWindow = True)
        # layout
        #TODO:  Next line will always have an error in Eclipse, even if it is correct.
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

    # When connected to Login, then block the brick
    def connectionToLogin(self, pPeer):
        if pPeer is not None:
            self.brick_widget.setEnabled(False)


    # Logged In : True or False 
    def loggedIn(self, pValue):
        self.brick_widget.setEnabled(pValue)

    def displayItemChanged(self, files_string):
        #TODO: DEBUG 
        print ">> file_string %r " % files_string
        filesList = files_string.split(",")
        for f in filesList:
            if f.endswith('.edf'):
                self.frameDisplay.setDataSource(f)

    def displayResetChanged(self):
        pass

    def transmissionChanged(self, _):
        pass

    def grayOut(self, _):
        pass
