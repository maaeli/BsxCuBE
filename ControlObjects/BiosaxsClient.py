import json
from Framework4.Control.Core.CObject import CObjectBase, Slot, Signal
from suds.client import Client
from suds.transport.http import HttpAuthenticated
import traceback
import sys
import os, shutil
from contextlib import closing
import zipfile

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
        #self.URL = 'http://ispyb.esrf.fr:8080/ispyb-ejb3/ispybWS/ToolsForBiosaxsWebService?wsdl'
        #Test machine
        self.URL = 'http://ispyvalid.esrf.fr:8080/ispyb-ejb3/ispybWS/ToolsForBiosaxsWebService?wsdl'
        #Alejandro's local machine
        #self.URL = 'http://pcantolinos:8080/ispyb-ejb3/ispybWS/ToolsForBiosaxsWebService?wsdl'
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

    def getPyarchDestination( self ):
        # This happens because I need the experiment ID but because the experiment has not been created yet I have to replace it in the server side
        # so I will replace /data/pyarch/bm29/%s%s/__ID__ by the good ID
        if ( self.selectedExperimentId is None ):
            self.selectedExperimentId = "__ID__"

        if ( self.URL == 'http://ispyb.esrf.fr:8080/ispyb-ejb3/ispybWS/ToolsForBiosaxsWebService?wsdl' ):
            return "/data/pyarch/bm29/%s%s/%s" % ( self.proposalType, self.proposalNumber, self.selectedExperimentId )
        return "/data/pyarch/bm29/testing/%s%s/%s" % ( self.proposalType, self.proposalNumber, self.selectedExperimentId )

    def getSpecimenIdBySampleCode( self, sampleCode ):
        print "[ISPyB] getSpecimenIdBySampleCode " + str( sampleCode )
        if self.experiment is None:
            print "[ISPyB] Experiment is None"
            return None
        if self.selectedExperimentId is None:
            print "[ISPyB] Experiment is None"
            return None
        for experiment in self.experiments:
            #print experiment.experiment.experimentId
            if experiment.experiment.experimentId == self.selectedExperimentId:
                for sample in experiment.experiment.samples:
                    #for specimen in sample.specimen3VOs:
                    for specimen in sample.measurements:
                        if specimen.code == sampleCode:
                            return specimen.specimenId
        return None

    # Return an array of samples which a given concentration
    def getSpecimensByConcentration( self, concentration ):
        print "[ISPyB] getSpecimenByConcentration: " + str( concentration )
        if self.experiment is None:
            print "[ISPyB] Experiment is None"
            return None
        if self.selectedExperimentId is None:
            print "[ISPyB] Experiment is None"
            return None

        samples = []
        for experiment in self.experiments:
            if experiment.experiment.experimentId == self.selectedExperimentId:
                for sample in experiment.experiment.samples:
                    if ( float( sample.concentration ) ) == ( float( concentration ) ):
                        samples.append( sample )
        return samples


    def getBufferIdByAcronym( self, bufferName ):
        for myBuffer in self.experiment.getBuffers():
            if bufferName == myBuffer.acronym:
                return myBuffer.bufferId
        return None

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

    def getMeasurementIdBySampleCodeConcentrationAndSEU( self, sampleCode, concentration, seu, bufferName ):
        try:
#            print "[ISPyB] getMeasurementIdBySampleCodeConcentrationAndSEU " + str( sampleCode ) + " " + str( concentration ) + " " + str( seu ) + " " + str( bufferName )
            if self.experiment is None:
                print "[ISPyB] Experiment is None"
                return None
            if self.selectedExperimentId is None:
                print "[ISPyB] Experiment is None"
                return None
            bufferId = self.getBufferIdByAcronym( bufferName )
#            print "[ISPyB] bufferId " + str( bufferId )
            for experiment in self.experiments:
                #print experiment.experiment.experimentId
                if experiment.experiment.experimentId == self.selectedExperimentId:
                    samples = self.getSpecimensByConcentration( concentration )
                    for sample in samples:
                        if sample.bufferId == bufferId:
                            #for specimen in sample.specimen3VOs:
                            for specimen in sample.measurements:
                                if ( float( specimen.exposureTemperature ) == float( seu ) and ( str( specimen.code ) == str( sampleCode ) ) ):
                                    return specimen.specimenId
        except Exception:
            print "[ISPyB] error"
            traceback.print_exc()
            raise Exception
        print "[ISPyB] Measurement not found with conc: %s SEU: %s and sampleCode:%s" % ( str( concentration ), str( seu ), str( sampleCode ) )
        return -1

    ### Mode: before, after, sample    
    def saveFrameSet( self, mode, sampleCode, exposureTemperature, storageTemperature, timePerFrame, timeStart, timeEnd, energy, detectorDistance, fileArray, snapshotCapillary, currentMachine, tocollect, pars, specimenId ):
        try:
            print "[ISPyB] Request for saveFrameSet " + str( mode ) + " " + str( sampleCode )
            if ( self.client is None ):
                self.__initWebservice()

            #specimenId = self.getMeasurementIdBySampleCodeConcentrationAndSEU(sampleCode, concentration, ispybSEUtemperature, bufferName)
            if specimenId is None:
                specimenId = -1

            self.client.service.saveFrame( mode,
                                          self.selectedExperimentId,
                                          specimenId,
                                          sampleCode,
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

                #If status is inished we compress the folder
                if  status == "FINISHED" :
                    #Zipping file
                    zipFilePath = self.getPyarchDestination() + "/" + str( self.selectedExperimentId ) + ".zip"
                    temporalPath = "/tmp/" + str( self.selectedExperimentId ) + ".zip"
                    self.zipFolder( self.getPyarchDestination(), temporalPath )
                    self.movefile( temporalPath, self.getPyarchDestination() )
                    self.client.service.setDataAcquisitionFilePath( self.selectedExperimentId, zipFilePath )
        except Exception:
            traceback.print_exc()
            raise Exception

    # This method should be removed as zip files are created dynamically on server side
    def zipFolder( self, path, archivename ):
        print "ISPyB: zipping " + path + " on " + archivename
        myZipFile = zipfile.ZipFile( archivename, 'w' )
        rootlen = len( path ) + 1
        assert os.path.isdir( path )
        for base, dirs, files in os.walk( path ):
            for file in files:
                fn = os.path.join( base, file )
                myZipFile.write( fn, fn[rootlen:] )
        myZipFile.close()

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


    #def createExperiment( self, proposalCode, proposalNumber, samples, storageTemperature, mode, extraflowTime, experimentType, sourceFile, name ):
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

#            print ( "self.client.service.createExperiment( %s, %s, %s, %s, %s, %s, %s, %s, %s" % ( 
#                                                               self.proposalType,
#                                                               self.proposalNumber,
#                                                               str( samples ),
#                                                               storageTemperature,
#                                                               mode,
#                                                               extraflowTime,
#                                                               experimentType,
#                                                               expectedXMLFilePath,
#                                                               name
#                                                                                                 ) )
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
    #experiment = biosaxs.getExperimentById(345)
    biosaxs.selectedExperimentId = 345
    print biosaxs.getSpecimenIdBySampleCode( "bsa_25C" )

