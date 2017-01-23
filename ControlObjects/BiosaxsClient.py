import json
from Framework4.Control.Core.CObject import CObjectBase, Slot, Signal
from suds.client import Client
from suds.transport.http import HttpAuthenticated
import traceback
import sys
import time
import os, shutil
from contextlib import closing
import zipfile
import datetime
import glob

class BiosaxsClient( CObjectBase ):
    signals = [
               Signal( "onSuccess" ),
               Signal( "onError" )
               ]
    slots = [
             Slot( "getExperimentNamesByProposalCodeNumber" ),
             Slot( "setUser" ),
             Slot( "getRobotXMLByExperimentId" )
             ]

    def init( self ):
        self.client = None

        #Prod machine
        self.URL = 'http://ispyb.esrf.fr:8080/ispyb/ispyb-ws/ispybWS/ToolsForBiosaxsWebService?wsdl'
        #Test machine
        #self.URL = 'http://ispyvalid.esrf.fr:8080/ispyb/ispyb-ws/ispybWS/ToolsForBiosaxsWebService?wsdl'

        print "ISPyB Server: " + self.URL

        self.selectedExperimentId = None

        #Login information
        self.user = None
        self.password = None
        self.proposalType = None
        self.proposalNumber = None


        self.timeout = 15
        self.experiments = None

    def __initWebservice( self ):

        self.httpAuthenticatedToolsForAutoprocessingWebService = HttpAuthenticated( username = self.user, password = self.password )
        self.client = Client( self.URL, transport = self.httpAuthenticatedToolsForAutoprocessingWebService, cache = None, timeout = self.timeout )
        self.experiments = []
        self.response = None


    def setUser( self, user, password, proposalType, proposalNumber ):
        self.user = user #"mx1438"
        self.password = password #"Rfo4-73"
        self.proposalType = proposalType
        self.proposalNumber = proposalNumber

    def getExperimentNamesByProposalCodeNumber( self, code, number ):
        if ( self.client is None ):
            self.__initWebservice()
        return self.client.service.findExperimentByProposalCode( code, number )
#        self.emit( "onSuccess", "getExperimentNamesByProposalCodeNumber", json.loads( response ) )

    #Without ExperimentId
    def getPyarchDestinationForHPLC( self ):
	date = datetime.datetime.today().strftime('%Y%m%d')
        return "/data/pyarch/2017/bm29/%s%s/%s/hplc" % ( self.proposalType, self.proposalNumber, date )


    def getPyarchDestination( self ):
	date = datetime.datetime.today().strftime('%Y%m%d')
        # This happens because I need the experiment ID but because the experiment has not been created yet I have to replace it in the server side
        # so I will replace /data/pyarch/bm29/%s%s/__ID__ by the good ID
        if ( self.selectedExperimentId is None ):
            self.selectedExperimentId = "__ID__"
        return "/data/pyarch/2017/bm29/%s%s/%s/%s" % ( self.proposalType, self.proposalNumber, date,self.selectedExperimentId )


    #It looks for a code in the comments that identifies the measurements
    # [1] This is a comment
    # ---
    #  |_ Id
    def getMeasurementIdByCommentId( self, commentId ):
        try:
            for experiment in self.experiments:
                if experiment.experiment.experimentId == self.selectedExperimentId:
                    for sample in experiment.experiment.samples:
                        #for specimen in sample.specimen3VOs:
                        for specimen in sample.measurements:
                            if str( specimen.comment ).find( "[" + str( commentId ) + "]" ) != -1:
                                return specimen.measurementId
        except:
            traceback.print_exc()
            raise Exception
        return -1

    ### Mode: before, after, sample    
    def saveFrameSet( self, mode, runNumber, exposureTemperature, storageTemperature, timePerFrame, timeStart, timeEnd, energy, detectorDistance, fileArray, snapshotCapillary, currentMachine, tocollect, pars, specimenId ):
        try:
            print "[ISPyB] Request for saveFrameSet " + str( mode ) + " " + str( runNumber )
            if ( self.client is None ):
                self.__initWebservice()

            #specimenId = self.getMeasurementIdBySampleCodeConcentrationAndSEU(sampleCode, concentration, ispybSEUtemperature, bufferName)
            if specimenId is None:
                specimenId = -1

            self.client.service.saveFrame( mode,
                                          self.selectedExperimentId,
                                          specimenId,
                                          runNumber,
                                          exposureTemperature,
                                          storageTemperature,
                                          timePerFrame,
                                          timeStart,
                                          timeEnd,
                                          energy,
                                          detectorDistance,
                                          fileArray,
                                          snapshotCapillary,
                                          currentMachine,
                                          str( tocollect ),
                                          str( pars ),
                                          pars["beamCenterX"],
                                          pars["beamCenterY"],
                                          pars["radiationRelative"],
                                          pars["radiationAbsolute"],

                                          pars["pixelSizeX"],
                                          pars["pixelSizeY"],
                                          pars["normalisation"],
                                          tocollect["transmission"]
                                          )
        except Exception:
            print "[ISPyB] error", sys.exc_info()[0]
            #traceback.print_exc()

    def getRobotXMLByExperimentId( self, experimentId ):
        self.selectedExperimentId = experimentId
        if ( self.client is None ):
            self.__initWebservice()
        return self.client.service.getRobotByExperimentId( experimentId )

    def setExperimentAborted( self ):
        try:
            self.updateStatus( "ABORTED" )
        except Exception:
            traceback.print_exc()
            raise Exception

    def updateStatus( self, status ):
        try:
            if ( self.client is None ):
                self.__initWebservice()
        except Exception:
            print "[ISPyB] It has been not possible to connect with ISPyB. No connection"
            raise Exception
        try:
            if ( self.selectedExperimentId is not None ):
                self.client.service.updateStatus( self.selectedExperimentId, status )


        except Exception:
            traceback.print_exc()
            raise Exception


    def movefile( self, afile, destination ):
        try:
            print "[ISPyB] Moving %s to : %s " % ( afile, destination )
            if not os.path.isdir( destination ):
                print "[ISPyB] Creating directory %s " % ( destination )
                os.makedirs( destination )
            shutil.move( afile, destination )
        except IOError as error:
            print "[ISPyB] Handled error while directory creation in pyarch: %s " % error


    def copyfile( self, afile, pyarch ):
        try:
            print "[ISPyB] Copying %s to pyarch: %s " % ( afile, pyarch )
            if not os.path.isdir( pyarch ):
                print "[ISPyB] Creating directory %s " % ( pyarch )
                os.makedirs( pyarch )
            shutil.copy( afile, pyarch )
        except IOError as error:
            print "[ISPyB] Handled error while directory creation in pyarch: %s " % error


    def createExperiment( self, samples, storageTemperature, mode, extraflowTime, experimentType, sourceFile, name ):
        try:
            if ( self.client is None ):
                self.__initWebservice()
        except Exception:
            print "[ISPyB] It has been not possible to connect with ISPyB. No connection"
            raise Exception

        try:
            self.experiment = None
            self.selectedExperimentId = None
            expectedXMLFilePath = self.getPyarchDestination() + '/' + name
            print "[ISPyB] Request to ISPyB: create new experiment for proposal " + str( self.proposalType ) + str( self.proposalNumber )
            print "[ISPyB] Name " + str( name )
            if ( ( str ( name ) == "BSA.xml" ) | ( str ( name ) == "Water.xml" ) ):
                experimentType = "CALIBRATION"


            experiment = self.client.service.createExperiment( 
                                                               self.proposalType,
                                                               self.proposalNumber,
                                                               str( samples ),
                                                               storageTemperature,
                                                               mode,
                                                               extraflowTime,
                                                               experimentType,
                                                               expectedXMLFilePath,
                                                               name )

            if ( experiment is None ):
                print "[ISPyB] ISPyB could not create the experiment from robot file"
                raise Exception

            print "[ISPyB] Experiment Created: " + str( experiment.experimentId )
            self.selectedExperimentId = experiment.experimentId
            self.experiment = Experiment( experiment )
            self.experiments.append( Experiment( experiment ) )
            print "[ISPyB] selectedExperimentId: " + str( self.selectedExperimentId )
        except Exception:
            print "[ISPyB] handled error"
            traceback.print_exc()
            raise Exception

        # Copying xml file to pyarch. It doesnt raise an exception
        self.copyfile( sourceFile, self.getPyarchDestination() )


    def logDataPolicyMessage( self, msg):
        file = open("/tmp/datapolicy.log","a+") 
        file.write("%s\n" % (msg)) 
        file.close() 

    # For data policy 
    def storeDataset(self, experimentType, directory, runNumber, sPrefix, pMaskFile, numberFrames, timePerFrame, concentration, comments, code, detectorDistance, waveLength, pixelSizeX, pixelSizeY, beamCenterX, beamCenterY, normalisation,diodeCurrents):

        # We have to wait for 1d creation to be completed
        if experimentType != 'TEST':
	    for i in range(10):
                time.sleep(1)
                self.logDataPolicyMessage('Sleeping %s seconds'%(str(i)))

 
	# Sample Changer experiments
	rawFiles = glob.glob("%s/%s/%s_*%s_?????.edf" %(directory, 'raw', sPrefix,runNumber))
        xmlFiles = glob.glob("%s/%s/%s_*%s_?????.xml" %(directory, 'raw', sPrefix,runNumber))
	onedFiles = glob.glob("%s/%s/%s_*%s_?????.dat" %(directory, '1d' , sPrefix,runNumber))
	
        # For HPLC it adds _buffer_aver_ and it is only four digits
	onedFiles = onedFiles + glob.glob("%s/%s/%s_*%s_buffer_aver_????.dat" %(directory, '1d' , sPrefix,runNumber))
	onedFiles = onedFiles + glob.glob("%s/%s/%s_*%s_?????_sub.dat" %(directory, '1d' , sPrefix,runNumber))		

        files = rawFiles + onedFiles + xmlFiles
	
	# It removes the test image that it is always ending by 00000.edf
        if experimentType != 'TEST':
             files = filter(lambda x : (x.endswith('00000.edf') != True), files)

	
       
        self.logDataPolicyMessage("\n\n-----------------\n")  
	self.logDataPolicyMessage("Proposal: %s" % (self.proposalType + self.proposalNumber)) 
	self.logDataPolicyMessage("directory %s" % (directory))
        self.logDataPolicyMessage("experimentType %s" % (experimentType))  
        self.logDataPolicyMessage("RunNumber %s" % (runNumber)) 
        self.logDataPolicyMessage("Prefix: %s" % (sPrefix)) 
        self.logDataPolicyMessage("pMaskFile: %s" % (str(pMaskFile)))
        self.logDataPolicyMessage("numberFrames: %s" % (str(numberFrames))) 
        self.logDataPolicyMessage("timePerFrame: %s" % (str(timePerFrame))) 
        self.logDataPolicyMessage("concentration: %s" % (str(concentration))) 
        self.logDataPolicyMessage("comments: %s" % (str(comments))) 
        self.logDataPolicyMessage("code: %s" % (str(code))) 
        self.logDataPolicyMessage("detectorDistance: %s" % (str(detectorDistance))) 
        self.logDataPolicyMessage("waveLength: %s" % (str(waveLength))) 
        self.logDataPolicyMessage("pixelSizeX: %s" % (str(pixelSizeX)))  
        self.logDataPolicyMessage("pixelSizeY: %s" % (str(pixelSizeY)))  
        self.logDataPolicyMessage("beamCenterX: %s" % (str(beamCenterX)))  
        self.logDataPolicyMessage("beamCenterY: %s" % (str(beamCenterY)))  
        self.logDataPolicyMessage("normalisation: %s" % (str(normalisation)))
        self.logDataPolicyMessage("diodeCurrents: %s" % (str(diodeCurrents)))    

        self.logDataPolicyMessage("%s/%s/%s_*%s_?????.edf" %(directory, 'raw', sPrefix,runNumber)) 


class Experiment:
    def __init__( self, experiment ):
        self.experiment = experiment

    def getBuffers( self ):
        return self.experiment.buffer3VOs

    def getPlates( self ):
        return self.experiment.samplePlate3VOs

    def getPlateGroups( self ):
        plates = self.getPlates()
        print plates
        dict = {}
        plateGroups = []
        for plate in plates:
            print str( plate )
            if hasattr( plate, 'plategroup3VO' ):
                print "contiene plategroup3VO"
                if not dict.has_key( plate.plategroup3VO.name ):
                    print "plate.plategroup3VO.name"
                    if plate.plategroup3VO is not None:
                        plateGroups.append( plate.plategroup3VO )
                    dict[plate.plategroup3VO.name] = True
        return plateGroups

if __name__ == "__main__":
    biosaxs = BiosaxsClient( "mx1438", "Rfo4-73" )
    biosaxs.getExperimentNamesByProposalCodeNumber( "mx", "1438" )
 
    biosaxs.selectedExperimentId = 345


