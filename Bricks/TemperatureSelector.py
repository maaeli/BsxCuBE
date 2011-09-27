import sys
from PyQt4 import Qt

class TemperatureSelector(Qt.QDialog):

    def __init__(self,title="Temperature",initvalue=20,minvalue=4,maxvalue=40):
        
        Qt.QDialog.__init__(self)
        self.setWindowTitle("Storage temperature")
        self.setModal(True)
        
        vBoxLayout = Qt.QVBoxLayout()
        self.setLayout(vBoxLayout)
        
        vBoxLayout.addWidget(Qt.QLabel("Please, select %s:" % title))        
        self.temperatureDoubleSpinBox = Qt.QDoubleSpinBox()
        self.temperatureDoubleSpinBox.setSuffix(" C")
        self.temperatureDoubleSpinBox.setDecimals(2)        
        self.temperatureDoubleSpinBox.setRange(minvalue, maxvalue)        

        try:
            initvalue = float(initvalue)
        except:
            initvalue = 20
        self.temperatureDoubleSpinBox.setValue(initvalue)        

        vBoxLayout.addWidget(self.temperatureDoubleSpinBox)
                
        buttonHBoxLayout = Qt.QHBoxLayout()
        okPushButton = Qt.QPushButton("Ok")
        Qt.QObject.connect(okPushButton, Qt.SIGNAL("clicked()"), self.okPushButtonClicked)
        buttonHBoxLayout.addWidget(okPushButton)
        cancelPushButton = Qt.QPushButton("Cancel" )
        Qt.QObject.connect(cancelPushButton, Qt.SIGNAL("clicked()"), self.cancelPushButtonClicked)
        buttonHBoxLayout.addWidget(cancelPushButton)        

        vBoxLayout.addLayout(buttonHBoxLayout)

    def cancelPushButtonClicked(self):
        self.reject()

    def okPushButtonClicked(self):
        self.accept()

    def getTemperature(self):
        return self.temperatureDoubleSpinBox.value()
                        
def getTemperature(title="Temperature",initvalue=20,minvalue=4, maxvalue=40):

    dialog = TemperatureSelector(title,initvalue,minvalue,maxvalue)

    if dialog.exec_() ==  Qt.QDialog.Accepted:
       return dialog.getTemperature()
    else:
       return None

if __name__ == '__main__':
    app = Qt.QApplication( sys.argv )
    print getTemperature()

