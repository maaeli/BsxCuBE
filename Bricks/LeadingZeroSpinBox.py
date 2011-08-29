#
#    

from PyQt4 import Qt

class LeadingZeroSpinBox(Qt.QSpinBox):

    def __init__(self, pParent, pLeadingZero):
        self.__leadingZero = pLeadingZero
        Qt.QSpinBox.__init__(self, pParent)
        
    def textFromValue(self, pValue):        
        return ("%0" + str(self.__leadingZero) + "d") % pValue
        
