"""
=============================================
  NAME       : Calibration Diamond Brick (CalibrationDiamondBrick.py)
  
  DESCRIPTION:
    
  VERSION    : 1

  REVISION   : 0

  RELEASE    : 2010/ABR/14

  PLATFORM   : Bliss Framework 4

  EMAIL      : ricardo.fernandes@esrf.fr
  
  HISTORY    :
=============================================
"""



# =============================================
#  IMPORT MODULES
# =============================================
try:
    import logging
    from Framework4.GUI import Core
    from Framework4.GUI.Core import Property, PropertyGroup, Connection, Signal, Slot       
    from PyQt4 import QtCore, QtGui, Qt, Qwt5 as qwt
except ImportError:
    print "%s.py: error when importing module!" % __name__



# =============================================
#  BLISS FRAMEWORK CATEGORY
# =============================================
__category__ = "General"



# =============================================
#  CLASS DEFINITION
# =============================================
class CalibrationDiamondBrick(Core.BaseBrick):
    
    

    # =============================================
    #  PROPERTIES/CONNECTIONS DEFINITION
    # =============================================            
    properties = {"caption": Property("string", "Caption", "", "captionChanged"),
                  "parameter": Property("string", "Parameter", "", "parameterChanged"),                  
                  "toolTip": Property("string", "Tool tip", "", "toolTipChanged"),
                  "expertModeOnly": Property("boolean", "Expert mode only", "", "expertModeOnlyChanged", False)}
    
        
    connections = {"calibration": Connection("Calibration object",
                                            [Signal("calibrationStatusChanged", "calibrationStatusChanged"),
                                             Signal("newPositionChanged", "newPositionChanged")],
                                            [Slot("executeCalibration")],
                                            "connectionStatusChanged"),
                    "login": Connection("Login object",
                                            [Signal("expertModeChanged", "expertModeChanged")],
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
        self.__parameter = ""
        self.__toolTip = ""
        self.__expertModeOnly = False
        self.__expertMode = False
        self.__setPosition = False
        self.__newPosition = 0
        
        self.brick_widget.setLayout(Qt.QVBoxLayout())
        self.commandPushButton = Qt.QPushButton(self.brick_widget)
        Qt.QObject.connect(self.commandPushButton, Qt.SIGNAL("clicked()"), self.commandPushButtonClicked)
        self.brick_widget.layout().addWidget(self.commandPushButton)
        



    # =============================================
    #  HANDLE PROPERTIES CHANGES
    # =============================================
    def captionChanged(self, pValue):
        self.commandPushButton.setText(pValue)


    def parameterChanged(self, pValue):
        self.__parameter = pValue


    def toolTipChanged(self, pValue):
        self.__toolTip = pValue
        self.commandPushButton.setToolTip(self.__toolTip)


    def expertModeOnlyChanged(self, pValue):
        self.__expertModeOnly = pValue
        self.expertModeChanged(self.__expertMode)



    # =============================================
    #  HANDLE SIGNALS
    # =============================================
    def commandPushButtonClicked(self):
        self.__setPosition = True
        self.getObject("calibration").executeCalibration(self.__parameter)



    def calibrationStatusChanged(self, pValue): 
        messageList = pValue.split(",", 2)
        if len(messageList) == 2:
            if messageList[0] == "0":   # command info
                logging.getLogger().info(messageList[1])
            elif messageList[0] == "1":     # command warning
                logging.getLogger().warning(messageList[1])
            elif messageList[0] == "2":     # command error
                logging.getLogger().error(messageList[1])
                
                
                
    def newPositionChanged(self, pValue):        
        self.__newPosition = pValue          
        if self.__setPosition:
            self.__setPosition = False
            if self.__newPosition == -1:
                Qt.QMessageBox.information(self.brick_widget, "Info", "Not enough counts to calculate the inflexion point of the diamond!")
            elif self.__newPosition > 0:
                if Qt.QMessageBox.question(self.brick_widget, "Info", "Do you accept '%s' as the inflexion point?" % self.__newPosition, Qt.QMessageBox.Yes, Qt.QMessageBox.No, Qt.QMessageBox.NoButton) == Qt.QMessageBox.Yes:    
                    self.getObject("calibration").setPosition(self.__newPosition)
                
                
   
    def expertModeChanged(self, pValue):
        self.__expertMode = pValue
        self.commandPushButton.setEnabled(not self.__expertModeOnly or self.__expertMode)
                    
   
   
    def connectionStatusChanged(self, pPeer):        
        pass


