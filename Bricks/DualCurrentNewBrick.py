import logging
import sip
from Framework4.GUI import Core
from Framework4.GUI.Core import Property, Connection, Signal
from PyQt4 import QtGui, Qt



# =============================================
#  BLISS FRAMEWORK CATEGORY
# =============================================
__category__ = "General"


# =============================================
#  CLASS DEFINITION
# =============================================
class DualCurrentNewBrick(Core.BaseBrick):



    # =============================================
    #  PROPERTIES/CONNECTIONS DEFINITION
    # =============================================            
    properties = {"label1": Property("string", "Label value1", "", "label1Changed"),
                  "maskFormat1": Property("string", "Mask format1", "", "maskFormat1Changed"),
                  "suffix1": Property("string", "Suffix1", "", "suffix1Changed"),
                  "minimumValue1": Property("float", "Minimum value1", "", "minimumValue1Changed"),
                  "maximumValue1": Property("float", "Maximum value1", "", "maximumValue1Changed"),
                  "label2": Property("string", "Label value2", "", "label2Changed"),
                  "maskFormat2": Property("string", "Mask format2", "", "maskFormat2Changed"),
                  "suffix2": Property("string", "Suffix2", "", "suffix2Changed"),
                  "minimumValue2": Property("float", "Minimum value2", "", "minimumValue2Changed"),
                  "maximumValue2": Property("float", "Maximum value2", "", "maximumValue2Changed"),
                  "maximumHistory": Property("integer", "Maximum history", "", "maximumHistoryChanged")}

    connections = {"reading1": Connection("DualCurrentNew object1",
                                        [Signal("value1Changed", "value1Changed")],
                                        [],
                                        "connectionStatusChanged"),
                   "reading2": Connection("DualCurrentNew object2",
                                        [Signal("value2Changed", "value2Changed")],
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
        self.__filtersDialog = None
        self.__label1 = ""
        self.__maskFormat1 = ""
        self.__suffix1 = ""
        self.__minimumValue1 = 0
        self.__maximumValue1 = 100
        self.__label2 = ""
        self.__maskFormat2 = ""
        self.__suffix2 = ""
        self.__minimumValue2 = 0
        self.__maximumValue2 = 100

        self.vboxLayout = Qt.QVBoxLayout()
        self.hBox1Layout = Qt.QHBoxLayout()

        self.brick_widget.setLayout(self.vboxLayout)

        self.value1Label = Qt.QLabel(self.__label1 + " (current, new)", self.brick_widget)
        self.hBox1Layout.addWidget(self.value1Label)

        self.currentValue1LineEdit = Qt.QLineEdit(self.brick_widget)
        self.currentValue1LineEdit.setEnabled(False)
        self.currentValue1LineEdit.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.currentValue1LineEdit.setToolTip("Current " + self.__label1)
        self.hBox1Layout.addWidget(self.currentValue1LineEdit)

        self.newValue1ComboBox = Qt.QComboBox(self.brick_widget)
        self.newValue1ComboBox.setEditable(True)
        self.newValue1ComboBox.lineEdit().setMaxLength(10)
        self.newValue1ComboBox.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.newValue1ComboBox.setToolTip("New " + self.__label1)
        Qt.QObject.connect(self.newValue1ComboBox, Qt.SIGNAL("editTextChanged(const QString &)"), self.newValue1ComboBoxChanged)
        Qt.QObject.connect(self.newValue1ComboBox.lineEdit(), Qt.SIGNAL("returnPressed()"), self.newValue1ComboBoxReturnPressed)
        self.hBox1Layout.addWidget(self.newValue1ComboBox)

        self.newValue1ComboBoxChanged(None)

        self.brick_widget.layout().addLayout(self.hBox1Layout)

        self.hBox2Layout = Qt.QHBoxLayout()

        self.value2Label = Qt.QLabel(self.__label2 + " (current, new)", self.brick_widget)
        self.hBox2Layout.addWidget(self.value2Label)

        self.currentValue2LineEdit = Qt.QLineEdit(self.brick_widget)
        self.currentValue2LineEdit.setEnabled(False)
        self.currentValue2LineEdit.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.currentValue2LineEdit.setToolTip("Current " + self.__label2)
        self.hBox2Layout.addWidget(self.currentValue2LineEdit)

        self.newValue2ComboBox = Qt.QComboBox(self.brick_widget)
        self.newValue2ComboBox.setEditable(True)
        self.newValue2ComboBox.lineEdit().setMaxLength(10)
        self.newValue2ComboBox.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.newValue2ComboBox.setToolTip("New " + self.__label2)
        Qt.QObject.connect(self.newValue2ComboBox, Qt.SIGNAL("editTextChanged(const QString &)"), self.newValue2ComboBoxChanged)
        Qt.QObject.connect(self.newValue2ComboBox.lineEdit(), Qt.SIGNAL("returnPressed()"), self.newValue2ComboBoxReturnPressed)
        self.hBox2Layout.addWidget(self.newValue2ComboBox)

        self.newValue2ComboBoxChanged(None)

        self.brick_widget.layout().addLayout(self.hBox2Layout)


    # =============================================
    #  HANDLE PROPERTIES CHANGES
    # =============================================
    def label1Changed(self, pValue):
        self.__label1 = pValue
        self.value1Label.setText(self.__label1)
        self.currentValue1LineEdit.setToolTip("Current " + self.__label1)
        self.newValue1ComboBox.setToolTip("New " + self.__label1)


    def label2Changed(self, pValue):
        self.__label2 = pValue
        self.value2Label.setText(self.__label2)
        self.currentValue2LineEdit.setToolTip("Current " + self.__label2)
        self.newValue2ComboBox.setToolTip("New " + self.__label2)

    def maskFormat1Changed(self, pValue):
        self.__maskFormat1 = pValue
        self.attenuators1FactorChanged(self.currentValue1LineEdit.text())

    def maskFormat2Changed(self, pValue):
        self.__maskFormat2 = pValue
        self.attenuators2FactorChanged(self.currentValue2LineEdit.text())

    def suffix1Changed(self, pValue):
        self.__suffix1 = pValue

    def suffix2Changed(self, pValue):
        self.__suffix2 = pValue

    def minimumValue1Changed(self, pValue):
        self.__minimumValue1 = pValue
        self.newValue1ComboBox.lineEdit().setValidator(Qt.QDoubleValidator(self.__minimumValue1, self.__maximumValue1, 10, self.newValue1ComboBox.lineEdit()))

    def minimumValue2Changed(self, pValue):
        self.__minimumValue2 = pValue
        self.newValue2ComboBox.lineEdit().setValidator(Qt.QDoubleValidator(self.__minimumValue2, self.__maximumValue2, 10, self.newValue2ComboBox.lineEdit()))

    def maximumValue1Changed(self, pValue):
        self.__maximumValue2 = pValue
        self.newValue1ComboBox.lineEdit().setValidator(Qt.QDoubleValidator(self.__minimumValue1, self.__maximumValue1, 10, self.newValue1ComboBox.lineEdit()))

    def maximumValue2Changed(self, pValue):
        self.__maximumValue2 = pValue
        self.newValue2ComboBox.lineEdit().setValidator(Qt.QDoubleValidator(self.__minimumValue2, self.__maximumValue2, 10, self.newValue2ComboBox.lineEdit()))


    def maximumHistoryChanged(self, pValue):
        self.newValue1ComboBox.setMaxCount(pValue)
        self.newValue2ComboBox.setMaxCount(pValue)

    # =============================================
    #  HANDLE SIGNALS
    # =============================================


    def attenuators1FactorChanged(self, pValue):
        if pValue == "":
            self.currentValue1LineEdit.setText(self.__suffix1)
        else:
            if self.__maskFormat1 == "":
                self.currentValue1LineEdit.setText(str(float(pValue)) + self.__suffix1)
            else:
                self.currentValue1LineEdit.setText(self.__maskFormat1 % float(pValue) + self.__suffix1)

    def attenuators2FactorChanged(self, pValue):
        if pValue == "":
            self.currentValue2LineEdit.setText(self.__suffix2)
        else:
            if self.__maskFormat2 == "":
                self.currentValue2LineEdit.setText(str(float(pValue)) + self.__suffix2)
            else:
                self.currentValue2LineEdit.setText(self.__maskFormat2 % float(pValue) + self.__suffix2)

    def transmissionChanged(self, pValue):
        self.getObject("attenuators").setValue1(pValue)
        self.getObject("attenuators").setValue2(pValue)


    def connectionStatusChanged(self, pPeer):
        self.brick_widget.setEnabled(pPeer is not None)



    def newValue1ComboBoxChanged(self, pValue):
        if pValue is None or pValue == "":
            self.newValue1ComboBox.lineEdit().palette().setColor(QtGui.QPalette.Base, QtGui.QColor(255, 255, 0))
        else:
            if self.newValue1ComboBox.lineEdit().hasAcceptableInput():
                self.newValue1ComboBox.lineEdit().palette().setColor(QtGui.QPalette.Base, QtGui.QColor(255, 255, 255))
            else:
                self.newValue1ComboBox.lineEdit().palette().setColor(QtGui.QPalette.Base, QtGui.QColor(255, 0, 0))
        self.newValue1ComboBox.lineEdit().update()


    def newValue1ComboBoxReturnPressed(self):
        if self.newValue1ComboBox.lineEdit().hasAcceptableInput():
            logging.getLogger().info("Setting transmission to " + self.newValue1ComboBox.currentText() + " %...")
            self.getObject("attenuators").setValue1(float(self.newValue1ComboBox.currentText()))
            self.newValue1ComboBox.clearEditText()

    def newValue2ComboBoxChanged(self, pValue):
        if pValue is None or pValue == "":
            self.newValue2ComboBox.lineEdit().palette().setColor(QtGui.QPalette.Base, QtGui.QColor(255, 255, 0))
        else:
            if self.newValue2ComboBox.lineEdit().hasAcceptableInput():
                self.newValue2ComboBox.lineEdit().palette().setColor(QtGui.QPalette.Base, QtGui.QColor(255, 255, 255))
            else:
                self.newValue2ComboBox.lineEdit().palette().setColor(QtGui.QPalette.Base, QtGui.QColor(255, 0, 0))
        self.newValue2ComboBox.lineEdit().update()


    def newValue2ComboBoxReturnPressed(self):
        if self.newValue2ComboBox.lineEdit().hasAcceptableInput():
            logging.getLogger().info("Setting transmission to " + self.newValue2ComboBox.currentText() + " %...")
            self.getObject("attenuators").setValue2(float(self.newValue2ComboBox.currentText()))
            self.newValue2ComboBox.clearEditText()

