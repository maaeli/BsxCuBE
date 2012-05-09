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
        for channel in self.__CHANNEL_LIST:
            try:
                value = self.channels.get(channel[:-7])
                setattr(self, channel[:-7], value)
                if value is not None:
                    getattr(self, channel[:-7]).connect("update", getattr(self, channel))
            except:
                pass

    def reprocess(self, pDirectory, pPrefix, pRunNumber, pFrameFirst, pFrameLast, pConcentration, pComments, pCode, pMaskFile, pDetectorDistance, pWaveLength, pPixelSizeX, pPixelSizeY, pBeamCenterX, pBeamCenterY, pNormalisation, pBeamStopDiode, pMachineCurrent, pKeepOriginal, pTimeOut, pFeedback):
        # Fixed since 2011
        self.reprocessDetector.set_value("Pilatus")
        # Fixed by SO 5/9 2012
        self.reprocessOperation.set_value("Complete reprocess")
        self.reprocessDirectory.set_value(pDirectory)
        self.reprocessPrefix.set_value(pPrefix)
        self.reprocessRunNumber.set_value(pRunNumber)

        if pFrameFirst is None:
            frameFirst = ""
        else:
            frameFirst = pFrameFirst
        self.reprocessFrameFirst.set_value(frameFirst)

        if pFrameLast is None:
            frameLast = ""
        else:
            frameLast = pFrameLast
        self.reprocessFrameLast.set_value(frameLast)

        if pConcentration is not None:
            concentration = str(pConcentration)
            self.reprocessConcentration.set_value(concentration)
        else:
            concentration = ""

        if pComments is not None:
            comments = str(pComments)
            self.reprocessComments.set_value(comments)
        else:
            comments = ""

        if pCode is not None:
            code = str(pCode)
            self.reprocessCode.set_value(code)
        else:
            code = ""

        if pMaskFile is not None:
            maskFile = str(pMaskFile)
            self.reprocessMaskFile.set_value(maskFile)
        else:
            maskFile = ""

        if pDetectorDistance is not None:
            detectorDistance = str(pDetectorDistance)
            self.reprocessDetector.set_value(detectorDistance)
        else:
            detectorDistance = ""

        if pWaveLength is not None:
            waveLength = str(pWaveLength)
            self.reprocessWaveLength.set_value(waveLength)
        else:
            waveLength = ""

        if pPixelSizeX is not None:
            pixelSizeX = str(pPixelSizeX)
            self.reprocessPixelSizeX.set_value(pixelSizeX)
        else:
            pixelSizeX = ""

        if pPixelSizeY is not None:
            pixelSizeY = str(pPixelSizeY)
            self.reprocessPixelSizeY.set_value(pPixelSizeY)
        else:
            pixelSizeY = ""

        if pBeamCenterX is not None:
            beamCenterX = str(pBeamCenterX)
            self.reprocessBeamCenterX.set_value(beamCenterX)
        else:
            beamCenterX = ""

        if pBeamCenterY is not None:
            beamCenterY = str(pBeamCenterY)
            self.reprocessBeamCenterY.set_value(beamCenterY)
        else:
            beamCenterY = ""

        if pNormalisation is not None:
            normalisation = str(pNormalisation)
            self.reprocessNormalisation.set_value(normalisation)
        else:
            normalisation = ""

        if pBeamStopDiode is not None:
            beamStopDiode = str(pBeamStopDiode)
            self.reprocessBeamStopDiode.set_value(beamStopDiode)
        else:
            beamStopDiode = ""

        if pMachineCurrent is not None:
            machineCurrent = str(pMachineCurrent)
            self.reprocessMachineCurrent.set_value(machineCurrent)
        else:
            machineCurrent = ""

        self.reprocessKeepOriginal.set_value(pKeepOriginal)

        self.commands["reprocess"](str(pDirectory),
                                   str(pPrefix),
                                   pRunNumber,
                                   frameFirst,
                                   frameLast,
                                   concentration,
                                   comments,
                                   code,
                                   maskFile,
                                   detectorDistance,
                                   waveLength,
                                   pixelSizeX,
                                   pixelSizeY,
                                   beamCenterX,
                                   beamCenterY,
                                   normalisation,
                                   beamStopDiode,
                                   machineCurrent,
                                   pKeepOriginal,
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
