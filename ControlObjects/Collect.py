from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot    
import os
import logging
from XSDataCommon import XSDataString, XSDataImage, XSDataBoolean, \
        XSDataInteger, XSDataDouble, XSDataFile, XSDataStatus, \
        XSDataLength, XSDataWavelength, XSDataDouble
from XSDataBioSaxsv1_0 import XSDataInputBioSaxsProcessOneFilev1_0, \
        XSDataResultBioSaxsProcessOneFilev1_0, XSDataBioSaxsSample, \
        XSDataBioSaxsExperimentSetup, XSDataInputBioSaxsSmartMergev1_0

class Collect(CObjectBase):
    signals = [Signal("collectProcessingDone")]
    slots = [Slot("testCollect"),
             Slot("collect"),
             Slot("collectAbort"),
             Slot("setCheckBeam"),
             Slot("triggerEDNA")]

    def __init__(self, *args, **kwargs):
        CObjectBase.__init__(self, *args, **kwargs)
        self.xsdin = XSDataInputBioSaxsProcessOneFilev1_0(experimentSetup=XSDataBioSaxsExperimentSetup(), sample=XSDataBioSaxsSample())
        self.xsdout = None
        self.ednaJob = None
        self.dat_filenames = {}
        self.pluginIntegrate = "EDPluginBioSaxsProcessOneFilev1_1"
        self.pluginMerge = "EDPluginBioSaxsSmartMergev1_1"

    def __getattr__(self, attr):
        if not attr.startswith("__"):
          try:
             return self.channels[attr]
          except KeyError:
              pass
        raise AttributeError, attr


    def init(self):
        self.collecting = False
        self.channels["jobSuccess"].connect("update", self.processingDone)
        self.commands["initPlugin"](self.pluginIntegrate)
        self.commands["initPlugin"](self.pluginMerge)


    def testCollect(self, pDirectory, pPrefix, pRunNumber, pConcentration, pComments, pCode, pMaskFile, pDetectorDistance, pWaveLength, pPixelSizeX, pPixelSizeY, pBeamCenterX, pBeamCenterY, pNormalisation):
        self.collectDirectory.set_value(pDirectory)
        self.collectPrefix.set_value(pPrefix)
        self.collectRunNumber.set_value(pRunNumber)
        self.collectConcentration.set_value(pConcentration)
        self.collectComments.set_value(pComments)
        self.collectCode.set_value(pCode)
        self.collectMaskFile.set_value(pMaskFile)
        self.collectDetectorDistance.set_value(pDetectorDistance)
        self.collectWaveLength.set_value(pWaveLength)
        self.collectPixelSizeX.set_value(pPixelSizeX)
        self.collectPixelSizeY.set_value(pPixelSizeY)        
        self.collectBeamCenterX.set_value(pBeamCenterX)
        self.collectBeamCenterY.set_value(pBeamCenterY)
        self.collectNormalisation.set_value(pNormalisation)                       
        self.commands["testCollect"]()

    def collect(self, pDirectory, pPrefix, pRunNumber, pNumberFrames, pTimePerFrame, pConcentration, pComments, pCode, pMaskFile, pDetectorDistance, pWaveLength, pPixelSizeX, pPixelSizeY, pBeamCenterX, pBeamCenterY, pNormalisation, pRadiationChecked, pRadiationAbsolute, pRadiationRelative, pProcessData, pSEUTemperature, pStorageTemperature):
        self.collecting = True
        self.collectDirectory.set_value(pDirectory)
        self.collectPrefix.set_value(pPrefix)
        self.collectRunNumber.set_value(pRunNumber)
        self.collectNumberFrames.set_value(pNumberFrames)
        self.collectTimePerFrame.set_value(pTimePerFrame)
        self.collectConcentration.set_value(pConcentration)
        self.collectComments.set_value(pComments)
        self.collectCode.set_value(pCode)
        self.collectMaskFile.set_value(pMaskFile)
        self.collectDetectorDistance.set_value(pDetectorDistance)
        self.collectWaveLength.set_value(pWaveLength)
        self.collectPixelSizeX.set_value(pPixelSizeX)
        self.collectPixelSizeY.set_value(pPixelSizeY)        
        self.collectBeamCenterX.set_value(pBeamCenterX)
        self.collectBeamCenterY.set_value(pBeamCenterY)
        self.collectNormalisation.set_value(pNormalisation)
        self.collectProcessData.set_value(pProcessData)                  

        #Prepare EDNA input
        self.xsdin.sample.concentration = XSDataDouble(float(pConcentration))
        self.xsdin.sample.code = XSDataString(str(pCode))
        self.xsdin.sample.comments = XSDataString(str(pComments))
       
        xsdExperiment = self.xsdin.experimentSetup
        xsdExperiment.detector = XSDataString("Pilatus")                    #Hardcoded for Pilatus
        xsdExperiment.detectorDistance = XSDataLength(value=float(pDetectorDistance))  
        xsdExperiment.pixelSize_1 = XSDataLength(value=float(pPixelSizeX)*1.0e-6)  
        xsdExperiment.pixelSize_2 = XSDataLength(value=float(pPixelSizeY)*1.0e-6)  
        xsdExperiment.beamCenter_1 = XSDataDouble(float(pBeamCenterX))
        xsdExperiment.beamCenter_2 = XSDataDouble(float(pBeamCenterY))
        xsdExperiment.wavelength = XSDataWavelength(float(pWaveLength)*1.0e-9)     
        xsdExperiment.maskFile = XSDataImage(path=XSDataString(str(pMaskFile)))
        xsdExperiment.normalizationFactor = XSDataDouble(float(pNormalisation))
        xsdExperiment.storageTemperature = XSDataDouble(pStorageTemperature)
        xsdExperiment.exposureTemperature = XSDataDouble(pSEUTemperature)
        #xsdExperiment.exposureTime = XSDataTime()
        #xsdExperiment.frameNumber = XSDataInteger()
        #xsdExperiment.frameMax = XSDataInteger()
        
        sPrefix=str(pPrefix)
        ave_filename = os.path.join(pDirectory,"1d", "%s_%03d_ave.dat" % (sPrefix, pRunNumber))
        self.xsdAverage = XSDataInputBioSaxsSmartMergev1_0(\
                                inputCurves= [XSDataFile(path=XSDataString(os.path.join(pDirectory,"1d", "%s_%03d_%02d.dat" % (sPrefix, pRunNumber, i)))) for i in range(1, pNumberFrames+1)],
                                mergedCurve= XSDataFile(path=XSDataString(ave_filename)))
        
        if pRadiationChecked:
            self.xsdAverage.absoluteFidelity = XSDataDouble(float(pRadiationAbsolute))
            self.xsdAverage.relativeFidelity = XSDataDouble(float(pRadiationRelative))
        #logging.warning("DEBUG 3 %s %s %s %s %s",pRadiationChecked,pRadiationAbsolute,pRadiationRelative,pSEUTemperature,pStorageTemperature)
                                
        self.xsdin.rawImageSize = XSDataInteger(4093756)                     #Hardcoded for Pilatus
        self.commands["collect"](callback=self.collectDone, error_callback=self.collectFailed)

    def triggerEDNA(self, raw_filename):
        raw_filename=str(raw_filename)
        self.xsdin.rawImage = XSDataImage(path=XSDataString(raw_filename))
        self.xsdin.experimentSetup.beamStopDiode = XSDataDouble(float(self.channels["collectBeamStopDiode"].value())) 
        self.xsdin.experimentSetup.machineCurrent = XSDataDouble(float(self.channels["machine_current"].value()))
        self.xsdin.logFile = XSDataFile(path=XSDataString(raw_filename.replace("/raw/", "/misc/").replace(".edf", ".log")))
        self.xsdin.normalizedImage = XSDataImage(path=XSDataString(raw_filename.replace("/raw/", "/2d/")))
        self.xsdin.integratedImage = XSDataImage(path=XSDataString(raw_filename.replace("/raw/", "/misc/").replace(".edf", ".ang")))
        self.xsdin.integratedCurve=XSDataFile(path=XSDataString(raw_filename.replace("/raw/", "/1d/").replace(".edf", ".dat")))
        #For debugging
        #open("/tmp/ednaTrigger.log","a").write(self.xsdin.marshal() )
            
        jobId = self.commands["startJob"]([self.pluginIntegrate,self.xsdin.marshal()])
        self.dat_filenames[jobId] = self.xsdin.integratedCurve.path.value
        logging.info("Processing job %s started", jobId)
        
    def collectDone(self, returned_value):
        self.collecting = False
        
        # start EDNA to calculate average at the end
        jobId = self.commands["startJob"]([self.pluginMerge,self.xsdAverage.marshal()])
        self.dat_filenames[jobId]=self.xsdAverage.mergedCurve.path.value

    def processingDone(self, jobId):
        if jobId in self.dat_filenames:
          self.emit("collectProcessingDone", self.dat_filenames[jobId])
          del self.dat_filenames[jobId]

    def collectFailed(self):
        self.collecting = False

    def collectAbort(self):
        logging.info("sending abort to stop spec collection")
        self.abortCollect.set_value(1)

        #self.commands["collect"].abort()

    def testCollectAbort(self):
        logging.info("sending abort to stop spec test collection")
        self.abortCollect.set_value(1)

        #self.commands["testCollect"].abort()

    def setCheckBeam(self, flag):
        logging.info("changing check beam in spec to %s" % flag) 
        if flag:
            self.channels["checkBeam"].set_value(1)
        else:
            self.channels["checkBeam"].set_value(0)

    # overwrite connectNotify ; first values will be read by brick
    def connectNotify(self, signal_name):
        pass

    def updateChannels(self):
        for channel_name, channel in self.channels.iteritems():
            if channel_name == "jobSuccess":
                continue
            channel.update(channel.value())
