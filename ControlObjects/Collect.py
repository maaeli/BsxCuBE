from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot    
import os
import logging
from XSDataCommon import XSDataString, XSDataImage, XSDataBoolean, \
        XSDataInteger, XSDataDouble, XSDataFile, XSDataStatus, \
        XSDataLength, XSDataWavelength, XSDataDouble, XSDataTime
from XSDataBioSaxsv1_0 import XSDataInputBioSaxsProcessOneFilev1_0, \
        XSDataResultBioSaxsProcessOneFilev1_0, XSDataBioSaxsSample, \
        XSDataBioSaxsExperimentSetup, XSDataInputBioSaxsSmartMergev1_0, XSDataResultBioSaxsSmartMergev1_0

class Collect(CObjectBase):
    signals = [Signal("collectProcessingDone"),
               Signal("collectProcessingLog")]
    slots = [Slot("testCollect"),
             Slot("collect"),
             Slot("collectAbort"),
             Slot("setCheckBeam"),
             Slot("triggerEDNA")]

    def __init__(self, *args, **kwargs):
        CObjectBase.__init__(self, *args, **kwargs)
        self.xsdin = XSDataInputBioSaxsProcessOneFilev1_0(experimentSetup=XSDataBioSaxsExperimentSetup(), sample=XSDataBioSaxsSample())
        self.xsdin.rawImageSize = XSDataInteger(4093756)                     #Hardcoded for Pilatus
        self.xsdout = None
        self.ednaJob = None
        self.dat_filenames = {}
        self.pluginIntegrate = "EDPluginBioSaxsProcessOneFilev1_1"
        self.pluginMerge = "EDPluginBioSaxsSmartMergev1_3"
        self.storageTemperature = -374
        self.exposureTemperature = -374
        self.xsdAverage_chris = None
        #self.xsdAverage_slavia = None

    def __getattr__(self, attr):
        if not attr.startswith("__"):
          try:
             return self.channels[attr]
          except KeyError:
              pass
        raise AttributeError, attr


    def init(self):
        self.collecting = False
        #self.channels["jobSuccess_chris"].connect("update", self.processingDone)
        self.channels["jobSuccess"].connect("update", self.processingDone)
        #self.commands["initPlugin_chris"](self.pluginIntegrate)
        #self.commands["initPlugin_chris"](self.pluginMerge)
        self.commands["initPlugin_slavia"](self.pluginIntegrate)
        self.commands["initPlugin_slavia"](self.pluginMerge)


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
        self.storageTemperature = float(pStorageTemperature)
        self.exposureTemperature = float(pSEUTemperature)
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
        xsdExperiment.frameMax = XSDataInteger(int(pNumberFrames))
        xsdExperiment.exposureTime = XSDataTime(float(pTimePerFrame))
        
        sPrefix=str(pPrefix)
        ave_filename = os.path.join(pDirectory,"1d", "%s_%03d_ave.dat" % (sPrefix, pRunNumber))
        sub_filename = os.path.join(pDirectory,"ednaSub", "%s_%03d_sub.dat" % (sPrefix, pRunNumber))
        self.xsdAverage_chris = XSDataInputBioSaxsSmartMergev1_0(\
                                inputCurves= [XSDataFile(path=XSDataString(os.path.join(pDirectory,"1d", "%s_%03d_%02d.dat" % (sPrefix, pRunNumber, i)))) for i in range(1, pNumberFrames+1)],
                                mergedCurve=XSDataFile(path=XSDataString(ave_filename)),
                                subtractedCurve=XSDataFile(path=XSDataString(sub_filename)))
        #for local processing
        #pDirectory = pDirectory.replace("/data/","/data_local",1)
        #ave_filename = os.path.join(pDirectory,"1d", "%s_%03d_ave.dat" % (sPrefix, pRunNumber))
        #sub_filename = os.path.join(pDirectory,"ednaSub", "%s_%03d_sub.dat" % (sPrefix, pRunNumber))
        # 
        #self.xsdAverage_slavia = XSDataInputBioSaxsSmartMergev1_0(\
        #                        inputCurves= [XSDataFile(path=XSDataString(os.path.join(pDirectory,"1d", "%s_%03d_%02d.dat" % (sPrefix, pRunNumber, i)))) for i in range(1, pNumberFrames+1)],
        #                        mergedCurve=XSDataFile(path=XSDataString(ave_filename)),
        #                        subtractedCurve=XSDataFile(path=XSDataString(sub_filename)))
        if pRadiationChecked:
            self.xsdAverage_chris.absoluteFidelity = XSDataDouble(float(pRadiationAbsolute))
            self.xsdAverage_chris.relativeFidelity = XSDataDouble(float(pRadiationRelative))
        #    self.xsdAverage_slavia.absoluteFidelity = XSDataDouble(float(pRadiationAbsolute))
        #    self.xsdAverage_slavia.relativeFidelity = XSDataDouble(float(pRadiationRelative))
        self.commands["collect"](callback=self.collectDone, error_callback=self.collectFailed)


    def triggerEDNA(self, raw_filename):
        raw_filename=str(raw_filename)
        tmp, suffix = os.path.splitext(raw_filename)
        tmp, base = os.path.split(tmp)
        directory, local = os.path.split(tmp) 
        frame = ""
        for c in base[-1::-1]:
            if c.isdigit():
                frame=c+frame
            else:
                break
        
        self.xsdin.experimentSetup.storageTemperature = XSDataDouble(self.storageTemperature)
        self.xsdin.experimentSetup.exposureTemperature = XSDataDouble(self.exposureTemperature)
        self.xsdin.experimentSetup.frameNumber = XSDataInteger(int(frame))
        self.xsdin.experimentSetup.beamStopDiode = XSDataDouble(float(self.channels["collectBeamStopDiode"].value())) 
        self.xsdin.experimentSetup.machineCurrent = XSDataDouble(float(self.channels["machine_current"].value()))
        xsdin_chris = self.xsdin.copy()
        #xsdin_slavia = self.xsdin.copy()
        
        xsdin_chris.rawImage = XSDataImage(path=XSDataString(raw_filename))
        xsdin_chris.logFile = XSDataFile(path=XSDataString(os.path.join(directory, "misc", base+".log")))
        xsdin_chris.normalizedImage = XSDataImage(path=XSDataString(os.path.join(directory, "2d", base+".edf")))
        xsdin_chris.integratedImage = XSDataImage(path=XSDataString(os.path.join(directory, "misc", base+".ang")))
        xsdin_chris.integratedCurve = XSDataFile(path=XSDataString(os.path.join(directory, "1d", base+".dat")))

        #directory = directory.replace("/data/","/data_local/",1)
        #xsdin_slavia.rawImage = XSDataImage(path=XSDataString(os.path.join(directory, "raw",base+".edf")))
        #xsdin_slavia.logFile = XSDataFile(path=XSDataString(os.path.join(directory, "misc", base+".log")))
        #xsdin_slavia.normalizedImage = XSDataImage(path=XSDataString(os.path.join(directory, "2d", base+".edf")))
        #xsdin_slavia.integratedImage = XSDataImage(path=XSDataString(os.path.join(directory, "misc", base+".ang")))
        #xsdin_slavia.integratedCurve = XSDataFile(path=XSDataString(os.path.join(directory, "1d", base+".dat")))

        xsd_marsh = xsdin_chris.marshal()    
        jobId = self.commands["startJob_slavia"]([self.pluginIntegrate,xsd_marsh])
        #jobId = self.commands["startJob_chris"]([self.pluginIntegrate,xsdin_chris.marshal()])
        #jobId2 = self.commands["startJob_slavia"]([self.pluginIntegrate,xsdin_slavia.marshal()])
        self.dat_filenames[jobId] = xsdin_chris.integratedCurve.path.value
        logging.info("Processing job %s started", jobId)
        #For debugging
        with open(raw_filename.replace(".edf",".xml"),"a") as xmlFile:
            xmlFile.write(xsd_marsh)
        
    def collectDone(self, returned_value):
        self.collecting = False
        # start EDNA to calculate average at the end
        jobId = self.commands["startJob_slavia"]([self.pluginMerge,self.xsdAverage_chris.marshal()])
        #jobId = self.commands["startJob_chris"]([self.pluginMerge,self.xsdAverage_chris.marshal()])
        self.dat_filenames[jobId]=self.xsdAverage_chris.mergedCurve.path.value

        
    def processingDone(self, jobId):
        if jobId in self.dat_filenames:
            filename = self.dat_filenames.pop(jobId)
            logging.info("processing Done from EDNA: %s -> %s",jobId, filename)
            self.emit("collectProcessingDone", filename)
            if jobId.startswith(self.pluginMerge):
                strXsdout = self.commands["getJobOutput_slavia"](jobId)
                #strXsdout = self.commands["getJobOutput_chris"](jobId)
                try: 
                    xsd = XSDataResultBioSaxsSmartMergev1_0.parseString(strXsdout)
                except:
                    logging.error("Unable to parse string from Tango/EDNA")
                else:
                    log = xsd.status.executiveSummary.value
                    logging.info(log)
                    self.emit("collectProcessingLog", log)
        else:
            logging.warning("processing Done from EDNA: %s -X-> None",jobId)

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
            if channel_name.startswith("jobSuccess"):
                continue
            channel.update(channel.value())
