
import sys, os, time, logging
    
from Framework4.GUI      import Core
from Framework4.GUI.Core import Connection

from PyQt4 import Qt

from BsxVideoWidget import BsxVideoWidget

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
        self._sampleChanger  = None

        mainLayout       = Qt.QHBoxLayout(self.brick_widget)
        self.videoWidget = BsxVideoWidget( self.brick_widget )
        mainLayout.addWidget( self.videoWidget )
        self.brick_widget.setLayout( mainLayout )

    def sample_changer_connected(self, sc):        

        if sc is not None:
           logging.info("Sample changer VIDEO connected") 

           self._sampleChanger = sc
           self.videoWidget.setAutoRefreshRate(50)
           self.videoWidget.setAutoRefresh(True)

           self.videoWidget.getNewImage              = self._sampleChanger.getImageJPG
           self.videoWidget.getCurrentLiquidPosition = self._sampleChanger.getCurrentLiquidPosition
           self.videoWidget.getCurrentBeamLocation   = self._sampleChanger.getBeamLocation
           self.videoWidget.setBeamLocation          = self._sampleChanger.setBeamLocation
        else:
           logging.info("Sample changer VIDEO NOT connected") 
           self.videoWidget.setAutoRefresh(False)

