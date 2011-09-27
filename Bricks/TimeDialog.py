import sys
from PyQt4 import Qt

class TimeDialog(Qt.QDialog):

    def __init__(self, title="Time"): 

        Qt.QDialog.__init__(self) 

        self.setWindowTitle(title)
        self.setModal(True)

        vBoxLayout = Qt.QVBoxLayout()
        
        timeHBoxLayout = Qt.QHBoxLayout()
        timeHBoxLayout.addWidget(Qt.QLabel("Time"))
        self.timeSpinBox = Qt.QSpinBox()
        self.timeSpinBox.setSuffix(" s")
        self.timeSpinBox.setRange(1, 1000)
        self.timeSpinBox.setValue(10)
        timeHBoxLayout.addWidget(self.timeSpinBox)
        vBoxLayout.addLayout(timeHBoxLayout)        
        
        buttonHBoxLayout = Qt.QHBoxLayout()
        okPushButton = Qt.QPushButton("Ok")
        Qt.QObject.connect(okPushButton, Qt.SIGNAL("clicked()"), self.okPushButtonClicked)
        buttonHBoxLayout.addWidget(okPushButton)
        cancelPushButton = Qt.QPushButton("Cancel")
        Qt.QObject.connect(cancelPushButton, Qt.SIGNAL("clicked()"), self.cancelPushButtonClicked)
        buttonHBoxLayout.addWidget(cancelPushButton)        
        vBoxLayout.addLayout(buttonHBoxLayout)

        self.setLayout(vBoxLayout)

    def getTimeValue(self):
        return self.timeSpinBox.value() 

    def cancelPushButtonClicked(self):
        self.reject()

    def okPushButtonClicked(self):
        self.accept()
                
def getTime(title=None):

    dialog = TimeDialog(title)

    if dialog.exec_() ==  Qt.QDialog.Accepted:
       return dialog.getTimeValue()
    else:
       return None


if __name__ == '__main__':
    app = Qt.QApplication( sys.argv )
    print getTime()
