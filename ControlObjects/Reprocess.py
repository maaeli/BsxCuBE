from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot

class Reprocess(CObjectBase):
    __CHANNEL_LIST = ["reprocessDirectoryChanged",
                      "reprocessPrefixChanged",
                      "reprocessRunNumberChanged",
                      "reprocessFrameFirstChanged",
                      "reprocessFrameLastChanged",
                      "reprocessConcentrationChanged",
                      "reprocessCommentsChanged",
                      "reprocessCodeChanged",
                      "reprocessMaskFileChanged",
                      "reprocessDetectorDistanceChanged",
                      "reprocessWaveLengthChanged",
                      "reprocessPixelSizeXChanged",
                      "reprocessPixelSizeYChanged",
                      "reprocessBeamCenterXChanged",
                      "reprocessBeamCenterYChanged",
                      "reprocessNormalisationChanged",
                      "reprocessBeamStopDiodeChanged",
                      "reprocessMachineCurrentChanged",
                      "reprocessKeepOriginalChanged",
                      "reprocessStatusChanged"]

    signals = [Signal(channel) for channel in __CHANNEL_LIST]
    slots = [Slot("reprocess")]

    def __init__(self, *args, **kwargs):
        CObjectBase.__init__(self, *args, **kwargs)

    def init(self):
        self.frameFirst = ""
        self.frameLast = ""
        self.concentration = ""
        self.comment = ""
        self.code = ""
        self.maskFile = ""
        self.detectorDistance = ""
        self.waveLength = ""
        self.pixelSizeX = ""
        self.pixelSizeY = ""
        self.beamCenterX = ""
        self.beamCenterY = ""
        self.normalisation = ""
        self.beamStopDiode = ""
        self.machineCurrent = ""

    def reprocess(self, pDirectory, pPrefix, pRunNumber, pFrameFirst, pFrameLast, pConcentration, pComments, pCode, pMaskFile, pDetectorDistance, pWaveLength, pPixelSizeX, pPixelSizeY, pBeamCenterX, pBeamCenterY, pNormalisation, pBeamStopDiode, pMachineCurrent, pKeepOriginal, pTimeOut, pFeedback):
        # Fixed since 2011
        self.detector = "Pilatus"
        # Fixed by SO 5/9 2012
        self.operation = "Complete reprocess"
        self.directory = pDirectory
        self.prefix = pPrefix
        self.runNumber = pRunNumber

        if pFrameFirst is None:
            self.frameFirst = pFrameFirst

        if pFrameLast is None:
            self.frameLast = pFrameLast

        if pConcentration is not None:
            self.concentration = pConcentration

        if pComments is not None:
            self.comments = pComments

        if pCode is not None:
            self.code = pCode

        if pMaskFile is not None:
            self.maskFile = pMaskFile

        if pDetectorDistance is not None:
            self.detectorDistance = pDetectorDistance

        if pWaveLength is not None:
            self.waveLength = pWaveLength

        if pPixelSizeX is not None:
            self.pixelSizeX = pPixelSizeX

        if pPixelSizeY is not None:
            self.pixelSizeY = pPixelSizeY

        if pBeamCenterX is not None:
            self.beamCenterX = pBeamCenterX

        if pBeamCenterY is not None:
            self.beamCenterY = pBeamCenterY

        if pNormalisation is not None:
            self.normalisation = pNormalisation

        if pBeamStopDiode is not None:
            self.beamStopDiode = pBeamStopDiode

        if pMachineCurrent is not None:
            self.machineCurrent = pMachineCurrent

        self.keepOriginal = pKeepOriginal

        self.commands["reprocess"](self.directory,
                                   self.prefix,
                                   self.runNumber,
                                   self.frameFirst,
                                   self.frameLast,
                                   self.concentration,
                                   self.comments,
                                   self.code,
                                   self.maskFile,
                                   self.detectorDistance,
                                   self.waveLength,
                                   self.pixelSizeX,
                                   self.pixelSizeY,
                                   self.beamCenterX,
                                   self.beamCenterY,
                                   self.normalisation,
                                   self.beamStopDiode,
                                   self.machineCurrent,
                                   self.keepOriginal,
                                   pTimeOut,
                                   pFeedback)


    def reprocessAbort(self):
        self.commands["reprocess"].abort()

    def reprocessDirectoryChanged(self, pValue):
        self.emit("reprocessDirectoryChanged", pValue)

    def reprocessPrefixChanged(self, pValue):
        self.emit("reprocessPrefixChanged", pValue)

    def reprocessRunNumberChanged(self, pValue):
        self.emit("reprocessRunNumberChanged", pValue)

    def reprocessFrameFirstChanged(self, pValue):
        self.emit("reprocessFrameFirstChanged", pValue)

    def reprocessFrameLastChanged(self, pValue):
        self.emit("reprocessFrameLastChanged", pValue)

    def reprocessConcentrationChanged(self, pValue):
        self.emit("reprocessConcentrationChanged", pValue)

    def reprocessCommentsChanged(self, pValue):
        self.emit("reprocessCommentsChanged", pValue)

    def reprocessCodeChanged(self, pValue):
        self.emit("reprocessCodeChanged", pValue)

    def reprocessMaskFileChanged(self, pValue):
        self.emit("reprocessMaskFileChanged", pValue)

    def reprocessDetectorDistanceChanged(self, pValue):
        self.emit("reprocessDetectorDistanceChanged", pValue)

    def reprocessWaveLengthChanged(self, pValue):
        self.emit("reprocessWaveLengthChanged", pValue)

    def reprocessPixelSizeXChanged(self, pValue):
        self.emit("reprocessPixelSizeXChanged", pValue)

    def reprocessPixelSizeYChanged(self, pValue):
        self.emit("reprocessPixelSizeYChanged", pValue)

    def reprocessBeamCenterXChanged(self, pValue):
        self.emit("reprocessBeamCenterXChanged", pValue)

    def reprocessBeamCenterYChanged(self, pValue):
        self.emit("reprocessBeamCenterYChanged", pValue)

    def reprocessNormalisationChanged(self, pValue):
        self.emit("reprocessNormalisationChanged", pValue)

    def reprocessBeamStopDiodeChanged(self, pValue):
        self.emit("reprocessBeamStopDiodeChanged", pValue)

    def reprocessMachineCurrentChanged(self, pValue):
        self.emit("reprocessMachineCurrentChanged", pValue)

    def reprocessKeepOriginalChanged(self, pValue):
        self.emit("reprocessKeepOriginalChanged", pValue)

    def reprocessStatusChanged(self, pValue):
        self.emit("reprocessStatusChanged", pValue)
