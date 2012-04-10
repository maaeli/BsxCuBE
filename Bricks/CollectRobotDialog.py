from PyQt4   import Qt, QtCore
from Samples import *

import logging
import os.path, time

rowletters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

class CollectRobotDialog(Qt.QDialog):

    def __init__(self, parent):

        self.__parent = parent     # Parent is CollectBrick 
        self.__copyLine = []
        self.__history = []

        # To map samples with rows each time we create a sample we give a unique number
        #   the position of a sample in the map should correspond with the row of the sample in the table
        #   throught the operations
        self.sampleIDs = []
        self.sampleIDCount = 0
        self.CBblock = 0     # during swapping callbacks on table rows will be deactivated
        self.filename = ""

        #
        #  we should get this as a signal once the parent brick gets connected. It is zero at creation time
        self.nbPlates = parent.nbPlates
        self.plateInfos = parent.plateInfos

        self.bufferNames = []
        self.copiedSample = None

        # COLS
        self.column_headers = [ "", "", "Use", "Type", "Plate", "Row", "Well", \
                                "Concentration", "Comments", "Code", "Viscosity", "Buffername", \
                                "Transmission", "Volume", "SEU Temp", "Flow", "Recup.", \
                                "Wait Time", "Del"]

        self.UP_COLUMN = 0
        self.DOWN_COLUMN = 1
        self.ENABLE_COLUMN = 2
        self.SAMPLETYPE_COLUMN = 3
        self.PLATE_COLUMN = 4
        self.ROW_COLUMN = 5
        self.WELL_COLUMN = 6
        self.CONCENTRATION_COLUMN = 7
        self.COMMENTS_COLUMN = 8
        self.CODE_COLUMN = 9
        self.VISCOSITY_COLUMN = 10
        self.BUFFERNAME_COLUMN = 11
        self.TRANSMISSION_COLUMN = 12
        self.VOLUME_COLUMN = 13
        self.TEMPERATURE_COLUMN = 14
        self.FLOW_COLUMN = 15
        self.RECUPERATE_COLUMN = 16
        self.WAITTIME_COLUMN = 17
        self.DELETE_COLUMN = 18

        self.PARAMLABEL_WIDTH = 130
        self.PARAMETERS_WIDTH = 220

        Qt.QDialog.__init__(self)

        upfile = os.path.join(os.path.dirname(__file__), "images/up.jpg")
        downfile = os.path.join(os.path.dirname(__file__), "images/down.jpg")
        delfile = os.path.join(os.path.dirname(__file__), "images/delete.jpg")

        uppix = Qt.QPixmap(upfile).scaled(14, 14)
        downpix = Qt.QPixmap(downfile).scaled(15, 15)
        delpix = Qt.QPixmap(delfile).scaled(10, 10)

        self.upIcon = Qt.QIcon(uppix)
        self.downIcon = Qt.QIcon(downpix)
        self.deleteIcon = Qt.QIcon(delpix)

        self.setWindowTitle("Collect using robot (configuration)")
        self.setLayout(Qt.QVBoxLayout())
        self.groupBox = Qt.QGroupBox("Parameters", self)
        self.groupBox.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.vBoxLayout = Qt.QVBoxLayout(self.groupBox)
        self.layout().addWidget(self.groupBox)

        self.hBoxLayout0 = Qt.QHBoxLayout()

        self.fileLabel = Qt.QLabel("File", self)
        self.fileLabel.setFixedWidth(self.PARAMLABEL_WIDTH)
        self.hBoxLayout0.addWidget(self.fileLabel)
        self.fileLineEdit = Qt.QLineEdit(self)
        self.fileLineEdit.setMaxLength(100)
        self.fileLineEdit.setFixedWidth(400)
        self.fileLineEdit.setEnabled(False)

        self.hBoxLayout0.setAlignment(QtCore.Qt.AlignLeft)
        self.hBoxLayout0.addWidget(self.fileLineEdit)

        #self.filePushButton = Qt.QPushButton("...", self)        
        #self.filePushButton.setFixedWidth(25)
        #Qt.QObject.connect(self.filePushButton, Qt.SIGNAL("clicked()"), self.filePushButtonClicked)
        #self.hBoxLayout0.addWidget(self.filePushButton)

        self.loadPushButton = Qt.QPushButton("Load", self)
        self.loadPushButton.setFixedWidth(70)
        Qt.QObject.connect(self.loadPushButton, Qt.SIGNAL("clicked()"), self.loadPushButtonClicked)
        self.hBoxLayout0.addWidget(self.loadPushButton)

        self.savePushButton = Qt.QPushButton("Save", self)
        self.savePushButton.setFixedWidth(70)
        Qt.QObject.connect(self.savePushButton, Qt.SIGNAL("clicked()"), self.savePushButtonClicked)
        self.hBoxLayout0.addWidget(self.savePushButton)


        self.saveAsPushButton = Qt.QPushButton("Save as", self)
        self.saveAsPushButton.setFixedWidth(70)
        Qt.QObject.connect(self.saveAsPushButton, Qt.SIGNAL("clicked()"), self.saveAsPushButtonClicked)
        self.hBoxLayout0.addWidget(self.saveAsPushButton)

        self.vBoxLayout.addLayout(self.hBoxLayout0)

        self.hBoxLayout1 = Qt.QHBoxLayout()
        self.sampleTypeLabel = Qt.QLabel("Sample type", self)
        self.sampleTypeLabel.setFixedWidth(self.PARAMLABEL_WIDTH)
        self.hBoxLayout1.addWidget(self.sampleTypeLabel)
        self.sampleTypeComboBox = Qt.QComboBox(self)
        self.sampleTypeComboBox.addItems(["Green", "Yellow", "Red"])
        self.sampleTypeComboBox.setFixedWidth(self.PARAMETERS_WIDTH)
        self.hBoxLayout1.setAlignment(QtCore.Qt.AlignLeft)
        self.hBoxLayout1.addWidget(self.sampleTypeComboBox)
        self.vBoxLayout.addLayout(self.hBoxLayout1)

        self.hBoxLayout2 = Qt.QHBoxLayout()
        self.storageTemperatureLabel = Qt.QLabel("Storage temperature", self)
        self.storageTemperatureLabel.setFixedWidth(self.PARAMLABEL_WIDTH)
        self.hBoxLayout2.addWidget(self.storageTemperatureLabel)
        self.storageTemperatureDoubleSpinBox = Qt.QDoubleSpinBox(self)
        self.storageTemperatureDoubleSpinBox.setSuffix(" C")
        self.storageTemperatureDoubleSpinBox.setDecimals(2)
        self.storageTemperatureDoubleSpinBox.setRange(4, 40)
        self.storageTemperatureDoubleSpinBox.setValue(20)
        self.storageTemperatureDoubleSpinBox.setFixedWidth(self.PARAMETERS_WIDTH)
        self.hBoxLayout2.setAlignment(QtCore.Qt.AlignLeft)
        self.hBoxLayout2.addWidget(self.storageTemperatureDoubleSpinBox)
        self.vBoxLayout.addLayout(self.hBoxLayout2)

        self.hBoxLayout3 = Qt.QHBoxLayout()
        self.extraFlowTimeLabel = Qt.QLabel("Extra flow time", self)
        self.extraFlowTimeLabel.setFixedWidth(self.PARAMLABEL_WIDTH)
        self.hBoxLayout3.addWidget(self.extraFlowTimeLabel)
        self.extraFlowTimeSpinBox = Qt.QSpinBox(self)
        self.extraFlowTimeSpinBox.setSuffix(" s")
        self.extraFlowTimeSpinBox.setRange(0, 900)
        self.extraFlowTimeSpinBox.setFixedWidth(self.PARAMETERS_WIDTH)
        self.hBoxLayout3.setAlignment(QtCore.Qt.AlignLeft)
        self.hBoxLayout3.addWidget(self.extraFlowTimeSpinBox)
        self.vBoxLayout.addLayout(self.hBoxLayout3)

        self.hBoxLayout4 = Qt.QHBoxLayout()
        self.optimizationLabel = Qt.QLabel("Optimization", self)
        self.optimizationLabel.setFixedWidth(self.PARAMLABEL_WIDTH)
        self.hBoxLayout4.addWidget(self.optimizationLabel)
        self.optimizationComboBox = Qt.QComboBox(self)
        self.optimizationComboBox.addItems(["None", "Sample SEU temperature", "Sample code and SEU temperature"])
        self.optimizationComboBox.setFixedWidth(self.PARAMETERS_WIDTH)
        self.hBoxLayout4.setAlignment(QtCore.Qt.AlignLeft)
        self.hBoxLayout4.addWidget(self.optimizationComboBox)
        self.vBoxLayout.addLayout(self.hBoxLayout4)

        self.hBoxLayout41 = Qt.QHBoxLayout()
        self.initialCleaningLabel = Qt.QLabel("Initial Cleaning", self)
        self.initialCleaningLabel.setFixedWidth(self.PARAMLABEL_WIDTH)
        self.hBoxLayout41.addWidget(self.initialCleaningLabel)
        self.initialCleaningCheckBox = Qt.QCheckBox(self)
        self.initialCleaningCheckBox.setChecked(1)
        self.hBoxLayout41.setAlignment(QtCore.Qt.AlignLeft)
        self.hBoxLayout41.addWidget(self.initialCleaningCheckBox)
        self.vBoxLayout.addLayout(self.hBoxLayout41)

        self.hBoxLayout7 = Qt.QHBoxLayout()
        self.bufferModeLabel = Qt.QLabel("Buffer mode", self)
        self.bufferModeLabel.setFixedWidth(self.PARAMLABEL_WIDTH)
        self.hBoxLayout7.addWidget(self.bufferModeLabel)
        self.bufferModeComboBox = Qt.QComboBox(self)
        self.bufferModeComboBox.addItems(["First and After", "Before", "After", "None"])
        self.bufferModeComboBox.setFixedWidth(self.PARAMETERS_WIDTH)
        self.hBoxLayout7.setAlignment(QtCore.Qt.AlignLeft)
        self.hBoxLayout7.addWidget(self.bufferModeComboBox)
        self.vBoxLayout.addLayout(self.hBoxLayout7)

        self.hBoxLayout5 = Qt.QHBoxLayout()
        self.historyLabel = Qt.QLabel("History", self)
        self.historyLabel.setFixedWidth(self.PARAMLABEL_WIDTH)
        self.hBoxLayout5.addWidget(self.historyLabel)
        self.historyText = Qt.QTextEdit(self)
        self.historyText.setReadOnly(True)
        self.historyText.setFixedWidth(600)
        self.historyText.setFixedHeight(80)
        self.hBoxLayout5.addWidget(self.historyText)
        self.clearHistoryPushButton = Qt.QPushButton("Clear", self)
        self.clearHistoryPushButton.setFixedWidth(50)
        Qt.QObject.connect(self.clearHistoryPushButton, Qt.SIGNAL("clicked()"), self.clearHistoryPushButtonClicked)
        self.hBoxLayout5.addWidget(self.clearHistoryPushButton)
        self.historyLabel.setAlignment(QtCore.Qt.AlignTop)
        self.hBoxLayout5.setAlignment(QtCore.Qt.AlignLeft)
        self.vBoxLayout.addLayout(self.hBoxLayout5)

        # SAMPLE TABLE
        self.hBoxLayout6 = Qt.QHBoxLayout()
        self.tableWidget = Qt.QTableWidget(0, len(self.column_headers), self)
        self.tableWidget.setHorizontalHeaderLabels(self.column_headers)
        #self.tableWidget.verticalHeader().hide()
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.setColumnWidth(self.SAMPLETYPE_COLUMN, 70)
        self.tableWidget.setColumnWidth(self.PLATE_COLUMN, 45)
        self.tableWidget.setColumnWidth(self.ROW_COLUMN, 45)
        self.tableWidget.setColumnWidth(self.WELL_COLUMN, 45)
        self.tableWidget.setColumnWidth(self.COMMENTS_COLUMN, 80)
        self.tableWidget.setColumnWidth(self.CODE_COLUMN, 80)
        self.tableWidget.setColumnWidth(self.VOLUME_COLUMN, 60)
        self.tableWidget.setSelectionBehavior(Qt.QAbstractItemView.SelectRows)
        self.tableWidget.setSelectionMode(Qt.QAbstractItemView.SingleSelection)
        self.hBoxLayout6.addWidget(self.tableWidget)
        self.vBoxLayout.addLayout(self.hBoxLayout6)

        # BUTTONS at END
        self.hBoxLayout8 = Qt.QHBoxLayout()

        self.hBoxLayout8 = Qt.QHBoxLayout()
        self.addPushButton = Qt.QPushButton("Add Sample", self)
        Qt.QObject.connect(self.addPushButton, Qt.SIGNAL("clicked()"), self.addPushButtonClicked)
        self.hBoxLayout8.addWidget(self.addPushButton)

        self.copyPushButton = Qt.QPushButton("Copy Sample", self)
        Qt.QObject.connect(self.copyPushButton, Qt.SIGNAL("clicked()"), self.copyPushButtonClicked)
        self.hBoxLayout8.addWidget(self.copyPushButton)
        self.copyPushButton.setEnabled(0)

        self.pastePushButton = Qt.QPushButton("Paste Sample", self)
        Qt.QObject.connect(self.pastePushButton, Qt.SIGNAL("clicked()"), self.pastePushButtonClicked)
        self.hBoxLayout8.addWidget(self.pastePushButton)
        self.pastePushButton.setEnabled(0)

        self.layout().addLayout(self.hBoxLayout8)

        self.hBoxLayout9 = Qt.QHBoxLayout()
        self.clearPushButton = Qt.QPushButton("Clear Configuration", self)
        self.clearPushButton.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Fixed)
        Qt.QObject.connect(self.clearPushButton, Qt.SIGNAL("clicked()"), self.clearConfigurationPushButtonClicked)
        self.hBoxLayout9.addWidget(self.clearPushButton)

        self.closePushButton = Qt.QPushButton("Close", self)
        self.closePushButton.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Fixed)
        Qt.QObject.connect(self.closePushButton, Qt.SIGNAL("clicked()"), self.closePushButtonClicked)
        self.hBoxLayout9.addWidget(self.closePushButton)
        self.layout().addLayout(self.hBoxLayout9)

        self.setGeometry(400, 200, 1100, 700)
        #
        # Style Sheet
        #
        self.setStyleSheet("*[valid=\"true\"]  {background-color: white}\
                            *[valid=\"false\"] {background-color: #f99}\
                            *[sampletype=\"Buffer\"] {background-color: #eec}\
                            *[sampletype=\"Sample\"] {background-color: #cce}")

    #------------------
    #  createSampleRow.  Creates GUI for each row in sample table
    #-------------------
    def createSampleRow(self, row):

        sampleID = self.sampleIDCount
        self.sampleIDCount += 1

        self.sampleIDs.insert(row, sampleID)

        tableWidget = self.tableWidget

        tableWidget.insertRow(row)

        # buttons
        upButton = Qt.QPushButton(self.upIcon, "", tableWidget)
        upButton.setFlat(True)
        downButton = Qt.QPushButton(self.downIcon, "", tableWidget)
        downButton.setFlat(True)
        deleteButton = Qt.QPushButton(self.deleteIcon, "", tableWidget)
        deleteButton.setFlat(True)
        tableWidget.setCellWidget(row, self.UP_COLUMN, upButton)
        tableWidget.setCellWidget(row, self.DOWN_COLUMN, downButton)
        tableWidget.setCellWidget(row, self.DELETE_COLUMN, deleteButton)

        # TODO.  Signal mapppers keep row at the moment of creation...but row number changes with these actions.
        #    we have to imagine another parameter
        upSignalMapper = Qt.QSignalMapper(self)
        upSignalMapper.setMapping(upButton, sampleID)
        upButton.clicked.connect(upSignalMapper.map)
        upSignalMapper.mapped[int].connect(self.upPushButtonClicked)

        downSignalMapper = Qt.QSignalMapper(self)
        downSignalMapper.setMapping(downButton, sampleID)
        downButton.clicked.connect(downSignalMapper.map)
        downSignalMapper.mapped[int].connect(self.downPushButtonClicked)

        deleteSignalMapper = Qt.QSignalMapper(self)
        deleteSignalMapper.setMapping(deleteButton, sampleID)
        deleteButton.clicked.connect(deleteSignalMapper.map)
        deleteSignalMapper.mapped[int].connect(self.deletePushButtonClicked)


        # enable 
        enableCheckBox = Qt.QCheckBox(tableWidget)
        tableWidget.setCellWidget(row, self.ENABLE_COLUMN, enableCheckBox)

        eSignalMapper = Qt.QSignalMapper(self)
        eSignalMapper.setMapping(enableCheckBox, sampleID)
        enableCheckBox.toggled.connect(eSignalMapper.map)
        eSignalMapper.mapped[int].connect(self.enableCheckBoxToggled)

        # type
        typeComboBox = Qt.QComboBox(tableWidget)
        typeComboBox.addItems(["Buffer", "Sample"])
        tableWidget.setCellWidget(row, self.SAMPLETYPE_COLUMN, typeComboBox)

        # use QSignalMapper to pass row as argument to the event handler
        tSignalMapper = Qt.QSignalMapper(self)
        tSignalMapper.setMapping(typeComboBox, sampleID)
        typeComboBox.currentIndexChanged.connect(tSignalMapper.map)
        tSignalMapper.mapped[int].connect(self.typeComboBoxChanged)

        # plate
        plateComboBox = Qt.QComboBox(tableWidget)
        tableWidget.setCellWidget(row, self.PLATE_COLUMN, plateComboBox)

        # use QSignalMapper to pass row as argument to the event handler
        pSignalMapper = Qt.QSignalMapper(self)
        pSignalMapper.setMapping(plateComboBox, sampleID)
        plateComboBox.currentIndexChanged.connect(pSignalMapper.map)
        pSignalMapper.mapped[int].connect(self.plateComboBoxChanged)


        # row
        rowComboBox = Qt.QComboBox(tableWidget)
        tableWidget.setCellWidget(row, self.ROW_COLUMN, rowComboBox)

        # well
        wellComboBox = Qt.QComboBox(tableWidget)
        tableWidget.setCellWidget(row, self.WELL_COLUMN, wellComboBox)

        # concentration
        concentrationDoubleSpinBox = Qt.QDoubleSpinBox(tableWidget)
        concentrationDoubleSpinBox.setSuffix(" mg/ml")
        concentrationDoubleSpinBox.setDecimals(2)
        concentrationDoubleSpinBox.setRange(0, 100)
        tableWidget.setCellWidget(row, self.CONCENTRATION_COLUMN, concentrationDoubleSpinBox)

        # comments
        commentsLineEdit = Qt.QLineEdit(tableWidget)
        commentsLineEdit.setValidator(Qt.QRegExpValidator(Qt.QRegExp("[a-zA-Z0-9\\%/()=+*^:.\-_ ]*"), commentsLineEdit))
        tableWidget.setCellWidget(row, self.COMMENTS_COLUMN, commentsLineEdit)

        # code
        codeLineEdit = Qt.QLineEdit(tableWidget)
        codeLineEdit.setMaxLength(30)
        codeLineEdit.setValidator(Qt.QRegExpValidator(Qt.QRegExp("^[a-zA-Z][a-zA-Z0-9_]*"), codeLineEdit))
        tableWidget.setCellWidget(row, self.CODE_COLUMN, codeLineEdit)

        # viscosity
        viscosityComboBox = Qt.QComboBox(tableWidget)
        viscosityComboBox.addItems(["Low", "Medium", "High"])
        tableWidget.setCellWidget(row, self.VISCOSITY_COLUMN, viscosityComboBox)

        # buffername
        bufferComboBox = Qt.QComboBox(tableWidget)
        bufferComboBox.setEditable(True)
        tableWidget.setCellWidget(row, self.BUFFERNAME_COLUMN, bufferComboBox)

        bSignalMapper = Qt.QSignalMapper(self)
        bSignalMapper.setMapping(bufferComboBox, sampleID)
        bufferComboBox.editTextChanged.connect(bSignalMapper.map)
        bSignalMapper.mapped[int].connect(self.bufferComboBoxChanged)

        # transmission
        transmissionDoubleSpinBox = Qt.QDoubleSpinBox(tableWidget)
        transmissionDoubleSpinBox.setSuffix(" %")
        transmissionDoubleSpinBox.setDecimals(1)
        transmissionDoubleSpinBox.setRange(0, 100)
        tableWidget.setCellWidget(row, self.TRANSMISSION_COLUMN, transmissionDoubleSpinBox)

        # volume
        volumeSpinBox = Qt.QSpinBox(tableWidget)
        volumeSpinBox.setSuffix(" u/l")
        volumeSpinBox.setRange(5, 150)
        tableWidget.setCellWidget(row, self.VOLUME_COLUMN, volumeSpinBox)

        # temperature
        temperatureSEUDoubleSpinBox = Qt.QDoubleSpinBox(tableWidget)
        temperatureSEUDoubleSpinBox.setSuffix(" C")
        temperatureSEUDoubleSpinBox.setDecimals(2)
        temperatureSEUDoubleSpinBox.setRange(4, 60)
        tableWidget.setCellWidget(row, self.TEMPERATURE_COLUMN, temperatureSEUDoubleSpinBox)

        # flow
        flowCheckBox = Qt.QCheckBox(tableWidget)
        tableWidget.setCellWidget(row, self.FLOW_COLUMN, flowCheckBox)
        recuperateCheckBox = Qt.QCheckBox(tableWidget)
        tableWidget.setCellWidget(row, self.RECUPERATE_COLUMN, recuperateCheckBox)

        # waittime
        waittimeSpinBox = Qt.QDoubleSpinBox(tableWidget)
        waittimeSpinBox.setSuffix(" sec")
        waittimeSpinBox.setDecimals(0)
        waittimeSpinBox.setRange(0, 10000)
        tableWidget.setCellWidget(row, self.WAITTIME_COLUMN, waittimeSpinBox)

        return sampleID


#---------------#
# SLOTS         #
#---------------#
    def clearHistory(self):
        self.historyText.clear()

    def addHistory(self, pLevel, pMessage, notify = 0):
        strLevel = ['INFO', 'WARNING', 'ERROR']
        message = "<i>[%s] %s:</i> <b>%s</b>" % (time.strftime("%Y/%m/%d %H:%M:%S"), strLevel[ pLevel] , pMessage)

        self.historyText.append(message)

    def getCollectRobotPars(self, all = 0):
        params = CollectPars()
        sampleList = SampleList()
        bufferList = SampleList()

        params.sampleType = self.sampleTypeComboBox.currentText()
        params.storageTemperature = self.storageTemperatureDoubleSpinBox.value()
        params.extraFlowTime = self.extraFlowTimeSpinBox.value()
        params.optimization = self.optimizationComboBox.currentIndex()
        params.optimizationText = self.optimizationComboBox.currentText()
        params.initialCleaning = self.initialCleaningCheckBox.isChecked()
        params.bufferMode = self.bufferModeComboBox.currentIndex()

        #=================================================
        # value for processData - THIS BELONGS TO THE MAIN BRICK
        #=================================================
        #if params.doProcess:  # in principle this is not necessary as True and False values should work.  
        # TODO:  check this
        #     params.processData = 1
        #else:
        #     params.processData = 0

        #=================================================
        #  buffer mode
        #=================================================
        params.bufferFirst = False
        params.bufferBefore = False
        params.bufferAfter = False

        if params.bufferMode == 0:
            params.bufferFirst = True
            params.bufferAfter = True
        elif params.bufferMode == 1:
            params.bufferBefore = True
        elif params.bufferMode == 2:
            params.bufferAfter = True

        #=================================================
        # optimization mode
        #=================================================
        params.optimSEUtemp = False
        params.optimCodeAndSEU = False

        if params.optimization == 1:
            params.optimSEUtemp = True
        elif params.optimization == 2:
            params.optimCodeAndSEU = True


        #-----------------------------------------------------
        # 
        # SAMPLES
        # 
        #-----------------------------------------------------
        for i in range(0, self.tableWidget.rowCount()):
            sample = self.getSampleRow(i)

            if all or sample.enable:
                if sample.isBuffer():
                    bufferList.append(sample)
                else:
                    sampleList.append(sample)

        #=================================================
        #  assign buffer to sample
        #  TODO:  allow to assign more than one buffer. all with same name
        #=================================================
        for sample in sampleList:
            sample.buffer = []
            if len(bufferList) == 1:   # if there is one and only one buffer defined dont look at name. assign
                sample.buffer.append(bufferList[0])
            else:
                for buffer in bufferList:
                    if buffer.buffername == sample.buffername:
                        sample.buffer.append(buffer)

        # ==================================================
        #  OPTIMIZE DATA COLLECTION PROCEDURE (IF REQUESTED)
        # ==================================================

        if params.optimSEUtemp:
            sampleList.sortSEUtemp()
        elif params.optimCodeAndSEU:
            sampleList.sortCodeAndSEU()

        params.sampleList = sampleList
        params.bufferList = bufferList

        return params

#---------------#
# CALLBACKS     #
#---------------#

    #------------------------------------------------------------------------
    #  loadPushButton -  Load file with collection parameters and history
    #------------------------------------------------------------------------
    def loadPushButtonClicked(self):

        dirname = ""
        if self.filename != "":
            dirname = os.path.split(self.filename)[0]
        else:
            try:
                dirname = os.path.split(self.__parent.collectpars.directory)
            except Exception, e:
                print "Ignored Exception 5: " + str(e)
                pass

        filename = Qt.QFileDialog.getOpenFileName(self, "Choose a file to load", dirname, "XML File (*.xml)")

        if not filename:
            return

        self.fileLineEdit.setText(filename)
        filename = str(filename)

        self.loadFile(filename)

    def loadFile(self, filename):
        try:
            pars = CollectPars(filename)

            self.clearConfiguration()

            #  Clear first if load was succesful
            # 
            for sampleID in self.sampleIDs:
                index = self.sampleIDs.index(sampleID)
                self.tableWidget.removeRow(index)
                self.sampleIDs.remove(sampleID)

            # 
            # General parameters
            # 
            self.CBblock = 1
            self.setComboBox(self.sampleTypeComboBox, pars.sampleType)

            self.storageTemperatureDoubleSpinBox.setValue(float(pars.storageTemperature))
            self.extraFlowTimeSpinBox.setValue(float(pars.extraFlowTime))

            self.initialCleaningCheckBox.setChecked(pars.initialCleaning)

            # These are saved by index
            self.optimizationComboBox.setCurrentIndex(pars.optimization)
            self.bufferModeComboBox.setCurrentIndex(pars.bufferMode)

            self.historyText.clear()
            self.historyText.setText(pars.history.strip())

            for buffer in  pars.bufferList:
                self.addSampleRow(buffer)
            for sample in  pars.sampleList:
                self.addSampleRow(sample)

            self.CBblock = 0
            self.filename = filename

            Qt.QMessageBox.information(self, "Info", "The file '%s' was successfully loaded!" % filename)
        except Exception, e:
            import traceback
            traceback.print_exc()
            logging.exception('Cannot load collection parameters file. \n')
            logging.getLogger().error("Full Exception: " + str(e))
            Qt.QMessageBox.critical(self, "Error", "Error when trying to read file '%s'!" % filename)

    def saveAsPushButtonClicked(self):

        filename = Qt.QFileDialog.getSaveFileName(self, "Choose a file to save", self.filename, "XML File (*.xml)")
        if not filename:
            return

        filename = str(filename)

        if not str(filename).lower().endswith(".xml"):
            filename += ".xml"
            self.fileLineEdit.setText(filename)

        self.filename = filename
        self.fileLineEdit.setText(filename)
        self.saveFile(filename)

    def savePushButtonClicked(self, filename = None):
        if self.filename == "" or not os.path.isfile(self.filename):
            self.saveAsPushButtonClicked()
        else:
            self.saveFile(self.filename , askrewrite = False)

    def saveFile(self, filename, askrewrite = True):

        if askrewrite and os.path.exists(filename):
            quitsave = Qt.QMessageBox.question(self, "Warning", "The file '%s' already exists. Overwrite it?" % filename, Qt.QMessageBox.Yes, Qt.QMessageBox.No, Qt.QMessageBox.NoButton) != Qt.QMessageBox.Yes
            if quitsave:
                return

        pars = self.getCollectRobotPars(all = 1)
        history = self.historyText.toPlainText()

        try:
            pars.save(filename , history)
            Qt.QMessageBox.information(self, "Info", "The file '%s' was successfully saved!" % filename)
        except Exception, e:
            import traceback
            traceback.print_exc()
            logging.exception('Cannot save collection parameters file.\n')
            logging.getLogger().error("Full Exception: " + str(e))
            Qt.QMessageBox.critical(self, "Error", "Error when trying to save file '%s'!" % filename)


    #
    # Callbacks for table widgets
    #
    @Qt.pyqtSlot(int)
    def enableCheckBoxToggled(self, sampleID):

        if self.CBblock:
              return
        try:
           index = self.sampleIDs.index(sampleID)
           checked = self.tableWidget.cellWidget(index, self.ENABLE_COLUMN).isChecked()
           for col in range(0, self.tableWidget.columnCount()):
               if col != self.ENABLE_COLUMN:
                   self.tableWidget.cellWidget(index, col).setEnabled(checked)
        except AttributeError:
            pass

    @Qt.pyqtSlot(int)
    def bufferComboBoxChanged(self, sampleID):
        if self.CBblock:
              return

        try:
            index = self.sampleIDs.index(sampleID)

            well_type = str(self.tableWidget.cellWidget(index, self.SAMPLETYPE_COLUMN).currentText())

            if well_type == "Sample":
                return

            self.bufferNames = self.getBufferNames()
            self.assignBufferNames()
        except AttributeError:
            pass

    @Qt.pyqtSlot(int)
    def typeComboBoxChanged(self, sampleID):
        if self.CBblock:
              return

        try:
            index = self.sampleIDs.index(sampleID)

            self.CBblock = 1
            self.assignOneBufferName(index, None)
            self.CBblock = 0

            self.formatLine(index)
        except AttributeError:
            pass

    @Qt.pyqtSlot(int)
    def plateComboBoxChanged(self, sampleID):
        if self.CBblock:
              return

        plateInfos = self.__parent.plateInfos

        try:
            index = self.sampleIDs.index(sampleID)
            platevalue = self.tableWidget.cellWidget(index, self.PLATE_COLUMN).currentIndex()

            row = self.tableWidget.cellWidget(index, self.ROW_COLUMN)
            well = self.tableWidget.cellWidget(index, self.WELL_COLUMN)

            nrows = int(plateInfos[platevalue][0])
            ncols = int(plateInfos[platevalue][1])

            #rowvalues  = [str(val) for val in range(1,nrows+1) ] 
            rowvalues = rowletters[:nrows]
            wellvalues = [str(val) for val in range(1, ncols + 1) ]

            row.clear()
            well.clear()

            row.addItems (rowvalues)
            well.addItems(wellvalues)

        except AttributeError:
            pass

#-------------------------------------------
#  Internal functions
#-------------------------------------------


    def setComboBox(self, combo, value):
        for i in range(combo.count()):
            if value == combo.itemText(i):
                combo.setCurrentIndex(i)
                break
        else:
            combo.setCurrentIndex(0)

    def getSampleRow(self, i):
        table = self.tableWidget
        sampleRow = Sample()

        sampleRow.enable = table.cellWidget(i, self.ENABLE_COLUMN).isChecked()
        sampleRow.type = str(table.cellWidget(i, self.SAMPLETYPE_COLUMN).currentText())
        sampleRow.typen = table.cellWidget(i, self.SAMPLETYPE_COLUMN).currentIndex()
        sampleRow.plate = str(table.cellWidget(i, self.PLATE_COLUMN).currentText())
        #sampleRow.row            =  str(table.cellWidget(i, self.ROW_COLUMN).currentText())   
        rowtxt = str(table.cellWidget(i, self.ROW_COLUMN).currentText())
        sampleRow.row = rowletters.index(rowtxt) + 1
        sampleRow.well = str(table.cellWidget(i, self.WELL_COLUMN).currentText())
        sampleRow.concentration = table.cellWidget(i, self.CONCENTRATION_COLUMN).value()
        sampleRow.comments = str(table.cellWidget(i, self.COMMENTS_COLUMN).text())
        sampleRow.code = str(table.cellWidget(i, self.CODE_COLUMN).text())
        sampleRow.viscosity = str(table.cellWidget(i, self.VISCOSITY_COLUMN).currentText())
        sampleRow.buffername = str(table.cellWidget(i, self.BUFFERNAME_COLUMN).currentText())
        sampleRow.transmission = table.cellWidget(i, self.TRANSMISSION_COLUMN).value()
        sampleRow.volume = table.cellWidget(i, self.VOLUME_COLUMN).value()
        sampleRow.flow = table.cellWidget(i, self.FLOW_COLUMN).isChecked()
        sampleRow.recuperate = table.cellWidget(i, self.RECUPERATE_COLUMN).isChecked()
        if sampleRow.type == 'Sample':
            sampleRow.SEUtemperature = table.cellWidget(i, self.TEMPERATURE_COLUMN).value()
            sampleRow.waittime = table.cellWidget(i, self.WAITTIME_COLUMN).value()
        else:
            sampleRow.SEUtemperature = 20.0
            sampleRow.waittime = 0.0
        sampleRow.title = sampleRow.getTitle()

        return sampleRow

    def addSampleRow(self, sample = None, index = -1):

        if sample is None:
            samp = Sample()
            if self.tableWidget.rowCount() == 0:
                samp.type = "Buffer"
            else:
                samp.type = "Sample"
        else:
            samp = sample

        if index == -1:
            index = self.tableWidget.rowCount()

        self.createSampleRow(index)
        self.setSampleRow(index, samp)

        self.copyPushButton.setEnabled(1)
        self.tableWidget.setRangeSelected(Qt.QTableWidgetSelectionRange(0, 0, index - 1, len(self.column_headers) - 1), 0)
        self.tableWidget.setRangeSelected(Qt.QTableWidgetSelectionRange(index, 0, index, len(self.column_headers) - 1), 1)
        self.tableWidget.setCurrentCell(index, 0)

    def removeSampleRow(self, sid):

        index = self.sampleIDs.index(sid)
        self.tableWidget.removeRow(index)
        self.sampleIDs.remove(sid)

        if self.tableWidget.rowCount() == 0:
            self.copyPushButton.setEnabled(0)

    def setSampleRow(self, index, sample):

        tableWidget = self.tableWidget

        plateInfos = self.__parent.plateInfos

        # enable
        tableWidget.cellWidget(index, self.ENABLE_COLUMN).setChecked(sample.enable)

        # type
        typeComboBox = tableWidget.cellWidget(index, self.SAMPLETYPE_COLUMN)
        self.setComboBox (typeComboBox, sample.type)

        # plate, row, well
        plateComboBox = tableWidget.cellWidget(index, self.PLATE_COLUMN)
        rowComboBox = tableWidget.cellWidget(index, self.ROW_COLUMN)
        wellComboBox = tableWidget.cellWidget(index, self.WELL_COLUMN)

        plate = (sample.plate is not None) and (int(sample.plate) - 1) or 0
        row = (sample.row   is not None) and (int(sample.row) - 1)   or 0
        well = (sample.well  is not None) and (int(sample.well) - 1)  or 0

        if plate >= len(plateInfos) or plate < 0: plate = 0

        nplates = len(plateInfos)
        nrows = int(plateInfos[plate][0])
        nwells = int(plateInfos[plate][1])

        if row >= nrows  or row < 0:  row = 0
        if well >= nwells or well < 0: well = 0

        plates = [str(num) for num in range(1, nplates + 1)]
        #rows   = [str(num) for num in range(1,nrows+1)]
        rows = rowletters[:nrows]
        wells = [str(num) for num in range(1, nwells + 1)]

        plateComboBox.clear()

        plateComboBox.addItems(plates)
        plateComboBox.setCurrentIndex(plate)

        rowComboBox.clear()
        wellComboBox.clear()

        rowComboBox.addItems(rows)
        wellComboBox.addItems(wells)

        rowComboBox.setCurrentIndex(row)
        wellComboBox.setCurrentIndex(well)

        # concentration
        concentrationDoubleSpinBox = tableWidget.cellWidget(index, self.CONCENTRATION_COLUMN)
        concentrationDoubleSpinBox.setValue(sample.concentration)

        # comments
        commentsLineEdit = tableWidget.cellWidget(index, self.COMMENTS_COLUMN)
        commentsLineEdit.setText(sample.comments)

        # code 
        codeLineEdit = tableWidget.cellWidget(index, self.CODE_COLUMN)
        codeLineEdit.setText(sample.code)

        # viscosity
        viscosityComboBox = tableWidget.cellWidget(index, self.VISCOSITY_COLUMN)
        self.setComboBox(viscosityComboBox, sample.viscosity)

        # buffername
        bufferComboBox = tableWidget.cellWidget(index, self.BUFFERNAME_COLUMN)

        if sample.type == "Buffer":
            if sample.buffername not in self.bufferNames:
                self.bufferNames.append(sample.buffername)
        self.assignOneBufferName(index, sample.buffername)

        # transmission
        transmissionDoubleSpinBox = tableWidget.cellWidget(index, self.TRANSMISSION_COLUMN)
        transmissionDoubleSpinBox.setValue(sample.transmission)

        # volume
        volumeDoubleSpinBox = tableWidget.cellWidget(index, self.VOLUME_COLUMN)
        volumeDoubleSpinBox.setValue(sample.volume)

        # flow
        flowCheckBox = tableWidget.cellWidget(index, self.FLOW_COLUMN)
        flowCheckBox.setChecked(sample.flow)

        # recuperate
        recuperateCheckBox = tableWidget.cellWidget(index, self.RECUPERATE_COLUMN)
        recuperateCheckBox.setChecked(sample.recuperate)

        # waittime
        if sample.type != 'Buffer':
            waittimeSpinBox = tableWidget.cellWidget(index, self.WAITTIME_COLUMN)
            waittimeSpinBox.setValue(sample.waittime)
        # temperature SEU
        if sample.type != 'Buffer':
            temperatureSEUDoubleSpinBox = tableWidget.cellWidget(index, self.TEMPERATURE_COLUMN)
            temperatureSEUDoubleSpinBox.setValue(sample.SEUtemperature)


        # final arrangementes
        self.formatLine(index, sample)


    def formatLine(self, index, sample = None):

        table = self.tableWidget
        concentration = table.cellWidget(index, self.CONCENTRATION_COLUMN)
        seutemperature = table.cellWidget(index, self.TEMPERATURE_COLUMN)
        bufcombo = table.cellWidget(index, self.BUFFERNAME_COLUMN)
        waittime = table.cellWidget(index, self.WAITTIME_COLUMN)

        well_type = str(self.tableWidget.cellWidget(index, self.SAMPLETYPE_COLUMN).currentText())

        if well_type == 'Buffer':
            concentration.setValue(0)
            concentration.setEnabled(False)
            bufcombo.setEditable(True)
            seutemperature.setEnabled(False)
            self.tableWidget.setCellWidget(index, self.WAITTIME_COLUMN, Qt.QLabel())
            self.tableWidget.setCellWidget(index, self.TEMPERATURE_COLUMN, Qt.QLabel())
        elif well_type == 'Sample':
            concentration.setEnabled(True)
            seutemperature.setEnabled(True)

            temperatureSEUDoubleSpinBox = Qt.QDoubleSpinBox(self.tableWidget)
            temperatureSEUDoubleSpinBox.setSuffix(" C")
            temperatureSEUDoubleSpinBox.setDecimals(2)
            temperatureSEUDoubleSpinBox.setRange(4, 60)
            self.tableWidget.setCellWidget(index, self.TEMPERATURE_COLUMN, temperatureSEUDoubleSpinBox)

            waittimeSpinBox = Qt.QDoubleSpinBox(self.tableWidget)
            waittimeSpinBox.setSuffix(" sec")
            waittimeSpinBox.setDecimals(0)
            waittimeSpinBox.setRange(0, 10000)
            self.tableWidget.setCellWidget(index, self.WAITTIME_COLUMN, waittimeSpinBox)

            buffernames = []
            bufcombo.setEditable(False)

            if sample:
                temperatureSEUDoubleSpinBox.setValue(sample.SEUtemperature)
                waittimeSpinBox.setValue(sample.waittime)

        for i in range(len(self.column_headers)):
            self.tableWidget.cellWidget(index, i).setProperty("sampletype", well_type)

        self.setStyleSheet(self.styleSheet())

    def getBufferNames(self):
        bufferNames = []
        for index in range(self.tableWidget.rowCount()):
            # get all buffer names first
            well_type = str(self.tableWidget.cellWidget(index, self.SAMPLETYPE_COLUMN).currentText())
            if well_type == "Buffer":
                bufferName = str(self.tableWidget.cellWidget(index, self.BUFFERNAME_COLUMN).currentText())
                if bufferName not in bufferNames:
                    bufferNames.append(bufferName)
        return bufferNames


    def assignBufferNames(self):

        for index in range(self.tableWidget.rowCount()):
            well_type = str(self.tableWidget.cellWidget(index, self.SAMPLETYPE_COLUMN).currentText())
            if well_type == "Sample":
                currentBuffer = str(self.tableWidget.cellWidget(index, self.BUFFERNAME_COLUMN).currentText())
                self.assignOneBufferName(index, currentBuffer)

    def assignOneBufferName(self, index, value):
        try:
            self.tableWidget.cellWidget(index, self.BUFFERNAME_COLUMN).clear()
            self.tableWidget.cellWidget(index, self.BUFFERNAME_COLUMN).addItems(self.bufferNames)
            idx = self.bufferNames.index(value)
            if idx != -1:
                self.tableWidget.cellWidget(index, self.BUFFERNAME_COLUMN).setCurrentIndex(idx)
        except AttributeError:
            pass     # there are some uncaught exceptions because when deleting samples some of the callbacks are still there. How to delete the callback?
        except ValueError:
            pass

    def addPushButtonClicked(self):
        index = self.tableWidget.currentRow()
        self.addSampleRow(index = index + 1)

    def copyPushButtonClicked(self):
        index = self.tableWidget.currentRow()
        self.copiedSample = self.getSampleRow(index)
        self.pastePushButton.setEnabled(1)

    def pastePushButtonClicked(self):
        index = self.tableWidget.currentRow()
        self.addSampleRow(index = index + 1)
        if self.copiedSample is not None:
            self.setSampleRow(index + 1, self.copiedSample)

    @Qt.pyqtSlot(int)
    def upPushButtonClicked(self, sampleID1):

        index1 = self.sampleIDs.index(sampleID1)
        if index1 < 1:
            return

        sampleID2 = self.sampleIDs[index1 - 1]

        self.swapRows(sampleID1, sampleID2)


    @Qt.pyqtSlot(int)
    def downPushButtonClicked(self, sampleID2):

        index2 = self.sampleIDs.index(sampleID2)
        if index2 >= (self.tableWidget.rowCount() - 1):
            return

        sampleID1 = self.sampleIDs[index2 + 1]

        self.swapRows(sampleID1, sampleID2)

    def swapRows(self, sid1, sid2):

        index1 = self.sampleIDs.index(sid1)
        index2 = self.sampleIDs.index(sid2)

        sample1 = self.getSampleRow(index1)
        sample2 = self.getSampleRow(index2)

        self.CBblock = 1    # to protect callbacks from doing things during swapping

        self.removeSampleRow(sid1)
        self.addSampleRow(sample2, index1)

        self.removeSampleRow(sid2)
        self.addSampleRow(sample1, index2)

        self.CBblock = 0


    @Qt.pyqtSlot(int)
    def deletePushButtonClicked(self, sampleID):

        self.removeSampleRow(sampleID)

    def clearConfigurationPushButtonClicked(self):
        if Qt.QMessageBox.question(self, "Warning", "Do you really want to clear the current configuration?", Qt.QMessageBox.Yes, Qt.QMessageBox.No, Qt.QMessageBox.NoButton) == Qt.QMessageBox.Yes:
            self.fileLineEdit.setText("")
            self.clearConfiguration()

    def clearConfiguration(self):
        self.sampleTypeComboBox.setCurrentIndex(0)
        self.storageTemperatureDoubleSpinBox.setValue(0)
        self.optimizationComboBox.setCurrentIndex(0)
        self.extraFlowTimeSpinBox.setValue(0)
        self.initialCleaningCheckBox.setChecked(1)
        self.bufferModeComboBox.setCurrentIndex(0)
        self.copyPushButton.setEnabled(0)
        self.pastePushButton.setEnabled(0)

        self.historyText.clear()

        while self.tableWidget.rowCount() > 0:
            self.tableWidget.removeRow(0)


    def clearHistoryPushButtonClicked(self):
        if Qt.QMessageBox.question(self, "Warning", "Do you really want to clear the current history?", Qt.QMessageBox.Yes, Qt.QMessageBox.No, Qt.QMessageBox.NoButton) == Qt.QMessageBox.Yes:
            self.historyText.clear()

    def closePushButtonClicked(self):
        self.accept()

if __name__ == '__main__':
    import sys
    class Parent:
        pass

    from PyTango import DeviceProxy
    sc = DeviceProxy("nela:20000/bm29/bssc/1")

    app = Qt.QApplication(sys.argv)

    bla = Parent()
    bla._sampleChanger = sc
    bla.nbPlates = 3
    bla.plateInfos = [[8, 12, 12],
                      [8, 12, 0],
                      [4, 11, 3]]

    wid = CollectRobotDialog(bla)
    wid.setWindowTitle('Collect Robot')
    wid.show()

    sys.exit(app.exec_())
