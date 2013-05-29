from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot
import os
import logging
import numpy
import time
import gevent
import math
import pprint
import datetime
import re
import sys
import traceback
from XSDataCommon import XSDataString, XSDataImage, XSDataBoolean, \
        XSDataInteger, XSDataDouble, XSDataFile, XSDataStatus, \
        XSDataLength, XSDataWavelength, XSDataDouble, XSDataTime
from XSDataBioSaxsv1_0 import XSDataInputBioSaxsProcessOneFilev1_0, \
        XSDataResultBioSaxsProcessOneFilev1_0, XSDataBioSaxsSample, \
        XSDataBioSaxsExperimentSetup, XSDataInputBioSaxsSmartMergev1_0, \
        XSDataResultBioSaxsSmartMergev1_0, XSDataInputBioSaxsToSASv1_0, \
        XSDataResultBioSaxsToSASv1_0, XSDataResultBioSaxsHPLCv1_0, \
        XSDataInputBioSaxsHPLCv1_0
#from XSDataSAS import XSDataInputSolutionScattering



logger = logging.getLogger( "Collect" )
class Collect( CObjectBase ):
    signals = [Signal( "collectBeamStopDiodeChanged" ),
               Signal( "collectDirectoryChanged" ),
               Signal( "collectRobotFileChanged" ),
               Signal( "collectPrefixChanged" ),
               Signal( "collectRunNumberChanged" ),
               Signal( "collectNumberFramesChanged" ),
               Signal( "collectTimePerFrameChanged" ),
               Signal( "collectConcentrationChanged" ),
               Signal( "collectCommentsChanged" ),
               Signal( "collectCodeChanged" ),
               Signal( "collectMaskFileChanged" ),
               Signal( "collectDetectorDistanceChanged" ),
               Signal( "collectWaveLengthChanged" ),
               Signal( "collectPixelSizeXChanged" ),
               Signal( "collectPixelSizeYChanged" ),
               Signal( "collectBeamCenterXChanged" ),
               Signal( "collectBeamCenterYChanged" ),
               Signal( "collectNormalisationChanged" ),
               Signal( "collectRadiationDamageChanged" ),
               Signal( "collectRelativeRadiationDamageChanged" ),
               Signal( "collectAbsoluteRadiationDamageChanged" ),
               Signal( "collectNewFrameChanged" ),
               Signal( "checkBeamChanged" ),
               Signal( "beamLostChanged" ),
               Signal( "collectProcessingDone" ),
               Signal( "collectProcessingLog" ),
               Signal( "collectDone" ),
               Signal( "clearCurve" ),
               Signal( "transmissionChanged" ),
               Signal( "machineCurrentChanged" ),
               Signal( "newSASUrl" )]
    slots = [Slot( "testCollect" ),
             Slot( "collect" ),
             Slot( "collectAbort" ),
             Slot( "setCheckBeam" ),
             Slot( "triggerEDNA" ),
             Slot( "blockEnergyAdjust" )
             ]

    def __init__( self, *args, **kwargs ):
        # username and password from login Brick
        self.__username = None
        self.__password = None

        #
        # HPCL or not
        self.isHPLC = False

        # ----------------------------
        # ISPyB Parameters
        self.isISPyB = False
        # Incremental number of the data collection ([0, 1, 2],[0,1,2] ... ) = [Buffer, Sample, Buffer][Buffer, Sample, Buffer] 
        self.dataCollectionOrder = 0
        #Measurement Id of the sample
        self.measurementId = None
        # ----------------------------


        CObjectBase.__init__( self, *args, **kwargs )
        self.__collectWithRobotProcedure = None
        self.xsdin = XSDataInputBioSaxsProcessOneFilev1_0( experimentSetup = XSDataBioSaxsExperimentSetup(), sample = XSDataBioSaxsSample() )
        self.xsdin_HPLC = XSDataInputBioSaxsHPLCv1_0( experimentSetup = XSDataBioSaxsExperimentSetup(), sample = XSDataBioSaxsSample() )
        self.xsdin.rawImageSize = XSDataInteger( 4093756 )                     #Hardcoded for Pilatus
        self.xsdout = None
        self.lastPrefixRun = None
        self.ednaJob = None
        self.dat_filenames = {}
        self.jobSubmitted = False
        self.pluginIntegrate = "EDPluginBioSaxsProcessOneFilev1_3"
        self.pluginMerge = "EDPluginBioSaxsSmartMergev1_5"
        self.pluginSAS = "EDPluginBioSaxsToSASv1_0"
        self.pluginHPLC = "EDPluginBioSaxsHPLCv1_0"
        self.pluginFlushHPLC = "EDPluginBioSaxsFlushHPLCv1_0"

        self.storageTemperature = -374
        self.exposureTemperature = -374
        self.xsdAverage = None
        # The keV to Angstrom calc
        self.hcOverE = 12.3984

        self.__energyAdjust = False


        # get machdevice from config file
        # <data name="uri"  value="orion:10000/FE/D/29" />
        self.machDevName = str( self.config["/object/data[@name='uri']/@value"][0] )

    def __getattr__( self, attr ):
        if not attr.startswith( "__" ):
            try:
                return self.channels[attr]
            except KeyError:
                pass
        raise AttributeError, attr

    def init( self ):
        self.edna1Dead = None
        self.edna2Dead = None
        self.collecting = False
        self.machineCurrent = 0.00
        self.nextRunNumber = -1
        self.deltaPilatus = 0.1

        self.channels["collectNewFrame"].connect( "update", self.collectNewFrameChanged )

        try:
            self.channels["jobSuccess_edna1"].connect( "update", self.processingDone )
            self.channels["jobFailure_edna1"].connect( "update", self.processingFailed )
            self.commands["initPlugin_edna1"]( self.pluginSAS )
            self.commands["initPlugin_edna1"]( self.pluginHPLC )
            self.edna1Dead = False
        except Exception:
            self.showMessageEdnaDead( 1 )

        try:
            self.channels["jobSuccess_edna2"].connect( "update", self.processingDone )
            self.channels["jobFailure_edna2"].connect( "update", self.processingFailed )
            self.commands["initPlugin_edna2"]( self.pluginIntegrate )
            self.commands["initPlugin_edna2"]( self.pluginMerge )

            self.edna2Dead = False
        except Exception:
            self.showMessageEdnaDead( 2 )
        # add a channel to read machine current (with polling)
        self.addChannel( 'tango',
                        'read_current_value',
                        self.machDevName,
                        'SR_Current',
                        polling = 3000 )
        # set up a connect to the Tango channel
        readMachCurrentValue = self.channels.get( 'read_current_value' )
        if readMachCurrentValue is not None:
            readMachCurrentValue.connect( 'update', self.currentChanged )
        # set up channels
        self.channels["collectRunNumber"].connect( "update", self.runNumberChanged )
        self.channels["checkBeam"].connect( "update", self.checkBeamChanged )

    def tangoErrMsgExtractDesc( self, errMsg ):
        pprint.pprint( errMsg )
        # try to see if it is a Tango message first
        tempList = str( errMsg ).split( "\n" )
        if re.match( ".*: an error occurred when calling Tango command .*", tempList[0] ):
            # Now let us check for first desc and do return on that
            message = "Unknown Error"
            for item in tempList:
                if re.match( ".* desc = .*", item ):
                    message = item[11:]
                    return message
            return message
        else:
            return None

    def showMessageEdnaDead( self, _ednaServerNumber ):
        if _ednaServerNumber == 1:
            if self.edna1Dead:
                return
            self.edna1Dead = True
        elif _ednaServerNumber == 2:
            if self.edna2Dead:
                return
            self.edna2Dead = True
        else:
            self.showMessage( 2, "ERROR! No such EDNA server: %d" % _ednaServerNumber )
        message = "Unable to connect to EDNA %d" % _ednaServerNumber
        logger.error( message )
        message = "EDNA server %d is dead, please restart EDNA %d" % ( _ednaServerNumber, _ednaServerNumber )
        self.showMessage( 2, message, notify = 1 )
        message = "ENDA %d is dead" % _ednaServerNumber
        logger.error( message )


    def currentChanged( self, current ):
        self.machineCurrent = current
        # Give this to the CollectBrick
        self.emit( "machineCurrentChanged", current )

    def getTemplateDirectory( self ):
        # get Template directory
        return str ( self.config["/object/data[@name='templateDirectory']/@value"][0] )

    def sasWebDisplay( self, url ):
        #TODO:DEBUG
        print "-In sasWebDisplay - received %s " % url
        self.emit( "newSASUrl", url )

    def putUserInfo( self, username, password ):
        self.__username = username
        self.__password = password

    def blockEnergyAdjust( self, pValue ):
        # True or false for following energy with Pilatus
        self.__energyAdjust = pValue

    def runNumberChanged( self, runNumber ):
        # set new run number from Spec - Convert it to int
        self.nextRunNumber = int( runNumber )

    def checkBeamChanged( self, pValue ):
        # new value for Checkbeam - send to Brick
        self.emit( "checkBeamChanged", pValue )

    def prepareEdnaInput( self, pConcentration, pComments, pCode, pMaskFile, pDetectorDistance, pWaveLength, pPixelSizeX, pPixelSizeY, pBeamCenterX, pBeamCenterY, pNormalisation, pNumberFrames, pTimePerFrame ):
        # fill up self.xsdinXSDataInputBioSaxsProcessOneFilev1_0
        logger.info( "Prepare EDNA input" )
        sample = self.xsdin.sample
        sample.concentration = XSDataDouble( float( pConcentration ) )
        sample.code = XSDataString( str( pCode ) )
        sample.comments = XSDataString( str( pComments ) )

        xsdExperiment = self.xsdin.experimentSetup
        xsdExperiment.detector = XSDataString( "Pilatus" )                    #Hardcoded for Pilatus
        xsdExperiment.detectorDistance = XSDataLength( value = float( pDetectorDistance ) )
        xsdExperiment.pixelSize_1 = XSDataLength( value = float( pPixelSizeX ) * 1.0e-6 )
        xsdExperiment.pixelSize_2 = XSDataLength( value = float( pPixelSizeY ) * 1.0e-6 )
        xsdExperiment.beamCenter_1 = XSDataDouble( float( pBeamCenterX ) )
        xsdExperiment.beamCenter_2 = XSDataDouble( float( pBeamCenterY ) )
        xsdExperiment.wavelength = XSDataWavelength( float( pWaveLength ) * 1.0e-10 )
        xsdExperiment.maskFile = XSDataImage( path = XSDataString( str( pMaskFile ) ) )
        xsdExperiment.normalizationFactor = XSDataDouble( float( pNormalisation ) )
        xsdExperiment.frameMax = XSDataInteger( int( pNumberFrames ) )
        xsdExperiment.exposureTime = XSDataTime( float( pTimePerFrame ) )

        self.xsdin_HPLC.sample = sample
        self.xsdin_HPLC.experimentSetup = xsdExperiment

    def testCollect( self, pDirectory, pPrefix, pRunNumber, pConcentration, pComments, pCode, pMaskFile, pDetectorDistance, pWaveLength, pPixelSizeX, pPixelSizeY, pBeamCenterX, pBeamCenterY, pNormalisation ):
        self.collectDirectory.set_value( pDirectory )
        self.collectPrefix.set_value( pPrefix )
        self.collectRunNumber.set_value( pRunNumber )
        self.collectConcentration.set_value( pConcentration )
        self.collectComments.set_value( pComments )
        self.collectCode.set_value( pCode )
        self.collectMaskFile.set_value( pMaskFile )
        self.collectDetectorDistance.set_value( pDetectorDistance )
        self.collectWaveLength.set_value( pWaveLength )
        self.collectPixelSizeX.set_value( pPixelSizeX )
        self.collectPixelSizeY.set_value( pPixelSizeY )
        self.collectBeamCenterX.set_value( pBeamCenterX )
        self.collectBeamCenterY.set_value( pBeamCenterY )
        self.collectNormalisation.set_value( pNormalisation )
        # note that pTimePerFrame is 1.0 s and number of frames is 1
        #pNumberFrames = 1
        #pTimePerFrame = 1.0
        #self.prepareEdnaInput( pConcentration, pComments, pCode, pMaskFile, pDetectorDistance, pWaveLength, pPixelSizeX, pPixelSizeY, pBeamCenterX, pBeamCenterY, pNormalisation, pNumberFrames, pTimePerFrame )
        self.commands["testCollect"]()



    def collect( self, pDirectory, pPrefix, pRunNumber, pNumberFrames, pTimePerFrame, pConcentration, pComments, pCode, pMaskFile, pDetectorDistance, pWaveLength, pPixelSizeX, pPixelSizeY, pBeamCenterX, pBeamCenterY, pNormalisation, pRadiationChecked, pRadiationAbsolute, pRadiationRelative, pProcessData, pSEUTemperature, pStorageTemperature ):
        #TODO: DEBUG
        logger.info( "Starting collection now" )
        try:
            self.storageTemperature = float( pStorageTemperature )
        except Exception:
            self.storageTemperature = 4
            logger.error( "Could not read storage Temperature - Check sample changer connection" )
        try:
            self.exposureTemperature = float( pSEUTemperature )
        except Exception:
            self.storageTemperature = 4
            logger.error( "Could not read exposure Temperature - Check sample changer connection" )
        self.collecting = True
        self.collectDirectory.set_value( pDirectory )
        self.collectPrefix.set_value( pPrefix )
        self.collectRunNumber.set_value( pRunNumber )
        self.collectNumberFrames.set_value( pNumberFrames )
        self.collectTimePerFrame.set_value( pTimePerFrame )
        self.collectConcentration.set_value( pConcentration )
        self.collectComments.set_value( pComments )
        self.collectCode.set_value( pCode )
        self.collectMaskFile.set_value( pMaskFile )
        self.collectDetectorDistance.set_value( pDetectorDistance )
        self.collectWaveLength.set_value( pWaveLength )
        self.collectPixelSizeX.set_value( pPixelSizeX )
        self.collectPixelSizeY.set_value( pPixelSizeY )
        self.collectBeamCenterX.set_value( pBeamCenterX )
        self.collectBeamCenterY.set_value( pBeamCenterY )
        self.collectNormalisation.set_value( pNormalisation )
        self.prepareEdnaInput( pConcentration, pComments, pCode, pMaskFile, pDetectorDistance, pWaveLength, pPixelSizeX, pPixelSizeY, pBeamCenterX, pBeamCenterY, pNormalisation, pNumberFrames, pTimePerFrame )


        sPrefix = str( pPrefix )
        ave_filename = os.path.join( pDirectory, "1d", "%s_%03d_ave.dat" % ( sPrefix, pRunNumber ) )
        sub_filename = os.path.join( pDirectory, "ednaSub", "%s_%03d_sub.dat" % ( sPrefix, pRunNumber ) )

        # TODO: only when it is last buffer of the data collection and not always
        # Indeed, it is not possible to get the measurementId of a buffer because the code is not unique
        sample = XSDataBioSaxsSample()
        user = None
        password = None

        # Sending ISPyBs information to EDNA
        if self.isISPyB:
            try:
                user = self.objects["biosaxs_client"].proposalType
                password = self.objects["biosaxs_client"].proposalNumber

                print "[ISPyB] Sending to EDNA login %s,%s, %s" % ( user,
                                                                       self.measurementId,
                                                                       pCode )
                #pyarchDestination = "/data/pyarch/bm29/%s/%s" % (user, self.objects["biosaxs_client"].selectedExperimentId)
                pyarchDestination = self.objects["biosaxs_client"].getPyarchDestination()
                print "[ISPyB] Copying into " + pyarchDestination
                sample = XSDataBioSaxsSample( 
                                         login = XSDataString( user ),
                                         passwd = XSDataString( password ),
                                         measurementID = XSDataInteger( self.measurementId ),
                                         ispybDestination = XSDataFile( XSDataString( pyarchDestination ) ),
                                         collectionOrder = XSDataInteger( self.dataCollectionOrder )
                                         )
            except Exception:
                print "[ISPyB] Error: setting ISPyB to False"
                self.isISPyB = False


        self.xsdAverage = XSDataInputBioSaxsSmartMergev1_0( \
                                inputCurves = [XSDataFile( path = XSDataString( os.path.join( pDirectory, "1d", "%s_%03d_%05d.dat" % ( sPrefix, pRunNumber, i ) ) ) ) for i in range( 1, pNumberFrames + 1 )],
                                mergedCurve = XSDataFile( path = XSDataString( ave_filename ) ),
                                subtractedCurve = XSDataFile( path = XSDataString( sub_filename ) ),
                                sample = sample )
        if pRadiationChecked:
            self.xsdAverage.absoluteFidelity = XSDataDouble( float( pRadiationAbsolute ) )
            self.xsdAverage.relativeFidelity = XSDataDouble( float( pRadiationRelative ) )
        prefixRun = "%s_%03d" % ( sPrefix, pRunNumber )
        if ( self.lastPrefixRun == prefixRun ):
            logger.error( "Collecting the same run again %s_%03d", sPrefix, pRunNumber )
        else:
            self.lastPrefixRun = prefixRun
            logger.info( "Starting collect of run %s_%03d ", sPrefix, pRunNumber )
        #
        # set the energy if needed 
        #
        self.__energy = self.objects["energyWaveLength"].getEnergy()
        self.__currentPilatusThreshold = self.objects["energyWaveLength"].getPilatusThreshold()
        if math.fabs( self.__energy - self.__currentPilatusThreshold ) > self.deltaPilatus:
            if self.__energyAdjust:
                self.objects["energyWaveLength"].setEnergy( self.__energy )
                while not self.objects["energyWaveLength"].pilatusReady() :
                    time.sleep( 0.5 )

        #
        # SET gapfill on the Pilatus (Even if not needed)
        #   
        self.channels["fill_mode"].set_value( "ON" )
        self.commands["collect"]( callback = self.specCollectDone, error_callback = self.collectFailed )

    def collectNewFrameChanged( self, value, last = {"frame":None} ):
        raw_filename = value.split( "," )[0]
        diode_current = self.channels["collectBeamStopDiode"].value()
        self.emit( "collectNewFrameChanged", raw_filename, float( diode_current ), float( self.machineCurrent ), time.asctime() )
        if last["frame"] != raw_filename:
            last["frame"] = raw_filename
            if self.collecting:
                self.triggerEDNA( raw_filename, diode_current )

    def triggerEDNA( self, raw_filename, diode_current ):
        """raw_filename is a path like '/data/visitor/mx1493/bm29/raw/ARR_147_00005.edf' ;
        base is supposed to be 'ARR_147_00005' 
        directory is supposed to be '/data/visitor/mx1493/bm29'
        frame is supposed to be '00005'
        """
        raw_filename = str( raw_filename )
        base = os.path.splitext( os.path.basename( raw_filename ) )[0]
        directory = os.path.dirname( os.path.dirname( raw_filename ) )
        frame = base.split( "_" )[-1]
        #tmp, _ = os.path.splitext( raw_filename )
        #tmp, base = os.path.split( tmp )
        #directory, _ = os.path.split( tmp )
        #frame = ""
        #for c in base[-1::-1]:
        #    if c.isdigit():
        #        frame = c + frame
        #    else:
        #        break

        self.xsdin.experimentSetup.storageTemperature = XSDataDouble( self.storageTemperature )
        self.xsdin.experimentSetup.exposureTemperature = XSDataDouble( self.exposureTemperature )
        self.xsdin.experimentSetup.frameNumber = XSDataInteger( int( frame ) )
        self.xsdin.experimentSetup.beamStopDiode = XSDataDouble( float( diode_current ) )
        # self.machineCurrent is already float
        self.xsdin.experimentSetup.machineCurrent = XSDataDouble( self.machineCurrent )
        self.xsdin.rawImage = XSDataImage( path = XSDataString( raw_filename ) )
        self.xsdin.logFile = XSDataFile( path = XSDataString( os.path.join( directory, "misc", base + ".log" ) ) )
        self.xsdin.normalizedImage = XSDataImage( path = XSDataString( os.path.join( directory, "2d", base + ".edf" ) ) )
        self.xsdin.integratedImage = XSDataImage( path = XSDataString( os.path.join( directory, "misc", base + ".ang" ) ) )
        self.xsdin.integratedCurve = XSDataFile( path = XSDataString( os.path.join( directory, "1d", base + ".dat" ) ) )
        # Save EDNA input to file for re-processing
        xmlFilename = os.path.splitext( raw_filename )[0] + ".xml"
        logger.info( "Saving XML data to %s", xmlFilename )
        self.xsdin.exportToFile( xmlFilename )
        # Run EDNA
        if self.isHPLC:
            try:#HPLC mode on slavia
                jobId = self.commands["startJob_edna1"]( [self.pluginHPLC, self.xsdin.marshal()] )
                self.dat_filenames[jobId] = self.xsdin.integratedCurve.path.value
                logger.info( "Processing job %s started", jobId )
                self.edna1Dead = False
                self.jobSubmitted = True
            except Exception:
                self.showMessageEdnaDead( 1 )
        else:#Simple integration on sparta
            try:
                jobId = self.commands["startJob_edna2"]( [self.pluginIntegrate, self.xsdin.marshal()] )
                self.dat_filenames[jobId] = self.xsdin.integratedCurve.path.value
                logger.info( "Processing job %s started", jobId )
                self.edna2Dead = False
                self.jobSubmitted = True
            except Exception:
                self.showMessageEdnaDead( 2 )


    def specCollectDone( self, returnValue ):
        self.collecting = False
        # start EDNA to calculate average at the end
        if not self.isHPLC:
            try:
                jobId = self.commands["startJob_edna2"]( [self.pluginMerge, self.xsdAverage.marshal()] )
                self.dat_filenames[jobId] = self.xsdAverage.mergedCurve.path.value
                self.edna2Dead = False
                self.jobSubmitted = True
            except Exception:
                self.showMessageEdnaDead( 2 )
        else:
            # If HPLC we can now dump data
            self.flushHPLC()

    # if failed, set failed flag
    def processingFailed( self, jobId ):
        self.processingDone( jobId, jobSuccess = False )

    def processingDone( self, jobId, jobSuccess = True ):
        time.sleep( 0.1 ) #this is to give more priority to other tasks
        if not jobId in self.dat_filenames:
            # Two special "jobId" are ignored
            if jobId not in ["No job succeeded (yet)", "No job Failed (yet)"]:
                # and react only if jobs have been submitted (to avoid spurious events)
                if self.jobSubmitted:
                    logger.warning( "processing Done from EDNA: %s but no Job submitted found in the submit list", jobId )
        else:
            filename = self.dat_filenames.pop( jobId )
            # stop here if not success
            if not jobSuccess:
                logger.info( "processing Failed from EDNA: %s -> %s", jobId, filename )
                return
            logger.info( "processing Done from EDNA: %s -> %s", jobId, filename )
            self.emit( "collectProcessingDone", filename )
            if jobId.startswith( self.pluginMerge ):
                time.sleep( 0.1 )
                try:
                    strXsdout = self.commands["getJobOutput_edna2"]( jobId )
                except Exception:
                    self.edna2Dead = True
                    message = "Tango/EDNA 2 is not responding !"
                    logger.error( message )
                    self.showMessage( 2, message )
                    return
                try:
                    xsd = XSDataResultBioSaxsSmartMergev1_0.parseString( strXsdout )
                    self.edna2Dead = False
                except Exception:
                    message = "Unable to parse string from Tango/EDNA 2"
                    logger.error( message )
                    self.showMessage( 2, message )
                    # no need to continue 
                    return
                if xsd.status is not None:
                    log = xsd.status.executiveSummary.value
                    if "Error" in log:
                        self.showMessage( 1, "Executive summary from EDNA: " + log )
                    else:
                        self.showMessage( 0, "Executive summary from EDNA: " + log )
                else:
                    self.showMessage( 2, "EDNA 2 has a problem - No Executive Summary - Please check" )

                # If autoRG has been used, launch the SAS pipeline (very time consuming)
                if xsd.subtractedCurve is None:
                    logger.info( "SAS pipeline not executed: no subtracted curve" )
                else:
                    if xsd.autoRg is None:
                        logger.info( "SAS pipeline not executed as autoRg previously failed" )
                        return
                    if xsd.gnom is None:
                        logger.info( "SAS pipeline not executed: no datGnom data present" )
                        return
                    rgOut = xsd.autoRg
                    filename = rgOut.filename.path.value
                    dest = os.path.join( os.path.dirname( os.path.dirname( filename ) ), "ednaSas",
                                        os.path.splitext( os.path.basename( filename ) )[0] )
                    if not os.path.isdir( dest ):
                        os.makedirs( dest )
                    logger.info( "filename as input for SAS %s", filename )
                    xsdin = XSDataInputBioSaxsToSASv1_0( subtractedCurve = rgOut.filename,
                                                        destinationDirectory = XSDataFile( XSDataString( dest ) ) )
                    logger.info( "Starting SAS pipeline for file %s", filename )
                    try:
                        time.sleep( 0.1 )
                        jobId = self.commands["startJob_edna1"]( [self.pluginSAS, xsdin.marshal()] )
                        self.dat_filenames[jobId] = rgOut.filename.path.value
                        self.edna1Dead = False
                        self.jobSubmitted = True
                    except Exception, errMsg:
                        message = "Error when trying to start EDNA 1: \n%r" % errMsg
                        self.showMessage( 2, message )
                        self.showMessageEdnaDead( 1 )
            elif jobId.startswith( self.pluginSAS ):
                time.sleep( 0.1 )
                try:
                    strXsdout = self.commands["getJobOutput_edna1"]( jobId )
                except Exception:
                    self.edna1Dead = True
                    message = "Tango/EDNA 1 (slavia) is not responding !"
                    logger.error( message )
                    self.showMessage( 2, message )
                    return
                try:
                    xsd = XSDataResultBioSaxsToSASv1_0.parseString( strXsdout )
                    self.edna1Dead = False
                except Exception:
                    message = "Unable to parse string from Tango/EDNA 1 (slavia)"
                    logger.error( message )
                    self.showMessage( 2, message )
                    # no need to continue 
                    return
                if xsd.status is not None:
                    log = xsd.status.executiveSummary.value
                    if "Error" in log:
                        self.showMessage( 1, log )
                    else:
                        self.showMessage( 0, log )
                try:
                    webPage = xsd.htmlPage.path.value
                except:
                    self.showMessage( 1, "No web page provided by plugin SAS !!!" )
                    return
                #TODO: need to be done automatically
                self.showMessage( 0, "Please display this web page: %s" % webPage )
                self.showMessage( 0, "or look in the SAS tab" )
                self.sasWebDisplay( "file://%s" % webPage )
            elif jobId.startswith( self.pluginHPLC ):#HPLC is on Slavia
                time.sleep( 0.1 )
                try:
                    strXsdout = self.commands["getJobOutput_edna1"]( jobId )
                except Exception:
                    self.edna1Dead = True
                    message = "Tango/EDNA 1 (Slavia) is not responding !"
                    logger.error( message )
                    self.showMessage( 2, message )
                    return
                try:
                    xsd = XSDataResultBioSaxsHPLCv1_0.parseString( strXsdout )
                    self.edna1Dead = False
                except Exception:
                    message = "Unable to parse string from Tango/EDNA 1 (Slavia)"
                    logger.error( message )
                    self.showMessage( 2, message )
                    # no need to continue 
                    return
                if xsd.status is not None:
                    log = xsd.status.executiveSummary.value
                    if "Error" in log:
                        self.showMessage( 1, log )
                    else:
                        self.showMessage( 0, log )



    def _abortCollectWithRobot( self ):
        #TODO: See if we actually come here
        print "---- Aborting Collection with Robot"
        # And stop the run
        self.emit( "collectDone" )
        if  self.__collectWithRobotProcedure is not None:
            self.__collectWithRobotProcedure.kill()



    def collectFailed( self, error ):
        """Callback when collect is aborted in spec (CTRL-C or error)"""
        self.collecting = False
        self._abortCollectWithRobot()

    def flushHPLC( self ):
        try:
            jobId = self.commands["startJob_edna1"]( [self.pluginFlushHPLC, self.xsdin.marshal()] )
            self.edna1Dead = False
            self.jobSubmitted = True
        except Exception:
            self.showMessageEdnaDead( 1 )


    def collectAbort( self ):
        logger.info( "sending abort to stop spec collection" )
        if self.isHPLC:# If HPLC we can now dump data
            self.flushHPLC()

        # abort data collection in spec (CTRL-C) ; maybe it will do nothing if spec is idle
        self.commands["collect"].abort()
        self._abortCollectWithRobot()

        logger.info( "Sending abort to ISPyB" )
        try:
            self.objects["biosaxs_client"].setExperimentAborted()
        except Exception, errMsg:
            self.showMessage( 2, "Error sending abort signal to ISPyB!" % errMsg )

    def testCollectAbort( self ):
        logger.info( "sending abort to stop spec test collection" )

    def setHPLC( self, pValue ):
        self.isHPLC = bool( pValue )

    def setCheckBeam( self, flag ):
        if flag:
            self.channels["checkBeam"].set_value( 1 )
        else:
            self.channels["checkBeam"].set_value( 0 )

    def setRobotFileName( self, pValue ):
        # Update latest Robot File
        self.collectRobotFile.set_value( pValue )

    # overwrite connectNotify ; first values will be read by brick
    def connectNotify( self, signal_name ):
        pass


    def updateChannels( self ):
        for channel_name, channel in self.channels.iteritems():
            if channel_name.startswith( "jobSuccess" ):
                continue
            channel.update( channel.value() )


    def showMessage( self, level, msg, notify = 0 ):
        #TODO: DEBUG
        print "showMessage %s with level %s " % ( msg, level )
        self.emit( "collectProcessingLog", level, msg, notify )


    def _collectOne( self, sample, pars, mode = None ):
        timeBefore = datetime.datetime.now()
        # ==================================================
        #  SETTING VISCOSITY
        # ==================================================
        if mode == "buffer_before":
            # this will allow to use several buffers of same name for same sample
            # we should check if enough volume is not available then go to next buffer in list
            tocollect = sample["buffer"][0]
        elif mode == "buffer_after":
            tocollect = sample["buffer"][0]
        else:
            tocollect = sample


        if self.objects["sample_changer"].setViscosityLevel( tocollect["viscosity"].lower() ) == -1:
            self.showMessage( 2, "Error when trying to set viscosity to '%s'...\nAborting collection!" % tocollect["viscosity"] )
            self.collectAbort()
            # allow time to abort
            time.sleep( 5 )

        # ==================================================
        #  SETTING SEU TEMPERATURE
        # ==================================================                        
        # temperature is taken from sample (not from buffer) even if buffer is collected
        self.showMessage( 0, "Setting SEU temperature to '%s'..." % sample["SEUtemperature"] )
        try:
            self.objects["sample_changer"].doSetSEUTemperatureProcedure( sample["SEUtemperature"] )
        except Exception, errMsg:
            self.showMessage( 2, "Error when setting SEU temperature. Error:\n%r\nAborting collection!" % errMsg )
            self.collectAbort()
            # allow time to abort
            time.sleep( 5 )

        # ==================================================
        #  FILLING 
        # ==================================================        
        self.showMessage( 0, "Filling (%s) from plate '%s', row '%s' and well '%s' with volume '%s'..." % ( mode, tocollect["plate"], tocollect["row"], tocollect["well"], tocollect["volume"] ) )
        try:
            self.objects["sample_changer"].doFillProcedure( tocollect["plate"], tocollect["row"], tocollect["well"], tocollect["volume"] )
        except Exception, errMsg:
            # Check if we have a standard Tango error (PyTango.DevFailed)
            msg = self.tangoErrMsgExtractDesc( errMsg )
            if msg is not None:
                message = "Error when trying to fill from plate '%s', row '%s' and well '%s' with volume '%s'.\nSampleChanger Error:\n%s\nAborting collection!" % ( tocollect["plate"], tocollect["row"], tocollect["well"], tocollect["volume"], msg )
                self.showMessage( 2, message, notify = 1 )
            else:
                message = "Error when trying to fill from plate '%s', row '%s' and well '%s' with volume '%s'.\nSampleChanger Error:\n%r\nAborting collection!" % ( tocollect["plate"], tocollect["row"], tocollect["well"], tocollect["volume"], errMsg )
                self.showMessage( 2, message )
            self.collectAbort()
            # allow time to abort
            time.sleep( 5 )

        # ==================================================
        #  FLOW
        # ==================================================
        if tocollect["flow"]:
            self.showMessage( 0, "Flowing with volume '%s' during '%s' second(s)..." % ( tocollect["volume"], pars["flowTime"] ) )
            try:
                self.objects["sample_changer"].flow( tocollect["volume"], pars["flowTime"] )
            except Exception, errMsg:
                # Check if we have a standard Tango error (PyTango.DevFailed)
                msg = self.tangoErrMsgExtractDesc( errMsg )
                if msg is not None:
                    message = "Error when trying to flow with volume '%s' during '%s' second(s)...\n%s\Aborting collection!" % ( tocollect["volume"], pars["flowTime"], msg )
                    self.showMessage( 2, message, notify = 1 )
                else:
                    message = "Error when trying to flow with volume '%s' during '%s' second(s)...\n%r\Aborting collection!" % ( tocollect["volume"], pars["flowTime"], errMsg )
                    self.showMessage( 2, message )
                self.collectAbort()
                # allow time to abort
                time.sleep( 5 )
        else:
            self.objects["sample_changer"].setLiquidPositionFixed( True )

        # ==========================
        #  SETTING TRANSMISSION 
        # ========================== 
        self.showMessage( 0, "Setting transmission for plate '%s', row '%s' and well '%s' to %s%s..." % ( tocollect["plate"], tocollect["row"], tocollect["well"], tocollect["transmission"], "%" ) )
        self.emit( "transmissionChanged", tocollect["transmission"] )

        # ==================================================
        #  PERFORM COLLECT
        # ==================================================
        self.showMessage( 0, "  - Start collecting (%s) '%s'..." % ( mode, pars["prefix"] ) )
        # Clear 1D curve
        # Commented out 26/6 2012 on order by Petra Pernot (SO)
        #self.emit("clearCurve")

        self.collect( pars["directory"],
                     pars["prefix"], pars["runNumber"],
                     pars["frameNumber"], pars["timePerFrame"], tocollect["concentration"], tocollect["comments"],
                     tocollect["code"], pars["mask"], pars["detectorDistance"], pars["waveLength"],
                     pars["pixelSizeX"], pars["pixelSizeY"], pars["beamCenterX"], pars["beamCenterY"],
                     pars["normalisation"], pars["radiationChecked"], pars["radiationAbsolute"],
                     pars["radiationRelative"],
                     pars["processData"], pars["SEUTemperature"], pars["storageTemperature"] )

        while self.collecting:
            time.sleep( 1 )

        self.showMessage( 0, "  - Finish collecting '%s'..." % pars["prefix"] )

        # ======================
        #  WAIT FOR END OF FLOW 
        # ======================
        if tocollect["flow"]:
            self.showMessage( 0, "Waiting for end of flow..." )
            try:
                self.objects["sample_changer"].wait()
            except Exception, errMsg:
                # Check if we have a standard Tango error (PyTango.DevFailed)
                msg = self.tangoErrMsgExtractDesc( errMsg )
                if msg is not None:
                    message = "Error when waiting for end of flow.\nSampleChanger Error:\n%s\nAborting collection!" % msg
                    self.showMessage( 2, message, notify = 1 )
                else:
                    message = "Error when waiting for end of flow.\nSampleChanger Error:\n%r\nAborting collection!" % errMsg
                    self.showMessage( 2, message )
                self.collectAbort()
                # allow time to abort
                time.sleep( 5 )

        # =============
        #  RECUPERATE 
        # =============
        if tocollect["recuperate"]:
            self.showMessage( 0, "Recuperating to plate '%s', row '%s' and well '%s'..." % ( tocollect["plate"], tocollect["row"], tocollect["well"] ) )
            try:
                self.objects["sample_changer"].doRecuperateProcedure( tocollect["plate"], tocollect["row"], tocollect["well"] )
            except Exception, errMsg:
                # Check if we have a standard Tango error (PyTango.DevFailed)
                msg = self.tangoErrMsgExtractDesc( errMsg )
                if msg is not None:
                    message = "Error when trying to recuperate to plate '%s', row '%s' well '%s'...\nSampleChanger Error:\n%s\nAborting collection!" % ( tocollect["plate"], tocollect["row"], tocollect["well"], msg )
                    self.showMessage( 2, message, notify = 1 )
                else:
                    message = "Error when trying to recuperate to plate '%s', row '%s' well '%s'...\nSampleChanger Error:\n%r\nAborting collection!" % ( tocollect["plate"], tocollect["row"], tocollect["well"], errMsg )
                    self.showMessage( 2, message )
                self.collectAbort()
                # allow time to abort
                time.sleep( 5 )

        # ==================================================
        #  CLEANING
        # ==================================================
        self.showMessage( 0, "Cleaning..." )

        try:
            self.objects["sample_changer"].doCleanProcedure()
        except Exception, errMsg:
            # Check if we have a standard Tango error (PyTango.DevFailed)
            msg = self.tangoErrMsgExtractDesc( errMsg )
            if msg is not None:
                message = "Error when trying to clean.\nSampleChanger Error:\n%s\nAborting collection!" % msg
                self.showMessage( 2, message, notify = 1 )
            else:
                message = "Error when trying to clean.\nSampleChanger Error:\n%r\nAborting collection!" % errMsg
                self.showMessage( 2, message )
            self.collectAbort()
            # allow time to abort
            time.sleep( 5 )

        # We took a frame, now send info to ISPyB
        #TODO: DEBUG
        timeAfter = datetime.datetime.now()
        return ( pars, tocollect, timeBefore, timeAfter, mode )


    def saveFrame( self, pars, tocollect, timeBefore, timeAfter, mode, sampleCode, measurementId ):
        self.showMessage( 0, "[ISPyB] Preparing to send to ISPyB: " + mode )
        files = []
        for i in range( 1, pars["frameNumber"] + 1 ):
            files.append( os.path.join( pars["directory"], "raw", "%s_%03d_%05d.dat" % ( pars["prefix"], pars["runNumber"], i ) ) )

        exposureTemperature = pars["SEUTemperature"]
        storageTemperature = pars["storageTemperature"]
        timePerFrame = pars["timePerFrame"]
        timeStart = timeBefore
        timeEnd = timeAfter
        energy = self.hcOverE / float( pars["waveLength"] )
        detectorDistance = pars["detectorDistance"]
        snapshotCapillary = "snapshotCapillary"
        currentMachine = "currentMachine"

        ispybMode = None
        if mode is "buffer_before":
            ispybMode = "before"
            #self.objects["biosaxs_client"].saveFrameSet("before", sampleCode, exposureTemperature, storageTemperature, timePerFrame, timeStart, timeEnd, energy, detectorDistance, str(files), snapshotCapillary, currentMachine, str(tocollect), str(pars))
        if mode is "buffer_after":
            ispybMode = "after"
            #self.objects["biosaxs_client"].saveFrameSet("after", sampleCode, exposureTemperature, storageTemperature, timePerFrame, timeStart, timeEnd, energy, detectorDistance, str(files), snapshotCapillary, currentMachine, str(tocollect), str(pars))
        if mode is "sample":
            ispybMode = "sample"
            #self.objects["biosaxs_client"].saveFrameSet("sample", sampleCode, exposureTemperature, storageTemperature, timePerFrame, timeStart, timeEnd, energy, detectorDistance, str(files), snapshotCapillary, currentMachine, str(tocollect), str(pars))

        self.objects["biosaxs_client"].saveFrameSet( ispybMode, sampleCode, exposureTemperature, storageTemperature, timePerFrame, timeStart, timeEnd, energy, detectorDistance, str( files ), snapshotCapillary,
                                                    currentMachine,
                                                    tocollect,
                                                    pars,
                                                    measurementId
                                                    )

    def setXMLRobotFilePath( self, path ):
        self.xmlRobotFilePath = path

    def _collectWithRobot( self, pars ):

        lastBuffer = ""
        # Setting sample type
        # Synchronous - no exception handling
        self.objects["sample_changer"].setSampleType( pars["sampleType"].lower() )


        # ===========================================
        #  Silent creation of the experiment in ISPyB
        # ===========================================
        try:
            if not pars["collectISPYB"]:
                print "[ISPyB] Create a new experiment in ISPyB"

                ispyBuffers = []
                bufferNames = []
                ##Collecting the buffers
                for sample in pars["sampleList"]:
                    if sample["enable"]:
                        if sample["buffer"][0]["buffername"] not in bufferNames:
                            bufferNames.append( sample["buffer"][0]["buffername"] )
                            ispyBuffers.append( sample["buffer"][0] )

                ##Collecting the samples
                idCounter = 1 #This id counter is a tag that it will set into the commets to identify the measurement
                for sample in pars["sampleList"]:
                    if sample["enable"]:
                        sample["comments"] = "[" + str( idCounter ) + "] " + sample["comments"]
                        sampleWithNoBufferAttribute = sample.copy()
                        sampleWithNoBufferAttribute["buffer"] = ""
                        ispyBuffers.append( sampleWithNoBufferAttribute )
                        idCounter = idCounter + 1

                fileNamePath = "Unknown"
                filePath = "Unknown"
                if ( self.xmlRobotFilePath is not None ):
                    fileNamePath = os.path.basename( self.xmlRobotFilePath )
                    filePath = self.xmlRobotFilePath


                self.objects["biosaxs_client"].createExperiment( 
#                                                                "mx", 1438,
                                                                 ispyBuffers,
                                                                 pars["storageTemperature"],
                                                                 "BeforeAndAfter",
                                                                 "10",
                                                                 "STATIC",
                                                                 filePath,
                                                                 fileNamePath )
                self.isISPyB = True #Tobe replaced by self.isISPyB
                print "[ISPyB] isISPyB set to True"
        except Exception:
            self.isISPyB = False
            traceback.print_exc()
            print "[ISPyB] Warning: isISPyB set to False"


        # ============================
        #  Setting storage temperature
        # ============================
        self.showMessage( 0, "Setting storage temperature to '%s' C..." % pars["storageTemperature"] )
        try:
            # ASynchronous - Treated in sample Changer
            self.objects["sample_changer"].setStorageTemperature( pars["storageTemperature"] )
        except Exception, errMsg:
            # Check if we have a standard Tango error (PyTango.DevFailed)
            msg = self.tangoErrMsgExtractDesc( errMsg )
            if msg is not None:
                message = "Error when trying to set Storage Temperature.\nSampleChanger Error:\n%s\nAborting collection!" % msg
                self.showMessage( 2, message, notify = 1 )
            else:
                message = "Error when trying to set Storage Temperature.\nSampleChanger Error:\n%r\nAborting collection!" % errMsg
                self.showMessage( 2, message )
            self.collectAbort()
            # allow time to abort
            time.sleep( 5 )

        # Open guillotine
        self.commands["guillopen"]()
        # count for 30s and then give alarm
        count = 0
        # wait  for "3" = open
        while self.channels["guillstate"].value() != "3":
            time.sleep( 0.5 )
            if count > 60 :
                message = "Error when trying to open guillotine. Aborting collection!"
                self.showMessage( 2, message )
                self.collectAbort()
                break

        # Open shutter
        self.commands["shopen"]()

        if pars["initialCleaning"]:
            self.showMessage( 0, "Initial cleaning..." )
            try:
                self.objects["sample_changer"].doCleanProcedure()
            except Exception, errMsg:
                # Check if we have a standard Tango error (PyTango.DevFailed)
                msg = self.tangoErrMsgExtractDesc( errMsg )
                if msg is not None:
                    message = "Error when trying to clean.\nSampleChanger Error:\n%s\nAborting collection!" % msg
                    self.showMessage( 2, message, notify = 1 )
                else:
                    message = "Error when trying to clean.\nSampleChanger Error:\n%r\nAborting collection!" % errMsg
                    self.showMessage( 2, message )
                self.collectAbort()
                # wait for abort to work
                time.sleep( 5 )

        self.lastSampleTime = time.time()
        prevSample = None
        runNumberSet = True
        # ==================================================
        #   MAIN LOOP on Samples
        # ==================================================
        measurementISPyBIteratorId = 1
        for sample in pars["sampleList"]:
            self.dataCollectionOrder = 0

            #ISPyB
            if ( self.isISPyB ):
                try:
                    self.measurementId = self.objects["biosaxs_client"].getMeasurementIdByCommentId( measurementISPyBIteratorId )
                    measurementISPyBIteratorId = measurementISPyBIteratorId + 1
                except Exception:
                    print "[ISPyB] Error: Setting ISPyB to False"
                    self.isISPyB = False
            #
            #  Collect buffer before
            #     - in mode BufferBefore  , always
            #     - in mode BufferFirst   , at beginning and every time buffer changes
            # 
            # In buffer first mode check also if temperature has changed. If so, consider as
            #    a change in buffer
            doFirstBuffer = pars["bufferBefore"]
            # in bufferFirst mode decide when to collect the buffer 
            if pars["bufferFirst"]:
                if sample["buffername"] != lastBuffer:
                    doFirstBuffer = True
                if prevSample is not None:
                    if prevSample["SEUtemperature"] != sample["SEUtemperature"]:
                        self.showMessage( 0, "SEU Temperature different from previous. Collecting buffer." )
                        doFirstBuffer = True

            if doFirstBuffer:
                if sample["buffername"] != lastBuffer:
                    lastBuffer = sample["buffername"]
                if runNumberSet:
                    # Using pars["runNumber"] from collect brick
                    runNumberSet = False
                else:
                    # need to increase run number
                    pars["runNumber"] = self.nextRunNumber

                self.dataCollectionOrder = 0
                ( pars, tocollect, timeBefore, timeAfter, mode ) = self._collectOne( sample, pars, mode = "buffer_before" )
                if self.isISPyB:
                    self.saveFrame( pars, tocollect, timeBefore, timeAfter, mode, sample["code"], self.measurementId )

            #
            # Wait if necessary before collecting sample
            #
            if sample["waittime"]:
                time_to_wait = sample["waittime"]
                while time_to_wait > 0:
                    self.showMessage( 0, "Waiting to start next sample. %d secs left..." % time_to_wait )
                    time.sleep( min( 10, time_to_wait ) )
                    time_to_wait = time_to_wait - 10
                self.showMessage( 0, "    Done waiting." )

            self.lastSampleTime = time.time()

            #
            # Collect sample
            #

            if runNumberSet:
                # Using pars["runNumber"] from collect brick
                runNumberSet = False
            else:
                # need to increase run number
                pars["runNumber"] = self.nextRunNumber

            self.dataCollectionOrder = 1
            ( pars, tocollect, timeBefore, timeAfter, mode ) = self._collectOne( sample, pars, mode = "sample" )
            if self.isISPyB:
                self.saveFrame( pars, tocollect, timeBefore, timeAfter, mode, sample["code"], self.measurementId )

            if pars["bufferAfter"]:

                if runNumberSet:
                    # Using pars["runNumber"] from collect brick
                    runNumberSet = False
                else:
                    # need to increase run number
                    pars["runNumber"] = self.nextRunNumber
                self.dataCollectionOrder = 2
                ( pars, tocollect, timeBefore, timeAfter, mode ) = self._collectOne( sample, pars, mode = "buffer_after" )
                if self.isISPyB:
                    self.saveFrame( pars, tocollect, timeBefore, timeAfter, mode, sample["code"], self.measurementId )

            prevSample = sample

        #
        # End of for sample loop
        #---------------------------------- 
        # Let us close guillotine and shutter
        self.commands["guillclose"]()
        self.commands["shclose"]()
        self.showMessage( 0, "The data collection is done!" )
        ## Sending status to ISPyB
        if ( self.isISPyB ):
            try:
                self.measurementId = self.objects["biosaxs_client"].updateStatus( "FINISHED" )
            except Exception:
                traceback.print_exc()

        self.emit( "collectDone" )


    def collectWithRobot( self, *args ):
        # if EDNA 2 is dead we do not collect !
        if not self.edna2Dead:
            self.__collectWithRobotProcedure = gevent.spawn( self._collectWithRobot, *args )
        else:
            message = "EDNA server 2 is dead, please restart EDNA 2"
            self.showMessage( 2, message, notify = 1 )

