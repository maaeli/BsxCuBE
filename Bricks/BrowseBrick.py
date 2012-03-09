import logging
import os
from Framework4.GUI import Core
from Framework4.GUI.Core import Property, Connection, Signal, Slot
from PyQt4 import QtCore, QtGui, Qt

__category__ = "BsxCuBE"



class BrowseBrick(Core.BaseBrick):

    properties = {"enableType": Property("boolean", "Enable type", "", "enableTypeChanged", True)}
    connections = {"browse": Connection("Browse object",
                                        [Signal("browseTypeChanged", "browseTypeChanged"),
                                         Signal("browseLocationChanged", "browseLocationChanged")],
                                        [],
                                        "connectionStatusChanged"),
                    "image_proxy": Connection("image proxy",
                                             [],
                                             [Slot('load_files')])
                   }




    signals = [Signal("displayResetChanged"),
               Signal("displayItemChanged")]
    slots = []


    def browseTypeChanged(self, pValue):
        if pValue is not None:
           self.typeComboBox.setCurrentIndex(int(pValue))

    def browseLocationChanged(self, pValue):
        if pValue is not None:
           self.locationLineEdit.setText(pValue)

    def connectionStatusChanged(self, pPeer):
        pass



    def __init__(self, *args, **kargs):
        Core.BaseBrick.__init__(self, *args, **kargs)


    def init(self):
        self.__expertMode = False
        self.__formats = [["All", ""], ["Raw EDF  (*.edf)", "edf"], ["Normalised EDF  (*.edf)", "edf"], ["Bruker  (*.gfrm)", "gfrm"], ["ADSC  (*.img)", "img"], ["Mar CCD  (*.mccd)", "mccd"], ["SPEC  (*.dat)", "dat"]]


        self.brick_widget.setLayout(Qt.QVBoxLayout())
        self.brick_widget.layout().setAlignment(QtCore.Qt.AlignTop)
        self.brick_widget.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)

        self.hBoxLayout0 = Qt.QHBoxLayout()
        self.typeLabel = Qt.QLabel("Type", self.brick_widget)
        self.typeLabel.setFixedWidth(130)
        self.hBoxLayout0.addWidget(self.typeLabel)
        self.typeComboBox = Qt.QComboBox(self.brick_widget)
        self.typeComboBox.addItems(["Normal", "HDF"])
        Qt.QObject.connect(self.typeComboBox, Qt.SIGNAL("currentIndexChanged(int)"), self.typeComboBoxChanged)
        self.hBoxLayout0.addWidget(self.typeComboBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout0)

        self.hBoxLayout1 = Qt.QHBoxLayout()
        self.locationLabel = Qt.QLabel(self.brick_widget)
        self.locationLabel.setFixedWidth(130)
        self.hBoxLayout1.addWidget(self.locationLabel)
        self.locationLineEdit = Qt.QLineEdit(self.brick_widget)
        self.locationLineEdit.setMaxLength(100)
        Qt.QObject.connect(self.locationLineEdit, Qt.SIGNAL("textChanged(const QString &)"), self.locationLineEditChanged)
        self.hBoxLayout1.addWidget(self.locationLineEdit)
        self.locationPushButton = Qt.QPushButton("...", self.brick_widget)
        self.locationPushButton.setFixedWidth(25)
        Qt.QObject.connect(self.locationPushButton, Qt.SIGNAL("clicked()"), self.locationPushButtonClicked)
        self.hBoxLayout1.addWidget(self.locationPushButton)
        self.brick_widget.layout().addLayout(self.hBoxLayout1)

        self.hBoxLayout2 = Qt.QHBoxLayout()
        self.formatLabel = Qt.QLabel("Format", self.brick_widget)
        self.formatLabel.setFixedWidth(130)
        self.hBoxLayout2.addWidget(self.formatLabel)
        self.formatComboBox = Qt.QComboBox(self.brick_widget)
        Qt.QObject.connect(self.formatComboBox, Qt.SIGNAL("currentIndexChanged(int)"), self.formatComboBoxChanged)
        self.hBoxLayout2.addWidget(self.formatComboBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout2)

        self.hBoxLayout3 = Qt.QHBoxLayout()
        self.prefixLabel = Qt.QLabel("Prefix", self.brick_widget)
        self.prefixLabel.setFixedWidth(130)
        self.hBoxLayout3.addWidget(self.prefixLabel)
        self.prefixComboBox = Qt.QComboBox(self.brick_widget)
        Qt.QObject.connect(self.prefixComboBox, Qt.SIGNAL("currentIndexChanged(int)"), self.prefixComboBoxChanged)
        self.hBoxLayout3.addWidget(self.prefixComboBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout3)

        self.hBoxLayout4 = Qt.QHBoxLayout()
        self.runNumberLabel = Qt.QLabel("Run #", self.brick_widget)
        self.runNumberLabel.setFixedWidth(130)
        self.hBoxLayout4.addWidget(self.runNumberLabel)
        self.runNumberComboBox = Qt.QComboBox(self.brick_widget)
        Qt.QObject.connect(self.runNumberComboBox, Qt.SIGNAL("currentIndexChanged(int)"), self.runNumberComboBoxChanged)
        self.hBoxLayout4.addWidget(self.runNumberComboBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout4)

        self.hBoxLayout5 = Qt.QHBoxLayout()
        self.extraLabel = Qt.QLabel("Extra", self.brick_widget)
        self.extraLabel.setFixedWidth(130)
        self.hBoxLayout5.addWidget(self.extraLabel)
        self.extraComboBox = Qt.QComboBox(self.brick_widget)
        Qt.QObject.connect(self.extraComboBox, Qt.SIGNAL("currentIndexChanged(int)"), self.extraComboBoxChanged)
        self.hBoxLayout5.addWidget(self.extraComboBox)
        self.brick_widget.layout().addLayout(self.hBoxLayout5)

        self.hBoxLayout6 = Qt.QHBoxLayout()
        self.itemsLabel = Qt.QLabel("Items (0)", self.brick_widget)
        self.itemsLabel.setFixedWidth(130)
        self.hBoxLayout6.addWidget(self.itemsLabel)
        self.itemsListWidget = Qt.QListWidget(self.brick_widget)
        Qt.QObject.connect(self.itemsListWidget, Qt.SIGNAL("itemSelectionChanged()"), self.itemsListWidgetChanged)
        self.hBoxLayout6.addWidget(self.itemsListWidget)
        self.brick_widget.layout().addLayout(self.hBoxLayout6)

        self.vBoxLayout0 = Qt.QVBoxLayout()
        self.vBoxLayout0.addSpacing(20)
        self.brick_widget.layout().addLayout(self.vBoxLayout0)

        self.hBoxLayout7 = Qt.QHBoxLayout()
        self.refreshPushButton = Qt.QPushButton("Refresh", self.brick_widget)
        self.refreshPushButton.setToolTip("Refresh item list with the specified parameters")
        self.hBoxLayout7.addWidget(self.refreshPushButton)
        Qt.QObject.connect(self.refreshPushButton, Qt.SIGNAL("clicked()"), self.refreshPushButtonClicked)
        self.brick_widget.layout().addLayout(self.hBoxLayout7)

        self.typeComboBoxChanged(self.typeComboBox.currentIndex())
        self.locationLineEditChanged(None)

    def delete(self):
        pass


    def enableTypeChanged(self, pValue):
        self.typeComboBox.setVisible(pValue)
        self.typeLabel.setVisible(pValue)
        self.typeComboBox.setCurrentIndex(0)


    def typeComboBoxChanged(self, pValue):
        self.formatComboBox.clear()
        if pValue == 0:
            self.locationLabel.setText("Directory")
            for description, extension in self.__formats:
                self.formatComboBox.addItem(description)
        else:
            self.locationLabel.setText("File")
            self.formatComboBox.addItems(["Raw EDF  (frame)", "Normalised EDF  (frame)", "SPEC  (curve)"])
        self.locationChanged(self.locationLineEdit.text(), pValue)



    def locationLineEditChanged(self, pValue):
        self.locationChanged(pValue, self.typeComboBox.currentIndex())



    def locationChanged(self, pValue, pType):
        if pType == 0:  # directory
            if pValue is not None and os.path.exists(pValue) and not os.path.isfile(pValue):
                if str(pValue).find(" ") == -1:
                    self.locationLineEdit.palette().setColor(QtGui.QPalette.Base, QtGui.QColor(255, 255, 255))
                else:
                    self.locationLineEdit.palette().setColor(QtGui.QPalette.Base, QtGui.QColor(255, 255, 0))
            else:
                self.locationLineEdit.palette().setColor(QtGui.QPalette.Base, QtGui.QColor(255, 0, 0))
        else:   # HDF file
            if pValue is not None and os.path.exists(pValue) and os.path.isfile(pValue):
                self.locationLineEdit.palette().setColor(QtGui.QPalette.Base, QtGui.QColor(255, 255, 255))
            else:
                self.locationLineEdit.palette().setColor(QtGui.QPalette.Base, QtGui.QColor(255, 0, 0))
        self.locationLineEdit.update()
        self.populatePrefixComboBox()
        self.populateRunNumberComboBox()
        self.populateExtraComboBox()
        self.populateItemsListWidget()



    def locationPushButtonClicked(self):
        if self.typeComboBox.currentIndex() == 0:
            qFileDialog = QtGui.QFileDialog(self.brick_widget, "Choose a directory", self.locationLineEdit.text())
            qFileDialog.setFileMode(QtGui.QFileDialog.DirectoryOnly)
        else:
            qFileDialog = QtGui.QFileDialog(self.brick_widget, "Choose a HDF file", self.locationLineEdit.text())
            qFileDialog.setAcceptMode(QtGui.QFileDialog.AcceptOpen)
            qFileDialog.setFilters(["Hierarchical Data Format (*.h5; *.hdf5)"])
        if qFileDialog.exec_():
            self.locationLineEdit.setText(str(qFileDialog.selectedFiles()[0]))




    def formatComboBoxChanged(self, pValue):
        if self.typeComboBox.currentIndex() == 0:
            directory = ("", "raw", "2d", "raw", "raw", "raw", "1d")[self.formatComboBox.currentIndex()]
            if directory != "":
                directoryList = str(self.locationLineEdit.text()).split("/")
                for i in range(len(directoryList) - 1, -1, -1):
                    if directoryList[i] != "":
                        if directoryList[i] in ("raw", "1d", "2d"):
                            directoryList[i] = directory
                        else:
                            directoryList.insert(i + 1, directory)
                        break
                directory = ""
                for i in range(0, len(directoryList)):
                    if directoryList[i] != "":
                        directory += "/" + directoryList[i]
                if os.path.exists(directory):
                    self.locationLineEdit.setText(directory)

            if self.formatComboBox.currentIndex() == 6:
                self.itemsListWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
            else:
                self.itemsListWidget.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        else:
            pass    # implement HDF

        self.populatePrefixComboBox()
        self.populateRunNumberComboBox()
        self.populateExtraComboBox()
        self.populateItemsListWidget()


    def prefixComboBoxChanged(self, pValue):
        self.populateRunNumberComboBox()
        self.populateExtraComboBox()
        self.populateItemsListWidget()


    def runNumberComboBoxChanged(self, pValue):
        self.populateExtraComboBox()
        self.populateItemsListWidget()



    def extraComboBoxChanged(self, pValue):
        self.populateItemsListWidget()


    def itemsListWidgetChanged(self):
        if str(self.locationLineEdit.text()).endswith("/"):
            directory0 = self.locationLineEdit.text()
        else:
            directory0 = self.locationLineEdit.text() + "/"
        items = ""
        for item in self.itemsListWidget.selectedItems():
            if items == "":
                items = str(directory0 + item.text())
            else:
                items += "," + str(directory0 + item.text())
            if item.text().split(".")[-1] != "dat":
                directoryList = str(self.locationLineEdit.text()).split("/")
                for i in range(len(directoryList) - 1, -1, -1):
                    if directoryList[i] != "":
                        if directoryList[i] in ("raw", "2d"):
                            directoryList[i] = "1d"
                        else:
                            directoryList.insert(i + 1, "1d")
                        break
                directory1 = ""
                for i in range(0, len(directoryList)):
                    if directoryList[i] != "":
                        directory1 += "/" + directoryList[i]
                filename = str(directory1 + "/" + item.text().split(".")[0] + ".dat")
                if os.path.exists(filename):
                    items += "," + filename
        self.emit("displayItemChanged", items)
        self.getObject('image_proxy').load_files(items.split(','))




    def refreshPushButtonClicked(self):
        self.populateItemsListWidget()



    def populatePrefixComboBox(self):
        items = []
        if self.typeComboBox.currentIndex() == 0:
            try:
                comboFormat = self.__formats[self.formatComboBox.currentIndex()][1]
                for filename in os.listdir(self.locationLineEdit.text()):
                    if os.path.isfile(self.locationLineEdit.text() + "/" + filename):
                        prefix, run, frame, extra, extension = self.getFilenameDetails(filename)
                        flag = False
                        if self.formatComboBox.currentIndex() == 0:
                            for i in range(1, len(self.__formats)):
                                if extension == self.__formats[i][1]:
                                    flag = True
                                    break
                        else:
                            flag = (extension == comboFormat)
                        if flag:
                            try:
                                items.index(prefix)
                            except ValueError:
                                items.append(prefix)
            except Exception, e:
                logging.getLogger().error("Ignored Exception: " + e)
                pass
        else:
            logging.getLogger().error("Unexpected HDF file")
            pass    # implement HDF  
        items.sort()
        items.insert(0, "All")
        currentText = self.prefixComboBox.currentText()
        self.prefixComboBox.clear()
        self.prefixComboBox.addItems(items)
        try:
            self.prefixComboBox.setCurrentIndex(items.index(currentText))
        except ValueError:
            self.prefixComboBox.setCurrentIndex(0)



    def populateRunNumberComboBox(self):
        items = []
        if self.typeComboBox.currentIndex() == 0:
            try:
                for filename in os.listdir(self.locationLineEdit.text()):
                    prefix, run, frame, extra, extension = self.getFilenameDetails(filename)
                    if run != "":
                        if self.prefixComboBox.currentIndex() == 0 or prefix == self.prefixComboBox.currentText():
                            try:
                                items.index(run)
                            except ValueError:
                                items.append(run)
            except Exception, e:
                logging.getLogger().error("Ignored Exception: " + e)
                pass
        else:
            logging.getLogger().error("Unexpected HDF file")
            pass    # implement HDF  
        items.sort(reverse = True)
        items.insert(0, "All")
        currentText = self.runNumberComboBox.currentText()
        self.runNumberComboBox.clear()
        self.runNumberComboBox.addItems(items)
        try:
            self.runNumberComboBox.setCurrentIndex(items.index(currentText))
        except ValueError:
            self.runNumberComboBox.setCurrentIndex(0)




    def populateExtraComboBox(self):
        items = []
        if self.typeComboBox.currentIndex() == 0:
            try:
                for filename in os.listdir(self.locationLineEdit.text()):
                    prefix, run, frame, extra, extension = self.getFilenameDetails(filename)
                    #if len(extra) > 0:
                    if (self.prefixComboBox.currentIndex() == 0 or prefix == self.prefixComboBox.currentText()) and (self.runNumberComboBox.currentIndex() == 0 or run == self.runNumberComboBox.currentText()):
                        try:
                            items.index(extra)
                        except ValueError:
                            items.append(extra)
            except Exception, e:
                logging.getLogger().error("Ignored Exception: " + e)
                pass
        else:
            logging.getLogger().error("Unexpected HDF file")
            pass    # implement HDF
        items.sort()
        items.insert(0, "All")
        currentText = self.extraComboBox.currentText()
        self.extraComboBox.clear()
        self.extraComboBox.addItems(items)
        try:
            self.extraComboBox.setCurrentIndex(items.index(currentText))
        except ValueError:
            self.extraComboBox.setCurrentIndex(0)




    def populateItemsListWidget(self):
        self.itemsListWidget.blockSignals(True)
        items = []
        if self.typeComboBox.currentIndex() == 0:
            try:
                comboFormat = self.__formats[self.formatComboBox.currentIndex()][1]
                for filename in os.listdir(self.locationLineEdit.text()):
                    if os.path.isfile(self.locationLineEdit.text() + "/" + filename):
                        prefix, run, frame, extra, extension = self.getFilenameDetails(filename)
                        if comboFormat == "":
                            flag = False
                            for i in range(1, len(self.__formats)):
                                if extension == self.__formats[i][1]:
                                    flag = True
                                    break
                        else:
                            flag = (extension == comboFormat)
                        if flag:
                            if (self.prefixComboBox.currentIndex() == 0 or prefix == self.prefixComboBox.currentText()) and (self.runNumberComboBox.currentIndex() == 0 or self.runNumberComboBox.currentText() == run) and (self.extraComboBox.currentIndex() == 0 or extra == self.extraComboBox.currentText()):
                                items.append(filename)
            except Exception, e:
                logging.getLogger().error("Ignored Exception: " + e)
                pass
        else:
            logging.getLogger().error("Unexpected HDF file")
            pass    # implement HDF
        items.sort(reverse = True)
        itemsSelect = []
        for i in range(0, self.itemsListWidget.count()):
            if self.itemsListWidget.item(i).isSelected():
                itemsSelect.append(self.itemsListWidget.item(i).text())

        self.itemsListWidget.clear()
        self.itemsListWidget.addItems(items)

        for i in range(0, self.itemsListWidget.count()):
            if self.itemsListWidget.item(i).text() in itemsSelect:
                self.itemsListWidget.item(i).setSelected(True)

        self.itemsLabel.setText("Items (" + str(self.itemsListWidget.count()) + ")")
        self.itemsListWidget.blockSignals(False)



    def getFilenameDetails(self, pFilename):
        pFilename = str(pFilename)
        i = pFilename.rfind(".")
        if i == -1:
            fileName = pFilename
            extension = ""
        else:
            fileName = pFilename[:i]
            extension = pFilename[i + 1:]
        items = fileName.split("_")
        prefix = items[0]
        run = ""
        frame = ""
        extra = ""
        i = len(items)
        j = 1
        while j < i:
            if items[j].isdigit():
                run = items[j]
                j += 1
                break
            else:
                prefix.join("_".join(items[j]))
                j += 1
        if j < i:
            if items[j].isdigit():
                frame = items[j]
                j += 1
            while j < i:
                if extra == "":
                    extra = items[j]
                else:
                    extra.join("_".join(items[j]))
                j += 1

        return prefix, run, frame, extra, extension

