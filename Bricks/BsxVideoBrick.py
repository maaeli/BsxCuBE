import sys, os, time, logging

from Framework4.GUI      import Core
from Framework4.GUI.Core import Connection

from PyQt4 import Qt

from BsxVideoWidget import BsxVideoWidget

logger = logging.getLogger("BsxVideoBrick")

__category__ = "BsxCuBE"

class BsxVideoBrick(Core.BaseBrick):

    properties = {}
    connections = {"samplechanger": Connection("Sample Changer object",
                    [],
                    [],
                    "sample_changer_connected")}

    def __init__(self, *args, **kargs):
        Core.BaseBrick.__init__(self, *args, **kargs)

    def init(self):
        self._sampleChanger = None

        mainLayout = Qt.QHBoxLayout(self.brick_widget)
        self.videoWidget = BsxVideoWidget(self.brick_widget)
        mainLayout.addWidget(self.videoWidget)
        self.brick_widget.setLayout(mainLayout)

    def exceptionCallback(self, exception):
        pass #logger.info("EXCEPTION:%r", exception)

    def sample_changer_connected(self, sc):
        if sc is not None:
            logger.info("Sample changer VIDEO connected")

            self._sampleChanger = sc
            self.videoWidget.setAutoRefreshRate(50)
            #TODO: Make a callback setting 
            #self.videoWidget.setCallbacks(new_image=self._sampleChanger.getImageJPG,
            #                              get_liquid_pos=)
            # override videoWidget calls
            self.videoWidget.getNewImage = self._sampleChanger.getImageJPG
            self.videoWidget.getCurrentLiquidPosition = self._sampleChanger.getCurrentLiquidPosition
            self.videoWidget.getCurrentBeamLocation = self._sampleChanger.getBeamLocation
            self.videoWidget.setBeamLocation = self._sampleChanger.setBeamLocation
            self.videoWidget.exceptionCallback = self.exceptionCallback

            #TODO: DEBUG Can not take video signal at the same time as doing something else
            self.videoWidget.setAutoRefresh(True)
            #self.videoWidget.setAutoRefresh(False)
        else:
            logger.info("Sample changer VIDEO NOT connected")
            self.videoWidget.setAutoRefresh(False)


