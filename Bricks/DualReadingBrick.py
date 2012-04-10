"""
=============================================
  NAME       : Reading Brick (ReadingBrick.py)
  
  DESCRIPTION:
    
  VERSION    : 1

  REVISION   : 0

  RELEASE    : 2010/APR/10

  PLATFORM   : Bliss Framework 4

  EMAIL      : ricardo.fernandes@esrf.fr
  
  HISTORY    :
=============================================
"""



# =============================================
#  IMPORT MODULES
# =============================================
import os
from Framework4.GUI import Core
from Framework4.GUI.Core import Property, PropertyGroup, Connection, Signal, Slot       
from PyQt4 import QtCore, QtGui, Qt



# =============================================
#  BLISS FRAMEWORK CATEGORY
# =============================================
__category__ = "Synoptic"


# =============================================
#  CLASS DEFINITION
# =============================================
class ReadingBrick(Core.BaseBrick):
    

    __STATE = {"unknown": Qt.QColor(0x64, 0x64, 0x64),
               "ready": Qt.QColor(0x0, 0x0, 0xff),
               "error": Qt.QColor(0xff, 0x0, 0x0)}

    

    # =============================================
    #  PROPERTIES/CONNECTIONS DEFINITION
    # =============================================            
    properties = {"maskFormat": Property("string", "Mask format", "", "maskFormatChanged"),
                  "suffix": Property("string", "Suffix", "", "suffixChanged"),
                  "fontSize": Property("combo", "Font size", "", "fontSizeChanged", "9", ["6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "22", "24", "26", "28", "30"]),
                  "valueThreshold": Property("float", "Value threshold", "", "valueThresholdChanged", 1),
                  "toolTip": Property("string", "Tool tip", "", "toolTipChanged"),}
    
    connections = {"reading": Connection("Reading object",
                                        [Signal("readingChanged", "readingChanged")],
                                        [],
                                        "connectionStatusChanged")}
    
    

    # =============================================
    #  SIGNALS/SLOTS DEFINITION
    # =============================================      
    signals = []
    slots = []
    



    # =============================================
    #  CONSTRUCTOR
    # =============================================                    
    def __init__(self, *args, **kargs):
        Core.BaseBrick.__init__(self, *args, **kargs)

            
           
        
    # =============================================
    #  WIDGET DEFINITION
    # =============================================
    def init(self):
        self.__maskFormat = ""
        self.__suffix = ""
        self.__toolTip = ""
        self.__value = "???"
        self.__threshold = 0
        self.brick_widget.setLayout(Qt.QHBoxLayout())        
        self.readingLabel = Qt.QLabel()
        self.readingLabel.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.readingLabel.setAlignment(Qt.Qt.AlignCenter)        
        self.readingLabel.setAutoFillBackground(True)        
        self.brick_widget.layout().addWidget(self.readingLabel)

        


    # =============================================
    #  HANDLE PROPERTIES CHANGES
    # =============================================
    def maskFormatChanged(self, pValue):
        self.__maskFormat = pValue
        self.readingChanged(self.__value)        
                

    def suffixChanged(self, pValue):
        self.__suffix = pValue
        self.readingChanged(self.__value)
        

    def fontSizeChanged(self, pValue):
        font = self.readingLabel.font()
        font.setPointSize(int(pValue))
        self.readingLabel.setFont(font)
        self.readingLabel.update()        
        self.readingChanged(self.__value)
        

    def valueThresholdChanged(self, pValue):
        self.__threshold = pValue
        self.readingChanged(self.__value)


    def toolTipChanged(self, pValue):
        self.__toolTip = pValue
        self.readingLabel.setToolTip(self.__toolTip)



    # =============================================
    #  HANDLE SIGNALS
    # =============================================            
    def readingChanged(self, pValue):
        try:
            self.__value = str(float(pValue))
            if self.__maskFormat == "":
                self.readingLabel.setText(self.__value + self.__suffix)
            else:
                self.readingLabel.setText(self.__maskFormat % float(self.__value) + self.__suffix)
            if float(self.__value) < self.__threshold:
                palette = self.readingLabel.palette()
                palette.setColor(QtGui.QPalette.Window, self.__STATE["ready"])
                self.readingLabel.setPalette(palette)
            else:
                palette = self.readingLabel.palette()
                palette.setColor(QtGui.QPalette.Background, self.__STATE["error"])
                self.readingLabel.setPalette(palette)
        except:
            self.__value = "???"
            self.readingLabel.setText(self.__value + self.__suffix)
            palette = self.readingLabel.palette()
            palette.setColor(QtGui.QPalette.Background, self.__STATE["unknown"])
            self.readingLabel.setPalette(palette)



    def connectionStatusChanged(self, pPeer):        
        pass



